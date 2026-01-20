import os
import subprocess
from dagster import op, job, schedule, ScheduleDefinition, DefaultScheduleStatus, RetryPolicy, Backoff

# Paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')
DBT_PROJECT_DIR = os.path.join(PROJECT_ROOT, 'medical_warehouse')

@op(retry_policy=RetryPolicy(max_retries=3, delay=60))
def scrape_telegram_data(context):
    """Runs the Telegram scraper script."""
    context.log.info("Starting Telegram scraping...")
    script_path = os.path.join(SCRIPTS_DIR, 'scraper.py')
    result = subprocess.run(['python', script_path], capture_output=True, text=True, check=True)
    context.log.info(result.stdout)
    if result.stderr:
        context.log.warning(result.stderr)
    return "Scraping completed"

@op
def load_raw_to_postgres(context, start_signal: str):
    """Loads raw JSON data into PostgreSQL."""
    context.log.info(f"Starting data loading. Signal: {start_signal}")
    script_path = os.path.join(SCRIPTS_DIR, 'loader.py')
    result = subprocess.run(['python', script_path], capture_output=True, text=True, check=True)
    context.log.info(result.stdout)
    if result.stderr:
        context.log.warning(result.stderr)
    return "Loading completed"

@op
def run_dbt_transformations(context, start_signal: str):
    """Executes dbt build for initial transformations."""
    context.log.info(f"Starting dbt build. Signal: {start_signal}")
    # Run dbt build in the medical_warehouse directory
    result = subprocess.run(['dbt', 'build'], cwd=DBT_PROJECT_DIR, capture_output=True, text=True, check=True)
    context.log.info(result.stdout)
    if result.stderr:
        context.log.warning(result.stderr)
    return "dbt transformations completed"

@op
def run_yolo_enrichment(context, start_signal: str):
    """Executes YOLO detection and rebuilds dbt marts."""
    context.log.info(f"Starting YOLO enrichment. Signal: {start_signal}")
    
    # 1. Run yolo_detect.py
    yolo_script = os.path.join(SCRIPTS_DIR, 'yolo_detect.py')
    yolo_result = subprocess.run(['python', yolo_script], capture_output=True, text=True, check=True)
    context.log.info("YOLO Detection Output:")
    context.log.info(yolo_result.stdout)
    
    # 2. Run dbt seed to load the new yolo_detections.csv
    seed_result = subprocess.run(['dbt', 'seed'], cwd=DBT_PROJECT_DIR, capture_output=True, text=True, check=True)
    context.log.info("dbt Seed Output:")
    context.log.info(seed_result.stdout)
    
    # 3. Trigger dbt build for marts to include enriched data
    # We use 'build' again to ensure everything is refreshed with the new seed data
    build_result = subprocess.run(['dbt', 'build'], cwd=DBT_PROJECT_DIR, capture_output=True, text=True, check=True)
    context.log.info("dbt Final Build Output:")
    context.log.info(build_result.stdout)
    
    return "YOLO enrichment and dbt mart rebuild completed"

@job
def medical_data_pipeline():
    """Defines the job dependency graph."""
    scrape_done = scrape_telegram_data()
    load_done = load_raw_to_postgres(scrape_done)
    transform_done = run_dbt_transformations(load_done)
    run_yolo_enrichment(transform_done)

# Configure daily schedule (runs every day at midnight)
daily_schedule = ScheduleDefinition(
    job=medical_data_pipeline,
    cron_schedule="0 0 * * *",
    default_status=DefaultScheduleStatus.STOPPED,
)

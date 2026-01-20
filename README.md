# Medical Data Warehouse (Telegram ELT)

A robust ELT (Extract, Load, Transform) data pipeline designed to scrape, store, and analyze Telegram data from Ethiopian medical business channels. This project utilizes **Python (Telethon)** for scraping, **PostgreSQL** for storage, and **dbt** for data modeling.

## 🚀 Features

- **Telegram Scraper**: Extracts messages and images from public Telegram channels.
- **Raw Data Lake**: Stores original API payloads as JSON and images locally.
- **Data Loader**: Validates and ingests raw JSON data into a valid PostgreSQL schema.
- **dbt Transformation**: Transforms raw data into a Star Schema (Facts & Dimensions) for analysis.
- **Dockerized Database**: Easy-to-setup PostgreSQL instance via Docker Compose.

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **Scraping**: Telethon
- **Database**: PostgreSQL 15 (Docker)
- **Transformation**: dbt (data build tool)
- **Containerization**: Docker & Docker Compose

## 📦 Project Structure

```
├── data/                       # Local Data Lake
│   ├── raw/
│   │   ├── images/             # Downloaded Telegram Images
│   │   └── telegram_messages/  # Raw JSON Payloads (Partitioned by Date)
├── medical_warehouse/          # dbt Project Directory
│   ├── models/                 # SQL Models (Staging, Marts)
│   ├── tests/                  # dbt Data Integrity Tests
│   └── dbt_project.yml         # dbt Configuration
├── scripts/                    # ETL Scripts
│   ├── scraper.py              # Telegram Scraper Script
│   └── loader.py               # Database Loader Script
├── api/                        # API Application (Task 4)
├── notebooks/                  # Analysis Notebooks (Task 3)
├── tests/                      # Python Unit Tests
├── logs/                       # Execution Logs
├── docker-compose.yml          # Postgres Service Definition
├── requirements.txt            # Python Dependencies
└── .env                        # Environment Variables (Not committed)
```

## 🏁 Getting Started

### 1. Prerequisites

- Python 3.10+ installed.
- Docker Desktop installed and running.
- A Telegram Account (for API credentials).

### 2. Installation

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/jossieT/telegram-medical-data-warehouse.git
    cd telegram-medical-data-warehouse
    ```

2.  **Create a Virtual Environment**:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Setup**:
    Create a `.env` file in the root directory:

    ```ini
    # Telegram API (get from my.telegram.org)
    TELEGRAM_API_ID=your_api_id
    TELEGRAM_API_HASH=your_api_hash
    TELEGRAM_PHONE=your_phone_number

    # Database Config (Docker)
    POSTGRES_DB=medical_warehouse
    POSTGRES_USER=medical_user
    POSTGRES_PASSWORD=medical_password
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5433

    # Database Config (Python Loader)
    DB_NAME=medical_warehouse
    DB_USER=medical_user
    DB_PASSWORD=medical_password
    DB_HOST=127.0.0.1
    DB_PORT=5433
    ```

### 3. Running the Pipeline

#### Step 1: Start the Database

```bash
docker-compose up -d
```

_Note: The database runs on port **5433** to avoid conflicts with local Postgres installations._

#### Step 2: Extract Data (Scrape)

run the scraper to fetch the last 200 messages from configured channels:

```bash
python scripts/scraper.py
```

_First run will require entering your Telegram login code._

#### Step 3: Load Data

Load the scraped JSON files into PostgreSQL:

```bash
python scripts/loader.py
```

```bash
cd medical_warehouse
dbt deps
dbt build
```

## ⚙️ Orchestration (Dagster)

The entire workflow (scraping, loading, transformation, and enrichment) is orchestrated using **Dagster**. This ensures observability, retries, and scheduled execution.

### Running the Pipeline with Dagster

1.  **Start the Dagster Development Server**:

    ```bash
    dagster dev -f pipeline.py
    ```

2.  **Access the UI**:
    Open [http://localhost:3000](http://localhost:3000) in your browser.

3.  **Execute the Job**:
    In the Dagster UI, find the `medical_data_pipeline` job and click **"Launch Pad"** -> **"Launch Run"**.

The pipeline follows this dependency graph:
`scrape_telegram_data` -> `load_raw_to_postgres` -> `run_dbt_transformations` -> `run_yolo_enrichment` (includes YOLO detection and final dbt mart rebuild).

## 📊 Data Models

The project implements a **Star Schema** with the following models:

- **`fct_messages`**: Central fact table containing all message events.
- **`dim_channels`**: Dimension table for channel metadata and statistics.
- **`dim_dates`**: Comprehensive date dimension for time-series analysis.

## 🧪 Testing

Run the dbt test suite to verify data integrity:

```bash
dbt test
```

Includes custom tests for:

- Duplicate checks
- Future date validation
- Non-negative view counts

## 🤝 Contributing

To ensure a smooth collaboration and maintain code quality, please follow the branching and PR strategy:

### Branching Strategy

- **`main`**: The production-ready branch. Only merges from `develop` or task-specific branches once verified.
- **`task/task-name`**: feature branches for specific tasks (e.g., `task/dagster-orchestration`).
- **`fix/bug-name`**: branches for hotfixes or bug resolutions.

### Pull Request (PR) Policy

1.  **Create a Branch**: Always work on a separate branch from `main`.
2.  **Linting & Tests**: Ensure that all tests pass locally and the linter (`flake8`) shows no errors.
3.  **CI Validation**: Every PR triggers a GitHub Action that runs:
    - Code linting (Python)
    - Unit tests
    - dbt model compilation
4.  **Review**: At least one project maintainer must approve the PR before merging.
5.  **Merge**: Once CI passes and approval is received, merge to `main` using "Squash and Merge" for a clean history.

## 📄 Documentation

Generate and view auto-generated documentation for the data warehouse:

```bash
dbt docs generate
dbt docs serve
```

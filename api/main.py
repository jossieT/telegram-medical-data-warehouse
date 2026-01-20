from fastapi import FastAPI
from .routers import reports, channels, search

app = FastAPI(
    title="Medical Data Warehouse API",
    description="Analytical API to expose insights from Telegram medical data.",
    version="1.0.0"
)

# Include Routers
app.include_router(reports.router)
app.include_router(channels.router)
app.include_router(search.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Medical Data Warehouse API",
        "docs": "/docs",
        "endpoints": [
            "/api/reports/top-products",
            "/api/reports/visual-content",
            "/api/channels/{channel_name}/activity",
            "/api/search/messages?query={query}"
        ]
    }

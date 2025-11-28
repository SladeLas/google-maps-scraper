"""Main entry point for the FastAPI app."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("slade_digital_scrapers.infrastructure.api.api:app", host="0.0.0.0", port=8000)

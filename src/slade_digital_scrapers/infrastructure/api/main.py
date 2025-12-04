"""Main entry point for the FastAPI app."""

import uvicorn
from slade_digital_scrapers.core.config import PORT

if __name__ == "__main__":
    uvicorn.run(
        "slade_digital_scrapers.infrastructure.api.api:app",
        host="0.0.0.0",
        port=PORT,
    )

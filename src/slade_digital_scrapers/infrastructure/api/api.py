"""Main scraping module API end points"""

import logging
import asyncio
import concurrent.futures
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from slade_digital_scrapers.core.config import (
    ALLOWED_ORIGINS,
    LOG_LEVEL,
)
from slade_digital_scrapers.infrastructure.models.entities.repository import (
    upsert_entities,
)
from slade_digital_scrapers.infrastructure.models.scraper_hisotry.repository import (
    upsert_scrape_history,
)
from slade_digital_scrapers.infrastructure.models.scraper_hisotry.schema import (
    ScrapeHistoryContract,
)

# Import the scraper function (adjust path if necessary)
try:
    from slade_digital_scrapers.gmaps_scraper.scraper import (
        scrape_google_maps,
    )
except ImportError:
    # Handle case where scraper might be in a different structure later
    logging.error("Could not import scrape_google_maps from scraper.py")
    # Define a dummy function to allow API to start, but fail on call
    def scrape_google_maps(*args, **kwargs):
        """Define a dummy function to allow API to start, but fail on call"""
        raise ImportError("Scraper function not available.")

# Configure basic logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="Slade Digital Scrapers",
    description="API to trigger Google Maps scraping based on a query.",
    version="0.1.0",
)

# Enable CORS so ToolJet/other clients can call the API from a browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool for running blocking database operations
executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=4
)

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "Google Maps Scraper API"}

@app.api_route(
    "/google_maps/scrape",
    methods=["GET", "POST"],
    response_model=List[Dict[str, Any]],
)
async def run_scrape(  # type: ignore[override]
    query: str = Query(
        ...,
        description="The search query for GMaps "
        "(e.g., 'restaurants in New York')",
    ),
    max_places: Optional[int] = Query(
        None,
        description="Max number of places to scrape. "
        "Scrapes all found if None.",
    ),
    lang: str = Query(
        "en",
        description="Language code for GMaps results (e.g., 'en', 'es')",
    ),
    headless: bool = Query(
        True,
        description="Run the browser in headless mode (no UI). "
        "Set to false for debugging locally.",
    ),
):
    """
    Triggers the Google Maps scraping process for the given query.
    """
    logging.info("=" * 60)
    logging.info("ENDPOINT CALLED: /google_maps/scrape")
    logging.info(
        "Received scrape request for query %r, max_places %s, lang %s, headless %s",
        query,
        max_places,
        lang,
        headless,
    )

    try:
        # Validate that scraper function is available
        if not callable(scrape_google_maps):
            logging.error("Scraper function is not callable")
            raise HTTPException(
                status_code=500,
                detail="Scraper function not available. Check server logs."
            )

        logging.info("Starting scraper function...")
        # Run the potentially long-running scraping task with timeout
        # Note: For production, consider running this in a background task
        # queue (e.g., Celery) to avoid blocking the API server for long
        # durations.
        results = await asyncio.wait_for(
            scrape_google_maps(
                query=query,
                max_places=max_places,
                lang=lang,
                headless=headless
            ),
            timeout=300  # 5 minutes timeout
        )

        logging.info(
            "Scraping finished for query %r. Found %d results.",
            query,
            len(results),
        )

        # Run blocking database operations in thread pool to avoid blocking
        # async event loop
        loop = asyncio.get_event_loop()

        # Adding the results in my db
        rows_added = await loop.run_in_executor(
            executor, upsert_entities, results
        )

        # Recording the scraper request
        # Generate a unique source identifier from the query
        source_id = (
            f"gmaps_{query.lower().replace(' ', '_').replace(',', '')[:50]}"
        )

        history_record = ScrapeHistoryContract(
            source=source_id,
            search_key=query,
            location_key=None,  # Could extract location from query if needed
            results_scraped=len(results)
        )

        await loop.run_in_executor(
            executor,
            upsert_scrape_history,
            [history_record.to_repository_dict()]
        )

        logging.info(
            "Saved %d entities and recorded scrape history for source %r",
            rows_added,
            source_id,
        )

        return results
    except asyncio.TimeoutError as exc:
        logging.error(
            "Scraping timeout for query %r after %d seconds", query, 300
        )
        raise HTTPException(
            status_code=504,
            detail="Scraping request timed out after 5 minutes"
        ) from exc
    except ImportError as e:
        logging.error(
            "ImportError during scraping for query %r: %s", query, e
        )
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: Scraper not available."
        ) from e
    except Exception as exc:
        logging.error(
            "An error occurred during scraping for query %r: %s",
            query, exc, exc_info=True)
        # Consider more specific error handling based on scraper exceptions
        raise HTTPException(
            status_code=500,
            detail=(
                f"An internal error occurred during scraping: {str(exc)}"
            )
        ) from exc

# Example for running locally (uvicorn main_api:app --reload)
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8001)

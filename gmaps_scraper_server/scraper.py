"""Async Playwright workflow for gathering Google Maps place data."""

import asyncio
from urllib.parse import urlencode
from playwright.async_api import async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# Import the extraction functions from our helper module
from . import extractor

# --- Constants ---
BASE_URL = "https://www.google.com/maps/search/"
DEFAULT_TIMEOUT = 30000  # 30 seconds for navigation and selectors
SCROLL_PAUSE_TIME = 1.5  # Pause between scrolls
MAX_SCROLL_ATTEMPTS_WITHOUT_NEW_LINKS = 5  # Stop after this many no-link scrolls

# --- Helper Functions ---
def create_search_url(query, lang="en"):
    """Creates a Google Maps search URL."""
    params = {'q': query, 'hl': lang}
    # Note: geo_coordinates and zoom might require different URL structure (/maps/@lat,lng,zoom)
    # For simplicity, starting with basic query search
    return BASE_URL + "?" + urlencode(params)

# --- Main Scraping Logic ---
async def scrape_google_maps(query, max_places=None, lang="en", headless=True):
    """
    Scrapes Google Maps for places based on a query.

    Args:
        query (str): The search query (e.g., "restaurants in New York").
        max_places (int, optional): Max num of places to scrape. Defaults to None.
        lang (str, optional): Language code for Google Maps (e.g., 'en', 'es'). Defaults to "en".
        headless (bool, optional): Whether to run the browser in headless mode. Defaults to True.

    Returns:
        list: A list of dictionaries, each containing details for a scraped place.
              Returns an empty list if no places are found or an error occurs.
    """
    results = []
    place_links = set()
    scroll_attempts_no_new = 0
    browser = None

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                ),
                java_script_enabled=True,
                accept_downloads=False,
                locale=lang,
            )
            page = await context.new_page()
            if not page:
                await browser.close()
                raise Exception(  # noqa: TRY002  # pylint: disable=broad-exception-raised
                    "Failed to create a new browser page "
                    "(context.new_page() returned None)."
                )
            # Removed problematic: await page.set_default_timeout(DEFAULT_TIMEOUT)
            # Removed associated debug prints

            search_url = create_search_url(query, lang)
            print(f"Navigating to search URL: {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            # --- Handle potential consent forms ---
            # This is a common pattern, might need adjustment based on specific consent popups
            try:
                consent_button_xpath = (
                    "//button[.//span[contains(text(), 'Accept all') "
                    "or contains(text(), 'Reject all')]]"
                )
                # Wait briefly for the button to potentially appear
                await page.wait_for_selector(
                    consent_button_xpath,
                    state="visible",
                    timeout=5000,
                )
                # Click the "Accept all" or equivalent button if found
                # Example: Prioritize "Accept all"
                accept_button = await page.query_selector(
                    "//button[.//span[contains(text(), 'Accept all')]]"
                )
                if accept_button:
                    print("Accepting consent form...")
                    await accept_button.click() # Added await
                else:
                    # Fallback to clicking the first consent button found (might be reject)
                    print("Clicking first available consent button...")
                    await page.locator(consent_button_xpath).first.click()
                # Wait for navigation/popup closure
                await page.wait_for_load_state("networkidle", timeout=5000)
            except PlaywrightTimeoutError:
                print("No consent form detected or timed out waiting.")
            except Exception as e:  # noqa: BLE001  # pylint: disable=broad-except
                print(f"Error handling consent form: {e}")


            # --- Scrolling and Link Extraction ---
            print("Scrolling to load places...")
            feed_selector = '[role="feed"]'
            try:
                await page.wait_for_selector(
                    feed_selector,
                    state="visible",
                    timeout=25000,
                )
            except PlaywrightTimeoutError:
                 # Check if it's a single result page (maps/place/)
                if "/maps/place/" in page.url:
                    print("Detected single place page.")
                    place_links.add(page.url)
                else:
                    print(
                        f"Error: Feed element '{feed_selector}' not found. "
                        "Maybe no results or page structure changed."
                    )
                    await browser.close()
                    return []

            if await page.locator(feed_selector).count() > 0:
                last_height = await page.evaluate(
                    f"document.querySelector('{feed_selector}').scrollHeight"
                )
                while True:
                    # Scroll down
                    await page.evaluate(
                        f"document.querySelector('{feed_selector}').scrollTop = "
                        f"document.querySelector('{feed_selector}').scrollHeight"
                    )
                    await asyncio.sleep(SCROLL_PAUSE_TIME)

                    # Extract links after scroll
                    current_links_list = await page.locator(
                        f'{feed_selector} a[href*="/maps/place/"]'
                    ).evaluate_all("elements => elements.map(a => a.href)")
                    current_links = set(current_links_list)
                    new_links_found = len(current_links - place_links) > 0
                    place_links.update(current_links)
                    print(f"Found {len(place_links)} unique place links so far...")

                    if max_places is not None and len(place_links) >= max_places:
                        print(f"Reached max_places limit ({max_places}).")
                        place_links = set(list(place_links)[:max_places]) # Trim excess links
                        break

                    # Check if scroll height has changed
                    new_height = await page.evaluate(
                        f"document.querySelector('{feed_selector}').scrollHeight"
                    )
                    if new_height == last_height:
                        # Check for the "end of results" marker
                        end_marker_xpath = (
                            "//span[contains(text(), \"You've reached the end of the list.\")]"
                        )
                        if await page.locator(end_marker_xpath).count() > 0:
                            print("Reached the end of the results list.")
                            break
                        else:
                            # If height didn't change and marker missing, maybe loading issue?
                            # Increment no-new-links counter
                            if not new_links_found:
                                scroll_attempts_no_new += 1
                                print(
                                    "Scroll height unchanged and no new links. "
                                    f"Attempt {scroll_attempts_no_new}/"
                                    f"{MAX_SCROLL_ATTEMPTS_WITHOUT_NEW_LINKS}"
                                )
                                if (
                                    scroll_attempts_no_new
                                    >= MAX_SCROLL_ATTEMPTS_WITHOUT_NEW_LINKS
                                ):
                                    print("Stopping scroll due to lack of new links.")
                                    break
                            else:
                                scroll_attempts_no_new = 0  # Reset when new links found
                    else:
                        last_height = new_height
                        scroll_attempts_no_new = 0 # Reset if scroll height changed

                    # Optional: Add a hard limit on scrolls to prevent infinite loops
                    # if scroll_count > MAX_SCROLLS: break

            # --- Scraping Individual Places ---
            print(f"\nScraping details for {len(place_links)} places...")
            count = 0
            for link in place_links:
                count += 1
                print(f"Processing link {count}/{len(place_links)}: {link}") # Keep sync print
                try:
                    await page.goto(link, wait_until='domcontentloaded') # Added await
                    # Wait a bit for dynamic content if needed, or wait for a specific element
                    # await page.wait_for_load_state('networkidle', timeout=10000)

                    html_content = await page.content() # Added await
                    place_data = extractor.extract_place_data(html_content)

                    if place_data:
                        place_data['link'] = link # Add the source link
                        results.append(place_data)
                        # print(json.dumps(place_data, indent=2))
                    else:
                        print(f"  - Failed to extract data for: {link}")
                        # Optionally save the HTML for debugging
                        # with open(f"error_page_{count}.html", "w", encoding="utf-8") as f:
                        #     f.write(html_content)

                except PlaywrightTimeoutError:
                    print(f"  - Timeout navigating to or processing: {link}")
                except Exception as e:  # noqa: BLE001  # pylint: disable=broad-except
                    print(f"  - Error processing {link}: {e}")
                await asyncio.sleep(0.5) # Changed to asyncio.sleep, added await

            await browser.close() # Added await

        except PlaywrightTimeoutError:
            print("Timeout error during scraping process.")
        except Exception as e:  # noqa: BLE001  # pylint: disable=broad-except
            print(f"An error occurred during scraping: {e}")
            import traceback
            traceback.print_exc() # Print detailed traceback for debugging
        finally:
            # Ensure browser is closed if an error occurred mid-process
            if browser and browser.is_connected(): # Check if browser exists and is connected
                await browser.close() # Added await

    print(f"\nScraping finished. Found details for {len(results)} places.")
    return results

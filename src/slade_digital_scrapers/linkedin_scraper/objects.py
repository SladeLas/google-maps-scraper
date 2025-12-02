"""Reusable Selenium data objects and helpers for LinkedIn scraping."""

from dataclasses import dataclass
from time import sleep

from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from . import constants as c


@dataclass
class Contact:
    """Lightweight representation of a LinkedIn contact."""

    name: str = None
    occupation: str = None
    url: str = None


@dataclass
class Institution:
    """Common fields shared by institutions/companies/schools."""

    institution_name: str = None
    linkedin_url: str = None
    website: str = None
    industry: str = None
    type: str = None
    headquarters: str = None
    company_size: int = None
    founded: int = None


@dataclass
class Experience(Institution):
    """Represents a single work experience entry."""

    from_date: str = None
    to_date: str = None
    description: str = None
    position_title: str = None
    duration: str = None
    location: str = None


@dataclass
class Education(Institution):
    """Represents an education entry on LinkedIn."""

    from_date: str = None
    to_date: str = None
    description: str = None
    degree: str = None


@dataclass
class Interest(Institution):
    """Represents an interest or followed organization."""

    title = None


@dataclass
class Accomplishment(Institution):
    """Represents a misc accomplishment (certifications, honors, etc.)."""

    category = None
    title = None


@dataclass
class Scraper:
    """Base Selenium-enabled scraper with utility helpers."""

    driver: Chrome = None
    WAIT_FOR_ELEMENT_TIMEOUT = 5
    TOP_CARD = "pv-top-card"

    @staticmethod
    def wait(duration):
        """Sleep for `duration` seconds (integer)."""

        sleep(int(duration))

    def focus(self):
        """Raise a JavaScript alert to steal focus back from LinkedIn."""

        self.driver.execute_script('alert("Focus window")')
        self.driver.switch_to.alert.accept()

    def mouse_click(self, elem):
        """Move the mouse to an element to trigger hover interactions."""

        action = webdriver.ActionChains(self.driver)
        action.move_to_element(elem).perform()

    def wait_for_element_to_load(self, by=By.CLASS_NAME, name="pv-top-card", base=None):
        """Wait for a single element to become present and return it."""

        base = base or self.driver
        return WebDriverWait(base, self.WAIT_FOR_ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located((by, name))
        )

    def wait_for_all_elements_to_load(self, by=By.CLASS_NAME, name="pv-top-card", base=None):
        """Wait for all matching elements to be present and return them."""

        base = base or self.driver
        return WebDriverWait(base, self.WAIT_FOR_ELEMENT_TIMEOUT).until(
            EC.presence_of_all_elements_located((by, name))
        )

    def is_signed_in(self):
        """Best-effort check that a LinkedIn nav element is visible."""

        try:
            WebDriverWait(self.driver, self.WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, c.VERIFY_LOGIN_ID))
            )
            self.driver.find_element(By.CLASS_NAME, c.VERIFY_LOGIN_ID)
            return True
        except Exception:
            pass
        return False

    def scroll_to_half(self):
        """Scroll the page to roughly the halfway point."""

        self.driver.execute_script(
            "window.scrollTo(0, Math.ceil(document.body.scrollHeight/2));"
        )

    def scroll_to_bottom(self):
        """Scroll to the bottom of the current page."""

        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def scroll_class_name_element_to_page_percent(self, class_name: str, page_percent: float):
        """Scroll a matching element to a given percentage of its height."""

        self.driver.execute_script(
            f'elem = document.getElementsByClassName("{class_name}")[0]; '
            f"elem.scrollTo(0, elem.scrollHeight*{str(page_percent)});"
        )

    def __find_element_by_class_name__(self, class_name):
        """Return True if an element with the class name exists."""

        try:
            self.driver.find_element(By.CLASS_NAME, class_name)
            return True
        except Exception:
            pass
        return False

    def __find_element_by_xpath__(self, tag_name):
        """Return True if an element matching the xpath exists."""

        try:
            self.driver.find_element(By.XPATH, tag_name)
            return True
        except Exception:
            pass
        return False

    def __find_enabled_element_by_xpath__(self, tag_name):
        """Return True if the first matched xpath element is enabled."""

        try:
            elem = self.driver.find_element(By.XPATH, tag_name)
            return elem.is_enabled()
        except Exception:
            pass
        return False

    @classmethod
    def __find_first_available_element__(cls, *args):
        """Return the first truthy element from the iterable arguments."""

        for elem in args:
            if elem:
                return elem[0]

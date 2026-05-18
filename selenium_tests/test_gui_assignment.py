import os
import re
import unittest

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


COURSE_SEARCH_URL = "https://primus.nss.udel.edu/CoursesSearch/"


def env_truthy(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def normalized_text(text):
    return re.sub(r"\s+", " ", text).strip()


def compact_text(text):
    return re.sub(r"\s+", "", text).lower()


def build_driver():
    browser = os.getenv("BROWSER", "chrome").strip().lower()
    headless = env_truthy("HEADLESS", default=False)

    if browser == "firefox":
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)
    else:
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1366,900")

        chrome_binary = os.getenv("CHROME_BINARY")
        if chrome_binary:
            options.binary_location = chrome_binary

        user_data_dir = os.getenv("CHROME_USER_DATA_DIR")
        if user_data_dir:
            options.add_argument("--user-data-dir=" + user_data_dir)

        profile_dir = os.getenv("CHROME_PROFILE_DIR")
        if profile_dir:
            options.add_argument("--profile-directory=" + profile_dir)

        driver = webdriver.Chrome(options=options)

    driver.set_window_size(1366, 900)
    return driver


class GuiInputReproductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = build_driver()
        cls.wait = WebDriverWait(cls.driver, 20)

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "driver", None):
            cls.driver.quit()

    def body_text(self):
        return normalized_text(self.driver.find_element(By.TAG_NAME, "body").text)

    def wait_for_body_text(self, expected, timeout=20):
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(
            lambda driver: expected.lower()
            in normalized_text(driver.find_element(By.TAG_NAME, "body").text).lower()
        )

    def test_udel_cisc615_spring_2026_instructor_is_clause_james(self):
        """Part 1: starts at UD Course Search and verifies CISC615 instructor.

        UD currently hides Location and Instructor fields from public sessions.
        To run this test all the way through, start Selenium with a browser
        profile that is already logged in to UD Course Search, for example:

        CHROME_USER_DATA_DIR=/path/to/chrome-profile python -m unittest ...
        """
        driver = self.driver
        driver.get(COURSE_SEARCH_URL)

        self.wait.until(EC.presence_of_element_located((By.ID, "term")))
        Select(driver.find_element(By.ID, "term")).select_by_value("2263")
        course_id = driver.find_element(By.ID, "course_number")
        course_id.clear()
        course_id.send_keys("CISC615")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "CISC615010")))
        results_text = self.body_text()
        self.assertIn("2026 Spring Semester (2263)", results_text)
        self.assertIn("CISC615010", results_text)
        self.assertIn("Software Testing and Maintenance", results_text)

        driver.find_element(By.LINK_TEXT, "CISC615010").click()
        self.wait_for_body_text("CISC615010 Software Testing and Maintenance")
        detail_text = self.body_text()

        if (
            "Login to view Location and Instructor information" in detail_text
            and "Clause" not in detail_text
        ):
            self.fail(
                "UD Course Search is hiding instructor data because this browser "
                "session is not logged in. Log in to UD first or run Selenium with "
                "an authenticated Chrome profile, then rerun this test."
            )

        self.assertIn(
            "clause,james",
            compact_text(detail_text),
            "Expected the CISC615 Spring 2026 instructor to be exactly Clause,James.",
        )

    def test_wikipedia_search_finds_selenium_software_article(self):
        driver = self.driver
        driver.get("https://www.wikipedia.org/")

        search = self.wait.until(EC.element_to_be_clickable((By.ID, "searchInput")))
        search.clear()
        search.send_keys("Selenium (software)")
        search.send_keys(Keys.ENTER)

        heading = self.wait.until(EC.visibility_of_element_located((By.ID, "firstHeading")))
        self.assertEqual("Selenium (software)", normalized_text(heading.text))
        self.assertIn("Selenium", self.body_text())

    def test_the_internet_login_success_logout_and_failure(self):
        driver = self.driver
        driver.get("https://the-internet.herokuapp.com/login")

        driver.find_element(By.ID, "username").send_keys("tomsmith")
        driver.find_element(By.ID, "password").send_keys("SuperSecretPassword!")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        self.wait_for_body_text("You logged into a secure area!")
        self.assertIn("Secure Area", self.body_text())

        driver.find_element(By.CSS_SELECTOR, "a.button.secondary").click()
        self.wait_for_body_text("You logged out of the secure area!")

        driver.find_element(By.ID, "username").send_keys("tomsmith")
        driver.find_element(By.ID, "password").send_keys("wrong-password")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        self.wait_for_body_text("Your password is invalid!")

    def test_saucedemo_add_remove_and_checkout_cart_items(self):
        driver = self.driver
        driver.get("https://www.saucedemo.com/")

        self.wait.until(EC.element_to_be_clickable((By.ID, "user-name"))).send_keys(
            "standard_user"
        )
        driver.find_element(By.ID, "password").send_keys("secret_sauce")
        driver.find_element(By.ID, "login-button").click()

        self.wait.until(EC.visibility_of_element_located((By.ID, "inventory_container")))
        driver.find_element(By.ID, "add-to-cart-sauce-labs-backpack").click()
        driver.find_element(By.ID, "add-to-cart-sauce-labs-bike-light").click()

        badge = self.wait.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "shopping_cart_badge"))
        )
        self.assertEqual("2", badge.text)

        driver.find_element(By.CLASS_NAME, "shopping_cart_link").click()
        self.wait_for_body_text("Your Cart")
        cart_text = self.body_text()
        self.assertIn("Sauce Labs Backpack", cart_text)
        self.assertIn("Sauce Labs Bike Light", cart_text)

        driver.find_element(By.ID, "remove-sauce-labs-bike-light").click()
        self.assertIn("Sauce Labs Backpack", self.body_text())
        WebDriverWait(driver, 10).until(
            lambda current_driver: "Sauce Labs Bike Light"
            not in normalized_text(current_driver.find_element(By.TAG_NAME, "body").text)
        )
        self.assertNotIn("Sauce Labs Bike Light", self.body_text())
        self.assertEqual(
            "1",
            driver.find_element(By.CLASS_NAME, "shopping_cart_badge").text,
        )

        driver.find_element(By.ID, "checkout").click()
        self.wait.until(EC.visibility_of_element_located((By.ID, "first-name"))).send_keys(
            "Gui"
        )
        driver.find_element(By.ID, "last-name").send_keys("Tester")
        driver.find_element(By.ID, "postal-code").send_keys("19716")
        driver.find_element(By.ID, "continue").click()

        self.wait_for_body_text("Checkout: Overview")
        self.assertIn("Sauce Labs Backpack", self.body_text())
        driver.find_element(By.ID, "finish").click()
        self.wait_for_body_text("Thank you for your order!")

    def test_todomvc_create_filter_and_clear_completed_items(self):
        driver = self.driver
        driver.get("https://demo.playwright.dev/todomvc/")

        driver.execute_script("window.localStorage.clear();")
        driver.refresh()

        todo_input = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".new-todo"))
        )
        for item in ["Write Selenium test", "Compare GUI tools", "Write report"]:
            todo_input.send_keys(item)
            todo_input.send_keys(Keys.ENTER)

        rows = [
            row for row in driver.find_elements(By.CSS_SELECTOR, ".todo-list li")
            if row.is_displayed()
        ]
        self.assertEqual(3, len(rows))

        rows[0].find_element(By.CSS_SELECTOR, ".toggle").click()
        rows[1].find_element(By.CSS_SELECTOR, ".toggle").click()

        driver.find_element(By.CSS_SELECTOR, "a[href='#/completed']").click()
        completed = [
            row for row in driver.find_elements(By.CSS_SELECTOR, ".todo-list li")
            if row.is_displayed()
        ]
        self.assertEqual(2, len(completed))
        self.assertIn("Write Selenium test", completed[0].text)
        self.assertIn("Compare GUI tools", completed[1].text)

        driver.find_element(By.CLASS_NAME, "clear-completed").click()
        driver.find_element(By.CSS_SELECTOR, "a[href='#/']").click()
        remaining = [
            row for row in driver.find_elements(By.CSS_SELECTOR, ".todo-list li")
            if row.is_displayed()
        ]
        self.assertEqual(1, len(remaining))
        self.assertIn("Write report", remaining[0].text)


if __name__ == "__main__":
    try:
        unittest.main(verbosity=2)
    except TimeoutException as exc:
        raise AssertionError("Timed out while waiting for a page interaction.") from exc

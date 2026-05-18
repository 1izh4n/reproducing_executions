# GUI Input Reproduction - OculiX/SikuliX style tests.
#
# Run from OculiX/SikuliX with this folder as the script bundle:
#   gui_assignment.sikuli
#
# The tests intentionally use visual/OCR actions instead of DOM selectors.
# Keep the browser visible, set zoom to 100%, and keep the window around
# 1366x900 or larger for the most reliable OCR.

from sikuli import *  # noqa
from java.lang import System
import re
import time


COURSE_SEARCH_URL = "https://primus.nss.udel.edu/CoursesSearch/"

Settings.MoveMouseDelay = 0.1
Settings.WaitScanRate = 2

TESTS = []


def test(fn):
    TESTS.append((fn.__name__, fn))
    return fn


def os_modifier_key():
    os_name = System.getProperty("os.name").lower()
    if "mac" in os_name:
        return Key.CMD
    return Key.CTRL


def shortcut(letter):
    keyDown(os_modifier_key())
    type(letter)
    keyUp(os_modifier_key())
    wait(0.2)


def go(url):
    shortcut("l")
    paste(url)
    type(Key.ENTER)
    wait(3)


def norm(text):
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def compact(text):
    return re.sub(r"\s+", "", str(text)).lower()


def read_screen_text():
    try:
        return SCREEN.text()
    except:
        return ""


def collect_lines():
    try:
        return list(SCREEN.collectLines())
    except:
        return []


def wait_for_text(expected, timeout=20):
    target = norm(expected)
    end = time.time() + timeout
    last_text = ""
    while time.time() < end:
        last_text = read_screen_text()
        if target in norm(last_text):
            return last_text
        wait(0.5)
    raise AssertionError("Text not visible: " + expected + "\nLast OCR text:\n" + last_text)


def assert_text_absent(unexpected, timeout=3):
    target = norm(unexpected)
    end = time.time() + timeout
    while time.time() < end:
        if target in norm(read_screen_text()):
            raise AssertionError("Unexpected text is still visible: " + unexpected)
        wait(0.5)


def find_line(text, timeout=15):
    target = norm(text)
    end = time.time() + timeout
    last_lines = []
    while time.time() < end:
        last_lines = collect_lines()
        exact_match = None
        partial_match = None
        for line in last_lines:
            line_text = norm(line.getText())
            if line_text == target:
                exact_match = line
                break
            if target in line_text and partial_match is None:
                partial_match = line
        if exact_match is not None:
            return exact_match
        if partial_match is not None:
            return partial_match
        wait(0.5)

    seen = []
    for line in last_lines:
        try:
            seen.append(line.getText())
        except:
            pass
    raise AssertionError("OCR line not found: " + text + "\nVisible lines:\n" + "\n".join(seen))


def click_line(text, timeout=15):
    match = find_line(text, timeout)
    click(match)
    wait(0.5)
    return match


def click_right_of_line(text, pixels=180, timeout=15):
    match = find_line(text, timeout)
    x = match.getX() + match.getW() + pixels
    y = match.getY() + int(match.getH() / 2)
    click(Location(x, y))
    wait(0.4)
    return match


def enter_text(text):
    paste(text)
    wait(0.2)


@test
def test_udel_cisc615_spring_2026_instructor_is_clause_james():
    go(COURSE_SEARCH_URL)
    wait_for_text("Courses Search")

    # The form starts with Fall selected. Use the visible Term control to choose Spring.
    click_right_of_line("Term:", 180)
    type(Key.HOME)
    type(Key.DOWN)
    type(Key.ENTER)
    wait(0.5)

    click_right_of_line("Course ID:", 180)
    enter_text("CISC615")
    type(Key.ENTER)

    wait_for_text("CISC615010", 25)
    click_line("CISC615010")
    detail_text = wait_for_text("Software Testing and Maintenance", 25)

    full_text = detail_text + "\n" + read_screen_text()
    if "login to view location and instructor information" in norm(full_text) and "clause" not in norm(full_text):
        raise AssertionError(
            "UD Course Search is hiding instructor data. Log in to UD in this browser, "
            "then rerun the OculiX script."
        )

    if "clause,james" not in compact(full_text):
        raise AssertionError("Expected instructor text Clause,James for CISC615 Spring 2026.")


@test
def test_wikipedia_search_finds_selenium_software_article():
    go("https://www.wikipedia.org/")
    wait_for_text("Wikipedia")
    click_line("Search Wikipedia")
    enter_text("Selenium (software)")
    type(Key.ENTER)
    page_text = wait_for_text("Selenium", 25)
    if "selenium (software)" not in norm(page_text + "\n" + read_screen_text()):
        raise AssertionError("Expected the Selenium (software) article after searching Wikipedia.")


@test
def test_the_internet_login_success_logout_and_failure():
    go("https://the-internet.herokuapp.com/login")
    wait_for_text("Login Page")

    click_right_of_line("Username", 160)
    enter_text("tomsmith")
    type(Key.TAB)
    enter_text("SuperSecretPassword!")
    type(Key.ENTER)
    wait_for_text("You logged into a secure area", 20)

    click_line("Logout")
    wait_for_text("You logged out of the secure area", 20)

    click_right_of_line("Username", 160)
    enter_text("tomsmith")
    type(Key.TAB)
    enter_text("wrong-password")
    type(Key.ENTER)
    wait_for_text("Your password is invalid", 20)


@test
def test_saucedemo_add_remove_and_checkout_cart_items():
    go("https://www.saucedemo.com/")
    wait_for_text("Swag Labs")

    click_line("Username")
    enter_text("standard_user")
    type(Key.TAB)
    enter_text("secret_sauce")
    type(Key.ENTER)

    wait_for_text("Products", 20)
    click_line("Add to cart")
    click_line("Add to cart")

    go("https://www.saucedemo.com/cart.html")
    wait_for_text("Your Cart", 20)
    wait_for_text("Sauce Labs Backpack")
    wait_for_text("Sauce Labs Bike Light")

    click_line("Remove")
    assert_text_absent("Sauce Labs Backpack", 5)
    wait_for_text("Sauce Labs Bike Light")

    click_line("Checkout")
    wait_for_text("Checkout: Your Information", 20)
    click_line("First Name")
    enter_text("Gui")
    type(Key.TAB)
    enter_text("Tester")
    type(Key.TAB)
    enter_text("19716")
    type(Key.ENTER)

    wait_for_text("Checkout: Overview", 20)
    wait_for_text("Sauce Labs Bike Light")
    click_line("Finish")
    wait_for_text("Thank you for your order", 20)


@test
def test_todomvc_create_filter_and_clear_completed_items():
    go("https://demo.playwright.dev/todomvc/")
    wait_for_text("todos", 20)

    click_line("What needs to be done")
    for item in ["Write OculiX test", "Compare GUI tools", "Write report"]:
        enter_text(item)
        type(Key.ENTER)

    wait_for_text("Write OculiX test")
    wait_for_text("Compare GUI tools")
    wait_for_text("Write report")

    first = find_line("Write OculiX test")
    click(Location(first.getX() - 30, first.getY() + int(first.getH() / 2)))
    second = find_line("Compare GUI tools")
    click(Location(second.getX() - 30, second.getY() + int(second.getH() / 2)))

    click_line("Completed")
    wait_for_text("Write OculiX test")
    wait_for_text("Compare GUI tools")

    click_line("Clear completed")
    click_line("All")
    wait_for_text("Write report")
    assert_text_absent("Write OculiX test", 5)
    assert_text_absent("Compare GUI tools", 5)


def run_all_tests():
    failures = []
    for name, fn in TESTS:
        print("[RUN] " + name)
        try:
            fn()
            print("[PASS] " + name)
        except Exception as exc:
            print("[FAIL] " + name + ": " + str(exc))
            failures.append(name + ": " + str(exc))

    if failures:
        raise AssertionError("OculiX test failures:\n" + "\n".join(failures))


run_all_tests()

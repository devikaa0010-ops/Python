from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

URL = "https://demoqa.com/text-box"


def get_user_input():
    """Read the details from the keyboard."""
    print("Enter the details to be filled in the form")
    return {
        "name": input("Full Name         : ").strip(),
        "email": input("Email             : ").strip(),
        "current": input("Current Address   : ").strip(),
        "permanent": input("Permanent Address : ").strip(),
    }


def fill_form(driver, wait, data):
    """Locate each field by its id and type the data."""
    fields = {
        "userName": data["name"],
        "userEmail": data["email"],
        "currentAddress": data["current"],
        "permanentAddress": data["permanent"],
    }
    for field_id, value in fields.items():
        element = wait.until(EC.visibility_of_element_located((By.ID, field_id)))
        element.clear()
        element.send_keys(value)

    submit = driver.find_element(By.ID, "submit")
    # Ads on DemoQA can cover the button, so scroll to it and click with JavaScript
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit)
    driver.execute_script("arguments[0].click();", submit)


def verify_output(wait, data):
    """Read the output box and compare it with the entered data."""
    wait.until(EC.visibility_of_element_located((By.ID, "output")))

    # Each output line looks like "Name:John" -> keep the part after the first ':'
    def value_of(element_id):
        text = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, f"#output #{element_id}"))).text
        return text.split(":", 1)[1].strip()

    checks = [
        ("Full Name", "name", data["name"]),
        ("Email", "email", data["email"]),
        ("Current Address", "currentAddress", data["current"]),
        ("Permanent Address", "permanentAddress", data["permanent"]),
    ]

    print("\n===== VERIFICATION =====")
    all_ok = True
    for label, element_id, expected in checks:
        actual = value_of(element_id)
        ok = actual == expected
        all_ok = all_ok and ok
        print(f"{label:<18}: expected '{expected}' | displayed '{actual}' "
              f"-> {'PASS' if ok else 'FAIL'}")

    print("\nResult:", "All details displayed correctly." if all_ok
          else "Some details do not match.")
    return all_ok


def main():
    data = get_user_input()
    driver = None
    try:
        driver = webdriver.Chrome()           # launch the browser
        driver.maximize_window()
        wait = WebDriverWait(driver, 15)      # explicit wait, up to 15 s
        driver.get(URL)                       # navigate to the page
        print(f"\nOpened: {driver.title}")

        fill_form(driver, wait, data)
        verify_output(wait, data)
    except TimeoutException:
        print("Error: page element did not appear in time.")
    except WebDriverException as e:
        print("Browser/WebDriver error:", e.msg)
    finally:
        if driver:
            driver.quit()                     # close the browser
            print("Browser closed.")


if __name__ == "__main__":
    main()
"""Base class for page objects."""

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class BasePage:
    TIMEOUT = 10
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, self.TIMEOUT)
    
    def go_to(self, url):
        self.driver.get(url)
    
    def find(self, by, locator):
        return self.wait.until(EC.presence_of_element_located((by, locator)))
    
    def find_all(self, by, locator):
        try:
            self.wait.until(EC.presence_of_element_located((by, locator)))
            return self.driver.find_elements(by, locator)
        except TimeoutException:
            return []
    
    def find_by_testid(self, testid):
        return self.find(By.CSS_SELECTOR, f'[data-testid="{testid}"]')
    
    def click(self, by, locator):
        elem = self.wait.until(EC.element_to_be_clickable((by, locator)))
        elem.click()
    
    def type_into(self, by, locator, text, clear=True):
        elem = self.find(by, locator)
        if clear:
            elem.clear()
        elem.send_keys(text)
    
    def is_visible(self, by, locator, timeout=5):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, locator))
            )
            return True
        except TimeoutException:
            return False
    
    def get_text(self, by, locator):
        return self.find(by, locator).text
    
    def wait_for_page_load(self):
        WebDriverWait(self.driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

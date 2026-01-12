"""Page object for the main inventory page."""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from .base_page import BasePage


class HomePage(BasePage):
    # Locators
    PAGE_TITLE = '[data-testid="page-title"]'
    
    # Add form
    INPUT_NAME = '[data-testid="input-item-name"]'
    INPUT_QTY = '[data-testid="input-item-quantity"]'
    SELECT_LOC = '[data-testid="select-item-location"]'
    BTN_ADD = '[data-testid="btn-add-item"]'
    
    # Move form
    INPUT_MOVE_NAME = '[data-testid="input-move-item-name"]'
    INPUT_MOVE_QTY = '[data-testid="input-move-quantity"]'
    SELECT_FROM = '[data-testid="select-from-location"]'
    SELECT_TO = '[data-testid="select-to-location"]'
    BTN_MOVE = '[data-testid="btn-move-item"]'
    
    # Table
    INVENTORY_TABLE = '[data-testid="inventory-table-body"]'
    INVENTORY_ROW = '[data-testid^="inventory-row-"]'
    
    def __init__(self, driver, base_url="http://localhost:8000"):
        super().__init__(driver)
        self.base_url = base_url
    
    def open(self):
        self.go_to(self.base_url)
        self.wait_for_page_load()
        return self
    
    def is_loaded(self):
        return self.is_visible(By.CSS_SELECTOR, self.PAGE_TITLE)
    
    def add_item(self, name, quantity, location):
        """Fill out add form and submit."""
        self.type_into(By.CSS_SELECTOR, self.INPUT_NAME, name)
        self.type_into(By.CSS_SELECTOR, self.INPUT_QTY, str(quantity))
        
        select = Select(self.find(By.CSS_SELECTOR, self.SELECT_LOC))
        select.select_by_value(location)
        
        self.click(By.CSS_SELECTOR, self.BTN_ADD)
        self.wait_for_page_load()
        time.sleep(0.3)  # let DOM update
        return self
    
    def move_item(self, name, quantity, from_loc, to_loc):
        """Fill out move form and submit."""
        self.type_into(By.CSS_SELECTOR, self.INPUT_MOVE_NAME, name)
        self.type_into(By.CSS_SELECTOR, self.INPUT_MOVE_QTY, str(quantity))
        
        Select(self.find(By.CSS_SELECTOR, self.SELECT_FROM)).select_by_value(from_loc)
        Select(self.find(By.CSS_SELECTOR, self.SELECT_TO)).select_by_value(to_loc)
        
        self.click(By.CSS_SELECTOR, self.BTN_MOVE)
        self.wait_for_page_load()
        time.sleep(0.3)
        return self
    
    def is_item_in_table(self, name):
        """Check if item name appears in the inventory table."""
        try:
            table = self.find(By.CSS_SELECTOR, self.INVENTORY_TABLE)
            return name in table.text
        except:
            return False
    
    def get_item_quantity(self, name, location=None):
        """Get the displayed quantity for an item."""
        rows = self.find_all(By.CSS_SELECTOR, self.INVENTORY_ROW)
        for row in rows:
            row_name = row.get_attribute("data-item-name")
            row_loc = row.get_attribute("data-item-location")
            
            if row_name == name:
                if location is None or row_loc == location:
                    qty_cell = row.find_element(By.CSS_SELECTOR, '[data-testid^="item-quantity-"]')
                    return int(qty_cell.text)
        return None
    
    def get_inventory_count(self):
        return len(self.find_all(By.CSS_SELECTOR, self.INVENTORY_ROW))

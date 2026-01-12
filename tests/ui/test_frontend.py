"""
Selenium UI tests for the inventory management frontend.
Uses Page Object Model for maintainability.
"""

import pytest
import time
from selenium.webdriver.common.by import By

from .pages import HomePage


@pytest.mark.ui
class TestHomepage:
    
    def test_page_loads(self, browser, api_base_url):
        """Basic check that the page loads."""
        page = HomePage(browser, api_base_url)
        page.open()
        
        assert page.is_loaded()
        assert "FactoryFlow" in page.get_text(By.CSS_SELECTOR, '[data-testid="page-title"]')
    
    def test_add_form_visible(self, browser, api_base_url):
        page = HomePage(browser, api_base_url).open()
        assert page.is_visible(By.CSS_SELECTOR, '[data-testid="add-item-form"]')
    
    def test_move_form_visible(self, browser, api_base_url):
        page = HomePage(browser, api_base_url).open()
        assert page.is_visible(By.CSS_SELECTOR, '[data-testid="move-item-form"]')


@pytest.mark.ui
class TestAddItem:
    
    def test_add_item_shows_in_table(self, browser, api_base_url):
        """
        Main test case: add an item and verify it appears in the table.
        This is the scenario from the requirements.
        """
        page = HomePage(browser, api_base_url)
        page.open()
        
        page.add_item(
            name="Tesla Model S Battery",
            quantity=50,
            location="Warehouse A"
        )
        
        assert page.is_item_in_table("Tesla Model S Battery")
    
    def test_add_item_correct_quantity(self, browser, api_base_url):
        """Verify the quantity shows correctly."""
        page = HomePage(browser, api_base_url)
        timestamp = int(time.time())
        name = f"Test Part {timestamp}"
        
        page.open()
        page.add_item(name=name, quantity=75, location="Warehouse B")
        
        displayed = page.get_item_quantity(name, "Warehouse B")
        assert displayed == 75
    
    def test_add_multiple_items(self, browser, api_base_url):
        """Can add multiple items in sequence."""
        page = HomePage(browser, api_base_url)
        ts = int(time.time())
        items = [
            (f"Part A {ts}", 10, "Warehouse A"),
            (f"Part B {ts}", 20, "Warehouse B"),
        ]
        
        page.open()
        for name, qty, loc in items:
            page.add_item(name, qty, loc)
        
        for name, _, _ in items:
            assert page.is_item_in_table(name), f"{name} should be in table"


@pytest.mark.ui
class TestMoveItem:
    
    def test_move_updates_quantities(self, browser, api_base_url):
        """Move items and verify both source and dest update."""
        page = HomePage(browser, api_base_url)
        ts = int(time.time())
        name = f"Move Test {ts}"
        
        page.open()
        
        # Add 100 to Warehouse A
        page.add_item(name, 100, "Warehouse A")
        
        # Move 30 to Warehouse B
        page.move_item(name, 30, "Warehouse A", "Warehouse B")
        
        # Check quantities
        src_qty = page.get_item_quantity(name, "Warehouse A")
        dst_qty = page.get_item_quantity(name, "Warehouse B")
        
        assert src_qty == 70, f"Source should have 70, got {src_qty}"
        assert dst_qty == 30, f"Dest should have 30, got {dst_qty}"


@pytest.mark.smoke
@pytest.mark.ui
def test_critical_elements_present(browser, api_base_url):
    """Quick check that main UI elements exist."""
    page = HomePage(browser, api_base_url).open()
    
    elements = [
        '[data-testid="page-header"]',
        '[data-testid="add-item-form"]',
        '[data-testid="move-item-form"]',
        '[data-testid="inventory-section"]',
    ]
    
    for sel in elements:
        assert page.is_visible(By.CSS_SELECTOR, sel, timeout=3), f"Missing: {sel}"

"""Shared fixtures for all tests."""

import os
import time
import pytest
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# Config
APP_URL = os.getenv("APP_URL", "http://localhost:8000")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://factoryflow:factoryflow@localhost:5432/factoryflow")
SELENIUM_REMOTE_URL = os.getenv("SELENIUM_REMOTE_URL", None)
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"


# --- API Fixtures ---

@pytest.fixture(scope="session")
def api_base_url():
    return APP_URL


@pytest.fixture
def api_session():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    yield session
    session.close()


# --- Database Fixtures ---

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def clean_db(db_session):
    """Wipe the items table for a clean slate."""
    db_session.execute(text("TRUNCATE TABLE items RESTART IDENTITY CASCADE"))
    db_session.commit()
    yield db_session


# --- Browser Fixtures ---

@pytest.fixture
def chrome_options():
    options = Options()
    
    if HEADLESS:
        options.add_argument("--headless=new")
    
    # Needed for Docker/CI
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    return options


@pytest.fixture
def browser(chrome_options):
    driver = None
    
    try:
        if SELENIUM_REMOTE_URL:
            driver = webdriver.Remote(
                command_executor=SELENIUM_REMOTE_URL,
                options=chrome_options
            )
        else:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.implicitly_wait(10)
        yield driver
    finally:
        if driver:
            driver.quit()


# --- Test Data ---

@pytest.fixture
def sample_item():
    return {
        "name": "Tesla Model S Battery",
        "quantity": 100,
        "location": "Warehouse A"
    }


@pytest.fixture
def sample_items():
    return [
        {"name": "Tesla Model S Battery", "quantity": 100, "location": "Warehouse A"},
        {"name": "Tesla Model 3 Motor", "quantity": 50, "location": "Warehouse B"},
        {"name": "Tesla Model X Chassis", "quantity": 25, "location": "Warehouse A"},
    ]


# --- Markers ---

def pytest_configure(config):
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "ui: UI tests")
    config.addinivalue_line("markers", "data: Data integrity tests")
    config.addinivalue_line("markers", "smoke: Quick smoke tests")

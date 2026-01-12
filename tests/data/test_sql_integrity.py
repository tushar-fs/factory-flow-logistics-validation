"""
SQL verification tests.

These tests query the database directly to verify data integrity.
The API might return 200 OK but not actually save anything - these tests catch that.
"""

import pytest
import time
from sqlalchemy import text


@pytest.mark.data
class TestItemCreation:
    
    def test_created_item_in_database(self, api_session, api_base_url, db_session):
        """After POST /inventory, verify the row actually exists in the DB."""
        ts = int(time.time())
        item = {
            "name": f"DB Test Item {ts}",
            "quantity": 42,
            "location": "Warehouse A"
        }
        
        # Create via API
        resp = api_session.post(f"{api_base_url}/inventory", json=item)
        assert resp.status_code == 201
        
        # Query DB directly
        row = db_session.execute(
            text("SELECT name, quantity, location FROM items WHERE name = :name"),
            {"name": item["name"]}
        ).fetchone()
        
        assert row is not None, "Item should exist in database"
        assert row[0] == item["name"]
        assert row[1] == item["quantity"]
        assert row[2] == item["location"]


@pytest.mark.data
class TestMoveIntegrity:
    """
    These are the important tests - verify move operation at the DB level.
    """
    
    def test_move_updates_both_locations(self, api_session, api_base_url, db_session):
        """
        THE KEY TEST from requirements:
        1. Create item with 100 qty in Warehouse A
        2. Move 5 to Warehouse B
        3. Query SQL: A should have 95, B should have 5
        
        This proves the API didn't just fake a 200 OK.
        """
        ts = int(time.time())
        name = f"Move Integrity Test {ts}"
        
        # Setup: create item with 100 qty
        api_session.post(f"{api_base_url}/inventory", json={
            "name": name,
            "quantity": 100,
            "location": "Warehouse A"
        })
        
        # Get initial state
        before_a = db_session.execute(
            text("SELECT quantity FROM items WHERE name = :n AND location = 'Warehouse A'"),
            {"n": name}
        ).scalar()
        
        before_b = db_session.execute(
            text("SELECT quantity FROM items WHERE name = :n AND location = 'Warehouse B'"),
            {"n": name}
        ).scalar() or 0
        
        # Move 5 items
        resp = api_session.post(f"{api_base_url}/move", json={
            "item_name": name,
            "quantity": 5,
            "from_location": "Warehouse A",
            "to_location": "Warehouse B"
        })
        assert resp.status_code == 200
        
        # Refresh session and check DB
        db_session.expire_all()
        
        after_a = db_session.execute(
            text("SELECT quantity FROM items WHERE name = :n AND location = 'Warehouse A'"),
            {"n": name}
        ).scalar()
        
        after_b = db_session.execute(
            text("SELECT quantity FROM items WHERE name = :n AND location = 'Warehouse B'"),
            {"n": name}
        ).scalar()
        
        # Verify changes
        assert after_a == before_a - 5, f"Warehouse A: expected {before_a - 5}, got {after_a}"
        assert after_b == before_b + 5, f"Warehouse B: expected {before_b + 5}, got {after_b}"
    
    def test_move_conserves_total(self, api_session, api_base_url, db_session):
        """Total inventory should stay the same after a move."""
        ts = int(time.time())
        name = f"Conservation Test {ts}"
        
        # Create in two locations
        api_session.post(f"{api_base_url}/inventory", json={"name": name, "quantity": 50, "location": "Warehouse A"})
        api_session.post(f"{api_base_url}/inventory", json={"name": name, "quantity": 30, "location": "Warehouse B"})
        
        # Total before
        total_before = db_session.execute(
            text("SELECT SUM(quantity) FROM items WHERE name = :n"),
            {"n": name}
        ).scalar()
        
        # Do some moves
        api_session.post(f"{api_base_url}/move", json={
            "item_name": name, "quantity": 10,
            "from_location": "Warehouse A", "to_location": "Warehouse B"
        })
        api_session.post(f"{api_base_url}/move", json={
            "item_name": name, "quantity": 5,
            "from_location": "Warehouse B", "to_location": "Warehouse C"
        })
        
        # Total after
        db_session.expire_all()
        total_after = db_session.execute(
            text("SELECT SUM(quantity) FROM items WHERE name = :n"),
            {"n": name}
        ).scalar()
        
        assert total_before == total_after, f"Total changed from {total_before} to {total_after}"


@pytest.mark.data
class TestConstraints:
    
    def test_cannot_move_more_than_available(self, api_session, api_base_url, db_session):
        """API should reject move if insufficient quantity."""
        ts = int(time.time())
        name = f"Insufficient Test {ts}"
        
        # Create with 5 qty
        api_session.post(f"{api_base_url}/inventory", json={
            "name": name, "quantity": 5, "location": "Warehouse A"
        })
        
        # Try to move 10 (should fail)
        resp = api_session.post(f"{api_base_url}/move", json={
            "item_name": name, "quantity": 10,
            "from_location": "Warehouse A", "to_location": "Warehouse B"
        })
        
        assert resp.status_code == 400
        
        # Verify qty unchanged
        db_session.expire_all()
        qty = db_session.execute(
            text("SELECT quantity FROM items WHERE name = :n AND location = 'Warehouse A'"),
            {"n": name}
        ).scalar()
        
        assert qty == 5, "Quantity should be unchanged after failed move"
    
    def test_required_fields(self, api_session, api_base_url):
        """Missing required fields should return 422."""
        resp = api_session.post(f"{api_base_url}/inventory", json={
            "quantity": 10,
            "location": "Warehouse A"
            # missing name
        })
        
        assert resp.status_code == 422

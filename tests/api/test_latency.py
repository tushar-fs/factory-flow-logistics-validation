"""
API Latency Tests - enforce response time SLAs.

If response time > threshold, the test fails.
This catches performance regressions before they hit prod.
"""

import time
import pytest
import requests


# Response time limits (ms)
SLA = {
    "health": 100,
    "get_inventory": 200,
    "post_inventory": 300,
    "post_move": 300,
}


def get_response_time_ms(response):
    return response.elapsed.total_seconds() * 1000


@pytest.mark.api
class TestAPILatency:
    
    def test_health_latency(self, api_session, api_base_url):
        """Health check should be fast."""
        url = f"{api_base_url}/health"
        
        response = api_session.get(url)
        elapsed = get_response_time_ms(response)
        
        assert response.status_code == 200
        assert elapsed < SLA["health"], f"Health took {elapsed:.0f}ms, limit is {SLA['health']}ms"
    
    def test_get_inventory_latency(self, api_session, api_base_url):
        """GET /inventory should respond under 200ms."""
        url = f"{api_base_url}/inventory"
        
        response = api_session.get(url)
        elapsed = get_response_time_ms(response)
        
        assert response.status_code == 200
        assert elapsed < SLA["get_inventory"], f"GET /inventory took {elapsed:.0f}ms, limit is {SLA['get_inventory']}ms"
    
    def test_post_inventory_latency(self, api_session, api_base_url):
        """POST /inventory should respond under 300ms."""
        url = f"{api_base_url}/inventory"
        item = {
            "name": f"Latency Test {time.time()}",
            "quantity": 10,
            "location": "Warehouse A"
        }
        
        response = api_session.post(url, json=item)
        elapsed = get_response_time_ms(response)
        
        assert response.status_code == 201
        assert elapsed < SLA["post_inventory"], f"POST /inventory took {elapsed:.0f}ms, limit is {SLA['post_inventory']}ms"
    
    def test_move_latency(self, api_session, api_base_url):
        """POST /move should respond under 300ms."""
        # Setup - create source item first
        source = {
            "name": f"Move Test {time.time()}",
            "quantity": 100,
            "location": "Warehouse A"
        }
        api_session.post(f"{api_base_url}/inventory", json=source)
        
        # Test move
        move_req = {
            "item_name": source["name"],
            "quantity": 10,
            "from_location": "Warehouse A",
            "to_location": "Warehouse B"
        }
        
        response = api_session.post(f"{api_base_url}/move", json=move_req)
        elapsed = get_response_time_ms(response)
        
        assert response.status_code == 200
        assert elapsed < SLA["post_move"], f"POST /move took {elapsed:.0f}ms, limit is {SLA['post_move']}ms"
    
    def test_multiple_requests_consistent(self, api_session, api_base_url):
        """Run 10 requests, all should meet SLA."""
        url = f"{api_base_url}/inventory"
        times = []
        
        for _ in range(10):
            response = api_session.get(url)
            times.append(get_response_time_ms(response))
            assert response.status_code == 200
        
        avg = sum(times) / len(times)
        max_time = max(times)
        
        assert max_time < SLA["get_inventory"], f"Max response {max_time:.0f}ms exceeded SLA"
        print(f"\n10 requests - avg: {avg:.0f}ms, max: {max_time:.0f}ms")


@pytest.mark.smoke
@pytest.mark.api
def test_endpoints_reachable(api_session, api_base_url):
    """Quick check that all endpoints respond."""
    endpoints = [
        ("GET", "/health", 200),
        ("GET", "/inventory", 200),
        ("GET", "/docs", 200),
    ]
    
    for method, path, expected in endpoints:
        response = api_session.request(method, f"{api_base_url}{path}")
        assert response.status_code == expected, f"{method} {path} returned {response.status_code}"

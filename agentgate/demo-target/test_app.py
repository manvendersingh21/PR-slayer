"""
Tests for the Orders API
"""
import pytest
from fastapi.testclient import TestClient
from app import app, orders_db, payments_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    """Reset database before each test"""
    orders_db.clear()
    payments_db.clear()
    yield


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_create_order():
    response = client.post("/orders", json={
        "user_id": "user123",
        "amount": 100.0
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user123"
    assert data["amount"] == 100.0
    assert data["status"] == "pending"
    assert "id" in data


def test_get_order():
    # Create order first
    create_resp = client.post("/orders", json={
        "user_id": "user123",
        "amount": 100.0
    })
    order_id = create_resp.json()["id"]
    
    # Get order
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    assert response.json()["id"] == order_id


def test_create_payment():
    # Create order first
    order_resp = client.post("/orders", json={
        "user_id": "user123",
        "amount": 100.0
    })
    order_id = order_resp.json()["id"]
    
    # Create payment
    response = client.post("/payments", json={
        "order_id": order_id,
        "amount": 100.0
    })
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == order_id
    assert data["amount"] == 100.0
    assert data["status"] == "completed"


def test_refund_requires_authentication():
    """
    CRITICAL: Refund must verify the user owns the order
    This test will fail if refund endpoint has missing auth check
    """
    # Create order for user1
    order_resp = client.post("/orders", json={
        "user_id": "user1",
        "amount": 100.0
    })
    order_id = order_resp.json()["id"]
    
    # Pay for order
    payment_resp = client.post("/payments", json={
        "order_id": order_id,
        "amount": 100.0
    })
    payment_id = payment_resp.json()["id"]
    
    # Try to refund as different user (should fail)
    response = client.post("/refunds", json={
        "payment_id": payment_id,
        "user_id": "user2"  # Different user!
    })
    assert response.status_code == 403, "Refund must check user ownership"


def test_refund_amount_validation():
    """
    CRITICAL: Refund amount must not exceed original payment
    This test will fail if refund allows excessive amounts
    """
    # Create and pay for order
    order_resp = client.post("/orders", json={
        "user_id": "user1",
        "amount": 100.0
    })
    order_id = order_resp.json()["id"]
    
    payment_resp = client.post("/payments", json={
        "order_id": order_id,
        "amount": 100.0
    })
    payment_id = payment_resp.json()["id"]
    
    # Try to refund more than paid (should fail)
    response = client.post("/refunds", json={
        "payment_id": payment_id,
        "amount": 150.0,  # More than original!
        "user_id": "user1"
    })
    assert response.status_code == 400, "Refund amount must not exceed payment"


def test_double_refund_prevention():
    """
    CRITICAL: Cannot refund the same payment twice
    This test will fail if double refunds are allowed
    """
    # Create and pay for order
    order_resp = client.post("/orders", json={
        "user_id": "user1",
        "amount": 100.0
    })
    order_id = order_resp.json()["id"]
    
    payment_resp = client.post("/payments", json={
        "order_id": order_id,
        "amount": 100.0
    })
    payment_id = payment_resp.json()["id"]
    
    # First refund (should succeed)
    response1 = client.post("/refunds", json={
        "payment_id": payment_id,
        "amount": 100.0,
        "user_id": "user1"
    })
    assert response1.status_code == 200
    
    # Second refund (should fail)
    response2 = client.post("/refunds", json={
        "payment_id": payment_id,
        "amount": 100.0,
        "user_id": "user1"
    })
    assert response2.status_code == 400, "Cannot refund twice"

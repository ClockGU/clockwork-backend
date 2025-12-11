import uuid
from fastapi.testclient import TestClient
import pytest


from api.db.schema.petition import Petition

# Helper function to return sample petition data matching your PetitionCreate schema.
def sample_petition_data():
    return {
        "user_account": "user@example.com",
        "org_unit": "Finance",
        "eos_number": "EOS123",
        "start_date": "2025-03-03",
        "end_date": "2025-03-10",
        "minutes": 60,
        "ba_degree": "Bachelor's",
        "budget_position": "Manager",
        "budget_approver": "Approver",
        "student_username": "student1"
        # Optional fields can be omitted or provided as needed.
    }


def test_create_petition(client):
    petition_data = sample_petition_data()
    response = client.post("/petitions/", json=petition_data)
    assert response.status_code == 200
    data = response.json()
    # Check that an id is generated and the returned fields match our input.
    assert "id" in data
    for key, value in petition_data.items():
        assert data[key] == value

def test_list_petitions(client):
    # Create two petitions.
    petition_data1 = sample_petition_data()
    petition_data2 = sample_petition_data()
    petition_data2["org_unit"] = "HR"  # Change one field for variety.
    
    client.post("/petitions/", json=petition_data1)
    client.post("/petitions/", json=petition_data2)
    
    response = client.get("/petitions/")
    assert response.status_code == 200
    data = response.json()
    # Expect two petitions in the list.
    assert isinstance(data, list)
    assert len(data) == 2

def test_read_petition(client):
    petition_data = sample_petition_data()
    create_response = client.post("/petitions/", json=petition_data)
    assert create_response.status_code == 200
    created = create_response.json()
    petition_id = created["id"]
    
    response = client.get(f"/petitions/{petition_id}")
    assert response.status_code == 200
    data = response.json()
    # Verify that the petition returned has the same id and data.
    assert data["id"] == petition_id
    for key, value in petition_data.items():
        assert data[key] == value

def test_read_petition_not_found(client):
    # Use a random UUID that does not exist.
    non_existent_id = str(uuid.uuid4())
    response = client.get(f"/petitions/{non_existent_id}")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Petition not found"

def test_update_petition(client):
    petition_data = sample_petition_data()
    create_response = client.post("/petitions/", json=petition_data)
    assert create_response.status_code == 200
    created = create_response.json()
    petition_id = created["id"]
    
    # Prepare updated data. Here, we change the org_unit field.
    updated_data = sample_petition_data()
    updated_data["org_unit"] = "HR"
    
    response = client.put(f"/petitions/{petition_id}", json=updated_data)
    assert response.status_code == 200
    data = response.json()
    # Verify the update took effect.
    assert data["org_unit"] == "HR"
    for key, value in updated_data.items():
        assert data[key] == value

def test_update_petition_not_found(client):
    non_existent_id = str(uuid.uuid4())
    petition_data = sample_petition_data()
    response = client.put(f"/petitions/{non_existent_id}", json=petition_data)
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Petition not found"

def test_delete_petition(client):
    petition_data = sample_petition_data()
    create_response = client.post("/petitions/", json=petition_data)
    assert create_response.status_code == 200
    created = create_response.json()
    petition_id = created["id"]
    
    delete_response = client.delete(f"/petitions/{petition_id}")
    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data["detail"] == "Petition deleted successfully"
    
    # Verify that trying to fetch the deleted petition returns 404.
    get_response = client.get(f"/petitions/{petition_id}")
    assert get_response.status_code == 404

def test_delete_petition_not_found(client):
    non_existent_id = str(uuid.uuid4())
    response = client.delete(f"/petitions/{non_existent_id}")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Petition not found"

from fastapi import status
from app.models.job import JobStatus
from app.models.certificate import CertificateStatus

def test_create_bulk_job_success(client):
    payload = {
        "title": "Backend Engineering Bootcamp 2026",
        "issuer_name": "AeroCloud Certification Authority",
        "course_or_event": "Python & FastAPI Fundamentals",
        "issue_date": "2026-10-10",
        "recipients": [
            {
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "identifier": "STU-1001",
                "custom_attributes": {"grade": "A+"}
            },
            {
                "name": "Bob Smith",
                "email": "bob@example.com",
                "identifier": "STU-1002",
                "custom_attributes": {"grade": "A"}
            }
        ]
    }

    # Pass process_async=false for instant synchronous execution in test
    response = client.post("/api/v1/jobs?process_async=false", json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED
    
    data = response.json()
    assert "id" in data
    assert data["title"] == payload["title"]
    assert data["total_recipients"] == 2
    assert data["successful_count"] == 2
    assert data["failed_count"] == 0
    assert data["status"] == JobStatus.COMPLETED.value
    assert data["progress_percentage"] == 100.0

def test_list_jobs(client):
    payload = {
        "title": "Event Workshop",
        "course_or_event": "AI Systems",
        "issue_date": "2026-10-10",
        "recipients": [
            {"name": "Charlie Brown", "email": "charlie@example.com"}
        ]
    }
    client.post("/api/v1/jobs?process_async=false", json=payload)
    
    response = client.get("/api/v1/jobs")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["title"] == "Event Workshop"

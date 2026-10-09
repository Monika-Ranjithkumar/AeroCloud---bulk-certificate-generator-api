from fastapi import status

def test_missing_required_job_fields(client):
    payload = {
        "title": "Incomplete Request"
        # Missing course_or_event, issue_date, recipients
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data

def test_empty_recipients_list(client):
    payload = {
        "title": "Empty Recipients Test",
        "course_or_event": "Docker Workshop",
        "issue_date": "2026-10-10",
        "recipients": []
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_invalid_recipient_email_format(client):
    payload = {
        "title": "Bad Email Test",
        "course_or_event": "Security 101",
        "issue_date": "2026-10-10",
        "recipients": [
            {
                "name": "David Miller",
                "email": "not-an-email-address"
            }
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_blank_recipient_name(client):
    payload = {
        "title": "Blank Name Test",
        "course_or_event": "Security 101",
        "issue_date": "2026-10-10",
        "recipients": [
            {
                "name": "   ",
                "email": "david@example.com"
            }
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

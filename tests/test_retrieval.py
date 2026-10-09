from fastapi import status

def test_certificate_retrieval_and_verification(client):
    payload = {
        "title": "Cloud Architecture 2026",
        "course_or_event": "AWS & Kubernetes",
        "issue_date": "2026-10-10",
        "recipients": [
            {
                "name": "Grace Hopper",
                "email": "grace@example.com",
                "identifier": "ENG-4001"
            }
        ]
    }

    # Create job synchronously
    job_resp = client.post("/api/v1/jobs?process_async=false", json=payload)
    assert job_resp.status_code == status.HTTP_202_ACCEPTED
    job_id = job_resp.json()["id"]

    # Get job details to retrieve certificate ID and code
    details_resp = client.get(f"/api/v1/jobs/{job_id}/details")
    assert details_resp.status_code == status.HTTP_200_OK
    details = details_resp.json()

    assert len(details["successful_certificates"]) == 1
    cert = details["successful_certificates"][0]
    cert_id = cert["id"]
    cert_code = cert["certificate_code"]

    # 1. Test Metadata retrieval
    meta_resp = client.get(f"/api/v1/certificates/{cert_id}")
    assert meta_resp.status_code == status.HTTP_200_OK
    assert meta_resp.json()["recipient_name"] == "Grace Hopper"

    # 2. Test PDF Download
    pdf_resp = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert pdf_resp.status_code == status.HTTP_200_OK
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 0

    # 3. Test Preview Image Download
    preview_resp = client.get(f"/api/v1/certificates/{cert_id}/preview")
    assert preview_resp.status_code == status.HTTP_200_OK
    assert preview_resp.headers["content-type"] == "image/png"

    # 4. Test Verification Endpoint (Valid Code)
    verify_valid = client.get(f"/api/v1/certificates/verify/{cert_code}")
    assert verify_valid.status_code == status.HTTP_200_OK
    v_data = verify_valid.json()
    assert v_data["valid"] is True
    assert v_data["recipient_name"] == "Grace Hopper"
    assert v_data["course_or_event"] == "AWS & Kubernetes"

    # 5. Test Verification Endpoint (Invalid Code)
    verify_invalid = client.get("/api/v1/certificates/verify/INVALID-CODE-9999")
    assert verify_invalid.status_code == status.HTTP_200_OK
    inv_data = verify_invalid.json()
    assert inv_data["valid"] is False

    # 6. Test ZIP Archive Download
    zip_resp = client.get(f"/api/v1/jobs/{job_id}/download-zip")
    assert zip_resp.status_code == status.HTTP_200_OK
    assert zip_resp.headers["content-type"] == "application/zip"
    assert len(zip_resp.content) > 0

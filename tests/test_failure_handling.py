from unittest.mock import patch
from fastapi import status
from app.models.job import JobStatus
from app.models.certificate import CertificateStatus

def test_partial_failure_in_batch(client):
    """
    Submits a batch where one recipient triggers an error during PDF rendering,
    while valid recipients complete successfully.
    Verifies partial failure isolation.
    """
    payload = {
        "title": "Robotics Masterclass",
        "course_or_event": "Autonomous Drones",
        "issue_date": "2026-10-10",
        "recipients": [
            {
                "name": "Valid Recipient 1",
                "email": "valid1@example.com"
            },
            {
                "name": "Failing Recipient 2",
                "email": "failing2@example.com"
            },
            {
                "name": "Valid Recipient 3",
                "email": "valid3@example.com"
            }
        ]
    }

    # Mock CertificateGenerator.generate_pdf to throw exception ONLY for Failing Recipient 2
    original_generate = client.app.dependency_overrides

    from app.services.generator import CertificateGenerator
    real_generate_pdf = CertificateGenerator.generate_pdf

    def mocked_generate_pdf(*args, **kwargs):
        recipient_name = kwargs.get("recipient_name") or (args[1] if len(args) > 1 else "")
        if "Failing Recipient 2" in recipient_name:
            raise RuntimeError("Simulated render crash: missing font or corrupted buffer")
        return real_generate_pdf(*args, **kwargs)

    with patch.object(CertificateGenerator, "generate_pdf", side_effect=mocked_generate_pdf):
        response = client.post("/api/v1/jobs?process_async=false", json=payload)
        assert response.status_code == status.HTTP_202_ACCEPTED
        job_data = response.json()

        assert job_data["status"] == JobStatus.PARTIALLY_COMPLETED.value
        assert job_data["total_recipients"] == 3
        assert job_data["successful_count"] == 2
        assert job_data["failed_count"] == 1
        assert job_data["progress_percentage"] == 100.0

        # Fetch detailed breakdown of job
        details_resp = client.get(f"/api/v1/jobs/{job_data['id']}/details")
        assert details_resp.status_code == status.HTTP_200_OK
        details = details_resp.json()

        assert len(details["successful_certificates"]) == 2
        assert len(details["failed_certificates"]) == 1

        failed_cert = details["failed_certificates"][0]
        assert failed_cert["recipient_name"] == "Failing Recipient 2"
        assert failed_cert["status"] == CertificateStatus.FAILED.value
        assert "Simulated render crash" in failed_cert["error_message"]

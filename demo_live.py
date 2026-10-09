import json
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db

def run_demo():
    init_db()
    print("=" * 70)
    print("      BULK CERTIFICATE GENERATOR - LIVE END-TO-END DEMO")
    print("=" * 70)
    
    client = TestClient(app)
    
    # 1. Health check
    health = client.get("/health").json()
    print("\n[1] Healthcheck:")
    print(json.dumps(health, indent=2))

    # 2. Submit Bulk Certificate Generation Request
    payload = {
        "title": "Global Tech Summit 2026",
        "issuer_name": "Aricloud Certification Authority",
        "course_or_event": "Mastering Distributed Cloud Systems",
        "issue_date": "2026-10-10",
        "send_email": True,
        "recipients": [
            {
                "name": "Sarah Connor",
                "email": "sarah.connor@cyberdyne.org",
                "identifier": "ENG-2026-01",
                "custom_attributes": {"track": "Cloud Architecture", "grade": "High Distinction"}
            },
            {
                "name": "Marcus Wright",
                "email": "marcus.wright@resistance.io",
                "identifier": "ENG-2026-02",
                "custom_attributes": {"track": "Cybersecurity", "grade": "Distinction"}
            },
            {
                "name": "Kyle Reese",
                "email": "kyle.reese@future.net",
                "identifier": "ENG-2026-03",
                "custom_attributes": {"track": "AI Operations", "grade": "Merit"}
            }
        ]
    }

    print("\n[2] Submitting Bulk Certificate Job Request...")
    response = client.post("/api/v1/jobs?process_async=false", json=payload)
    print(f"HTTP Status Code: {response.status_code}")
    job_status = response.json()
    print("Job Response:")
    print(json.dumps(job_status, indent=2))

    job_id = job_status["id"]

    # 3. Retrieve Detailed Progress & Certificate Listing
    print(f"\n[3] Fetching Job Details for Job ID '{job_id}'...")
    details_resp = client.get(f"/api/v1/jobs/{job_id}/details")
    details = details_resp.json()
    print(json.dumps(details, indent=2))

    # 4. Certificate Verification Demo
    if details["successful_certificates"]:
        sample_cert = details["successful_certificates"][0]
        cert_code = sample_cert["certificate_code"]
        cert_id = sample_cert["id"]

        print(f"\n[4] Verifying Certificate Code '{cert_code}'...")
        verify_resp = client.get(f"/api/v1/certificates/verify/{cert_code}")
        print("Verification Result:")
        print(json.dumps(verify_resp.json(), indent=2))

        # 5. Download Certificate PDF test
        print(f"\n[5] Testing Certificate PDF Download for ID '{cert_id}'...")
        pdf_resp = client.get(f"/api/v1/certificates/{cert_id}/download")
        print(f"Content-Type: {pdf_resp.headers.get('content-type')}")
        print(f"PDF File Size: {len(pdf_resp.content)} bytes")

    # 6. Bulk Export ZIP Archive Demo
    print(f"\n[6] Exporting Bulk ZIP Archive for Job ID '{job_id}'...")
    zip_resp = client.get(f"/api/v1/jobs/{job_id}/download-zip")
    print(f"Content-Type: {zip_resp.headers.get('content-type')}")
    print(f"ZIP Archive File Size: {len(zip_resp.content)} bytes")

    print("\n" + "=" * 70)
    print("               DEMO EXECUTED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    run_demo()

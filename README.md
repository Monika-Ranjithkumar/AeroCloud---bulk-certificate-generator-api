# Bulk Certificate Generator API

A high-performance, robust backend service built in **Python** using **FastAPI** and **SQLAlchemy** to generate personalized event/course certificates in bulk for large lists of recipients.

---

## 🌟 Key Features

1. **Bulk Certificate Request Processing**:
   - Submit hundreds or thousands of certificate requests in a single API call (`POST /api/v1/jobs`).
   - Asynchronous background task execution (`202 Accepted`) prevents HTTP timeouts.
   - Synchronous processing option available for instant validation or testing (`?process_async=false`).

2. **Input Validation**:
   - Strict Pydantic v2 schema validation for recipient email syntax, recipient name length, and custom metadata.
   - Invalid payloads are isolated per recipient with specific error diagnostics attached.

3. **High-Quality PDF & Preview Rendering**:
   - Uses **ReportLab** to generate crisp, print-ready landscape PDF certificates.
   - Uses **Pillow (PIL)** to generate high-resolution PNG image previews for web display.
   - Embedded **QR Codes** (via `qrcode`) link directly to an online verification endpoint.

4. **Progress & Status Tracking**:
   - Track overall batch job status (`pending`, `processing`, `completed`, `partially_completed`, `failed`).
   - Real-time percentage progress (`progress_percentage`) and success/failure counters (`successful_count`, `failed_count`).

5. **Partial Failure Isolation**:
   - If rendering or data processing fails for an individual recipient (e.g. corrupt payload or missing custom asset), the failure is logged on that specific record.
   - The remaining valid recipients in the same batch continue processing without interruption.

6. **Flexible Retrieval & Bulk Export**:
   - Download individual PDF certificates (`GET /api/v1/certificates/{id}/download`).
   - Download PNG preview images (`GET /api/v1/certificates/{id}/preview`).
   - Export all successfully generated PDF certificates for a job in a single **ZIP archive** (`GET /api/v1/jobs/{id}/download-zip`).

7. **Public Certificate Verification API**:
   - Direct verification endpoint (`GET /api/v1/certificates/verify/{certificate_code}`) to verify recipient authenticity and issue details.

---

## 🛠 Tech Stack

- **Language**: Python 3.9+
- **Web Framework**: FastAPI (Async ready, Pydantic v2, OpenAPI/Swagger UI)
- **Database & ORM**: SQLAlchemy 2.0 with SQLite (zero-config default, easily configurable to PostgreSQL via `DATABASE_URL`)
- **PDF Generation**: ReportLab
- **Image Generation**: Pillow (PIL)
- **QR Code Engine**: qrcode
- **Testing**: Pytest & HTTPX TestClient

---

## 📁 Project Structure

```
d:\Aricloud\
├── app/
│   ├── api/
│   │   ├── deps.py               # Database dependency injection
│   │   └── v1/
│   │       ├── certificates.py   # Certificate metadata, download & verification endpoints
│   │       └── jobs.py           # Bulk job submission, status & ZIP export endpoints
│   ├── config.py                 # Application settings & storage directory initialization
│   ├── database.py               # SQLAlchemy engine, session maker & schema initialization
│   ├── main.py                   # FastAPI application entrypoint & middleware setup
│   ├── models/
│   │   ├── certificate.py        # CertificateRecord ORM model
│   │   └── job.py                # CertificateJob ORM model
│   ├── schemas/
│   │   ├── certificate.py        # Certificate & verification response schemas
│   │   ├── job.py                # Job create request & status response schemas
│   │   └── recipient.py          # Recipient data validation schema
│   └── services/
│       ├── generator.py          # ReportLab & PIL PDF/PNG rendering engine
│       └── job_processor.py      # Background task processor & ZIP export generator
├── storage/                      # Local filesystem storage for PDFs, previews & ZIPs
├── tests/                        # Automated Pytest suite
│   ├── conftest.py               # Test database fixtures & client setup
│   ├── test_failure_handling.py  # Partial failure isolation tests
│   ├── test_generator.py         # PDF & image rendering unit tests
│   ├── test_job_creation.py      # Bulk job submission & listing tests
│   ├── test_retrieval.py         # Certificate download & verification tests
│   └── test_validation.py        # Input schema validation tests
├── pytest.ini                    # Pytest configuration
├── requirements.txt              # Python package dependencies
├── run.py                        # Server runner script
└── README.md                     # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9 or higher installed.

### 2. Setup Virtual Environment & Install Dependencies

```bash
# Clone or open project directory
cd d:\Aricloud

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate virtual environment (Linux/macOS)
# source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

---

## 🏃 Running the Application

Start the development server using `run.py`:

```bash
python run.py
```

Or using Uvicorn directly:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once running, access:
- **Interactive Swagger API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Running Automated Tests

The application includes a comprehensive test suite covering job creation, input validation, PDF generation, partial failure handling, certificate download, ZIP exports, and QR code verification.

Execute all tests with Pytest:

```bash
pytest
```

To view verbose test output:

```bash
pytest -v
```

---

## 📖 API Usage Guide

### 1. Submit a Bulk Certificate Generation Request

**Endpoint**: `POST /api/v1/jobs`

**Headers**: `Content-Type: application/json`

**Sample Request (`curl`)**:

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/jobs' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Backend Engineering Bootcamp 2026",
    "issuer_name": "Aricloud Certification Authority",
    "course_or_event": "Advanced Python & FastAPI Architecture",
    "issue_date": "2026-10-10",
    "recipients": [
      {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "identifier": "STU-1001",
        "custom_attributes": {
          "grade": "A+",
          "honor": "Distinction"
        }
      },
      {
        "name": "Bob Smith",
        "email": "bob@example.com",
        "identifier": "STU-1002",
        "custom_attributes": {
          "grade": "A"
        }
      }
    ]
  }'
```

**Response (`202 Accepted`)**:

```json
{
  "id": "e83b4a12-5c91-4d1a-a123-89b09f123456",
  "title": "Backend Engineering Bootcamp 2026",
  "issuer_name": "Aricloud Certification Authority",
  "course_or_event": "Advanced Python & FastAPI Architecture",
  "issue_date": "2026-10-10",
  "status": "pending",
  "total_recipients": 2,
  "processed_count": 0,
  "successful_count": 0,
  "failed_count": 0,
  "progress_percentage": 0.0,
  "error_summary": null,
  "created_at": "2026-10-09T22:00:00.000000",
  "updated_at": "2026-10-09T22:00:00.000000"
}
```

---

### 2. Check Job Progress / Status

**Endpoint**: `GET /api/v1/jobs/{job_id}`

```bash
curl -X 'GET' 'http://localhost:8000/api/v1/jobs/e83b4a12-5c91-4d1a-a123-89b09f123456'
```

**Response (`200 OK`)**:

```json
{
  "id": "e83b4a12-5c91-4d1a-a123-89b09f123456",
  "title": "Backend Engineering Bootcamp 2026",
  "issuer_name": "Aricloud Certification Authority",
  "course_or_event": "Advanced Python & FastAPI Architecture",
  "issue_date": "2026-10-10",
  "status": "completed",
  "total_recipients": 2,
  "processed_count": 2,
  "successful_count": 2,
  "failed_count": 0,
  "progress_percentage": 100.0,
  "error_summary": null,
  "created_at": "2026-10-09T22:00:00.000000",
  "updated_at": "2026-10-09T22:00:02.000000"
}
```

---

### 3. Check Detailed Job Progress (Passed vs Failed Items)

**Endpoint**: `GET /api/v1/jobs/{job_id}/details`

```bash
curl -X 'GET' 'http://localhost:8000/api/v1/jobs/e83b4a12-5c91-4d1a-a123-89b09f123456/details'
```

**Response (`200 OK`)**:

```json
{
  "job": {
    "id": "e83b4a12-5c91-4d1a-a123-89b09f123456",
    "status": "completed",
    "total_recipients": 2,
    "processed_count": 2,
    "successful_count": 2,
    "failed_count": 0,
    "progress_percentage": 100.0
  },
  "successful_certificates": [
    {
      "id": "cert-1111-2222-3333",
      "job_id": "e83b4a12-5c91-4d1a-a123-89b09f123456",
      "recipient_name": "Alice Johnson",
      "recipient_email": "alice@example.com",
      "status": "generated",
      "certificate_code": "CERT-2026-A1B2C3D4",
      "download_url": "/api/v1/certificates/cert-1111-2222-3333/download",
      "preview_url": "/api/v1/certificates/cert-1111-2222-3333/preview"
    }
  ],
  "failed_certificates": []
}
```

---

### 4. Download Generated Certificates

- **Download Individual PDF**:
  `GET /api/v1/certificates/{certificate_id}/download`

- **View PNG Image Preview**:
  `GET /api/v1/certificates/{certificate_id}/preview`

- **Download All Certificates in a Batch (ZIP Archive)**:
  `GET /api/v1/jobs/{job_id}/download-zip`

```bash
# Example download ZIP archive
curl -O 'http://localhost:8000/api/v1/jobs/e83b4a12-5c91-4d1a-a123-89b09f123456/download-zip'
```

---

### 5. Verify Certificate Authenticity

Scan QR code or query the verification endpoint directly:

**Endpoint**: `GET /api/v1/certificates/verify/{certificate_code}`

```bash
curl -X 'GET' 'http://localhost:8000/api/v1/certificates/verify/CERT-2026-A1B2C3D4'
```

**Response (`200 OK`)**:

```json
{
  "valid": true,
  "certificate_code": "CERT-2026-A1B2C3D4",
  "recipient_name": "Alice Johnson",
  "course_or_event": "Advanced Python & FastAPI Architecture",
  "issuer_name": "Aricloud Certification Authority",
  "issue_date": "2026-10-10",
  "generated_at": "2026-10-09T22:00:02.000000",
  "message": "Certificate is authentic and valid."
}
```

---

## 📐 Implementation & Design Decisions

### 1. Asynchronous Background Processing Model
- **Choice**: Bulk requests return an instant `202 Accepted` response with a unique `job_id`, deferring PDF/PNG generation to background worker tasks (`FastAPI BackgroundTasks` / ThreadPool execution engine).
- **Reasoning**: Generating PDFs and QR codes for large recipient lists (e.g. 1,000+ recipients) can take several seconds to minutes. Synchronous processing would cause client HTTP timeouts. Background processing ensures fast API response times while allowing clients to query progress periodically.
- **Scalability Note**: The service uses an independent database session per worker thread, making it trivial to substitute `BackgroundTasks` with **Celery** or **Redis Queue (RQ)** for distributed worker clusters in high-traffic production environments.

### 2. Partial Failure Isolation & Atomic Item Commits
- **Choice**: Each recipient record in a bulk batch is processed within an isolated `try...except` block, committing individual record statuses (`GENERATED` or `FAILED`) immediately upon completion.
- **Reasoning**: A corrupted recipient payload or rendering fault should not invalidate an entire batch job of valid certificates. Valid certificates are created and stored, while failing items log their detailed error message (`error_message`) for inspection and retry.
- **Job Status Matrix**:
  - `COMPLETED`: All recipient certificates rendered successfully (`failed_count == 0`).
  - `PARTIALLY_COMPLETED`: At least one certificate rendered successfully, and at least one failed (`successful_count > 0` and `failed_count > 0`).
  - `FAILED`: All recipients failed validation or rendering (`successful_count == 0`).

### 3. QR Code Embedding & Authenticity Verification Scheme
- **Choice**: Every generated certificate contains a unique alphanumeric identifier (`CERT-YYYY-XXXXXXXX`) and an embedded high-resolution QR code pointing to the verification API endpoint.
- **Reasoning**: QR codes provide instant anti-tamper verification for third parties (employers, academic institutions) scanning the certificate.

### 4. Pure Python PDF & Image Generation Stack
- **Choice**: Used **ReportLab** for vector PDF generation and **Pillow** for raster PNG image previews.
- **Reasoning**: Pure Python libraries eliminate heavy C binary runtime dependencies (e.g., `wkhtmltopdf` or system GTK libraries for `WeasyPrint`), ensuring cross-platform portability on Windows, Linux, and macOS.

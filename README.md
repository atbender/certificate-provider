# Certificate Provider

A simple service that creates and validates digital certificates for training providers.

![certificate example](assets/certificate-example.png)

## Quick Start

```bash
docker compose up --build
```

## What It Does

- **Creates digital certificates** with unique IDs and verification codes
- **Validates certificates** through an API or web interface
- **Provides PDF certificates** with student name, course details, and instructors

## How to Use

### Creating Certificates

Send a POST request to `/api/generate` with your admin token:

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: your-secure-admin-token" \
  -d '{
    "student_name": "John Doe",
    "course_name": "Kubernetes Administration",
    "issue_date": "2023-05-15",
    "instructor": "Jane Smith",
    "co_instructor": "Bob Johnson"
  }'
```

### Validating Certificates

**Option 1:** Use the web interface at `http://localhost:8000`

**Option 2:** Use the API:

```bash
# Simple GET request
curl "http://localhost:8000/api/validate?certificate_id=KC-202305-4C2A90-C9B1&verification_code=WEDGD0HZII0B"
```

### Viewing & Downloading

**Option 1:** Use the web interface at `http://localhost:8000`

**Option 2:** Use the following endpoints with query parameters:

```bash
# View in browser
http://localhost:8000/view?certificate_id=KC-202305-4C2A90-C9B1&verification_code=WEDGD0HZII0B

# Download
http://localhost:8000/download?certificate_id=KC-202305-4C2A90-C9B1&verification_code=WEDGD0HZII0B
```

## Setup Requirements

- Set the `ADMIN_TOKEN` environment variable before starting the application
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
curl -X POST "http://localhost:8050/api/generate" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: your-secure-admin-token" \
  -d '{
    "student_name": "STUDENT_NAME",
    "course_name": "COURSE_NAME",
    "issue_date": "ISSUE_DATE",
    "instructor": "INSTRUCTOR",
    "instructor_title": "INSTRUCTOR_TITLE",
    "co_instructor": "CO_INSTRUCTOR",
    "co_instructor_title": "CO_INSTRUCTOR_TITLE",
    "organization": "ORGANIZATION",
    "place": "PLACE",
    "certification_type": "CERTIFICATION_TYPE",
    "hours": "HOURS"
  }'
```

### Validating Certificates

**Option 1:** Use the web interface at `http://localhost:8050`

**Option 2:** Use the API:

```bash
# Simple GET request
curl "http://localhost:8050/api/validate?certificate_id=KC-202503-819012-391D&verification_code=QO5JG6ZAYZWZ"
```

### Viewing & Downloading

**Option 1:** Use the web interface at `http://localhost:8050`

**Option 2:** Use the following endpoints with query parameters:

```bash
# View in browser
http://localhost:8050/view?certificate_id=KC-202503-819012-391D&verification_code=QO5JG6ZAYZWZ
```

```bash
# Download
http://localhost:8050/download?certificate_id=KC-202503-819012-391D&verification_code=QO5JG6ZAYZWZ
```

## Setup Requirements

- Set the `ADMIN_TOKEN` environment variable before starting the application.

- Default token is `your-secure-admin-token`

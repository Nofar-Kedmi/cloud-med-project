# Cloud-Based Medical Information System

A Flask MVC web application for managing patients, doctor visits, prescriptions, and pharmacist dispensing workflows. The system integrates MongoDB Atlas for persistence, Google Cloud Vision for prescription OCR and document validation, Google Drive for PDF storage, and Tavily for clinical intelligence lookups.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- MongoDB Atlas cluster (or compatible MongoDB instance)
- Google Cloud service account JSON for Vision API (`google_vision_credentials.json`)
- Optional: Google Drive OAuth credentials for physician PDF uploads

## Setup Before Running Docker

### 1. Place credentials in the project root

Copy your Google Vision service account file to the repository root:

```text
Cloud Computing Project/
├── google_vision_credentials.json   ← place here
├── .env
├── Dockerfile
└── run.py
```

### 2. Create a `.env` file

Copy `.env.example` to `.env` and fill in your values. At minimum you need:

```env
SECRET_KEY=your-secret-key
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=cloud_med_project
GOOGLE_VISION_CREDENTIALS_FILE=google_vision_credentials.json
TAVILY_API_KEY=your-tavily-key
```

The pharmacist module also reads `MONGO_URI` / `MONGO_DB_NAME`; you may set those to the same values as `MONGODB_URI` / `MONGODB_DB_NAME`.

### 3. Seed users (first-time setup)

If the database has no accounts yet, run locally (outside Docker):

```bash
python scripts/seed_users.py
```

Default demo accounts:

| Role       | Email                     | Password      |
|------------|---------------------------|---------------|
| Admin      | admin@medical.local       | admin123      |
| Doctor     | doctor@medical.local      | doctor123     |
| Pharmacist | pharmacist@medical.local  | pharmacist123 |

## Docker Commands

Build the image:

```bash
docker build -t cloud-med-project .
```

Run the container (mount `.env` and Vision credentials from the host):

**Linux / macOS:**

```bash
docker run -p 5000:5000 \
  --env-file .env \
  -v "$(pwd)/google_vision_credentials.json:/app/google_vision_credentials.json:ro" \
  cloud-med-project
```

**Windows (PowerShell):**

```powershell
docker run -p 5000:5000 `
  --env-file .env `
  -v "${PWD}/google_vision_credentials.json:/app/google_vision_credentials.json:ro" `
  cloud-med-project
```

Open the application at [http://localhost:5000](http://localhost:5000).

## Accessing the Portals

After signing in, each role is redirected automatically:

| Portal     | URL after login        | Main features                                      |
|------------|------------------------|----------------------------------------------------|
| Login      | `/auth/login`          | Shared entry point for all roles                   |
| Admin      | `/admin/patients`      | Patient CRUD and system administration             |
| Doctor     | `/doctor/dashboard`    | Visits, prescriptions, PDF generation              |
| Pharmacist | `/pharmacist/search`   | Patient search, OCR, validation, dispensing        |

## Local Development (without Docker)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env
python scripts\seed_users.py
python run.py
```

## Project Structure

```text
app/                  Flask application (controllers, models, services, templates)
scripts/              Database seed and Google Drive auth utilities
tests/                Pytest test suite
test_prescriptions/   Sample prescription images for pharmacist OCR demos
```

## Architecture

See [PLANNING.md](PLANNING.md) for the full system design and development phases.

# Customer Management Application

This repository contains a customer management web application designed for AWS Lambda (Python) and a React frontend. Data is stored in Aurora PostgreSQL, accessed through Python CRUD wrappers that enforce validation, soft deletes, and audit logging.

## Architecture

- **Backend**: Python + SQLAlchemy models and CRUD services (`backend/app`).
- **Database**: Aurora PostgreSQL with UUID primary keys and `IsActive` soft delete flags on every table except `DataLog`.
- **Frontend**: React + Vite (`frontend`).
- **Authentication**: AWS IAM (expected to be configured via API Gateway/Lambda authorizers).
- **Data logging**: Every CRUD action writes to `DataLog` through the `CreateDataLog` helper.

## Database Schema

Models are defined in `backend/app/models.py` and match the required tables:
- Customers
- Address
- EmailAddress
- OptIn
- Province
- Country
- CountryLanguage
- Language
- Timezone
- Currency
- Invoice
- DataLog (no `IsActive`)
- DataAction

## CRUD Wrapper Functions

CRUD behavior is implemented in `backend/app/crud.py`:
- `read`
- `validate`
- `get_can_remove`
- `get_can_delete`
- `upsert`
- `remove`
- `delete`

All exceptions are caught and logged through `CreateDataLog`, with `IsSuccess = false` and the exception text captured in `DetailedLog`.

## Pre-seeded Data

Use the seeding helpers in `backend/app/seed_data.py` to load:
- ISO 639 languages from Wikipedia.
- TZ database timezones from Wikipedia.
- Sovereign states from Wikipedia.
- ISO 4217 currency codes from Wikipedia.
- Static `DataAction` records.

```bash
cd backend
python -m app.seed_data
```

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## DevOps Notes

- Use `docker-compose.yml` for local Postgres/Aurora-compatible testing.
- Deploy Lambda handlers in `backend/app/handlers.py` behind API Gateway with IAM auth.
- A GitHub Actions workflow is provided for linting and tests.

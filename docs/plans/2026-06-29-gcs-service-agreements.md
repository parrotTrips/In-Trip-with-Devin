# GCS Service Agreements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Store service agreements in a private GCP Cloud Storage bucket and expose them to travelers through temporary signed URLs.

**Architecture:** The spreadsheet/Supabase stores either a regular URL or a `gs://bucket/object` URI in `wetravel_trips.service_agreement_url`. The backend resolves `gs://` values into signed HTTPS URLs when returning `/me/trip`. The frontend remains unchanged because it already opens `tripInfo.service_agreement_url`.

**Tech Stack:** FastAPI, SQLAlchemy, Google Cloud Storage, pytest, GCP Cloud Storage, Google Sheets import pipeline.

---

### Task 1: Add Backend Resolver Tests

**Files:**
- Create: `backend/tests/services/test_service_agreement_service.py`
- Modify: `backend/tests/integration/test_trip_routes.py`

**Step 1: Test regular URLs**

Assert that a normal `https://...` service agreement URL is returned unchanged.

**Step 2: Test `gs://` parsing and signed URL generation**

Mock the signed URL function and assert that `GET /me/trip` returns the signed HTTPS URL instead of the raw `gs://` URI.

### Task 2: Implement Service Agreement Resolver

**Files:**
- Create: `backend/app/services/service_agreement_service.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/routers/trip.py`

**Step 1: Add dependency**

Add `google-cloud-storage` to backend dependencies.

**Step 2: Implement resolver**

Add:

- `parse_gcs_uri(uri)`
- `generate_signed_url_from_gcs_uri(uri, ttl_minutes=30)`
- `resolve_service_agreement_url(value)`

If value is empty or `None`, return `None`. If value is not `gs://`, return unchanged. If it is `gs://`, return a signed URL.

**Step 3: Integrate in `/me/trip`**

Before returning trip payload, call `resolve_service_agreement_url(row["service_agreement_url"])`.

### Task 3: Add Operational Documentation

**Files:**
- Create: `docs/service-agreements-gcs.md`

Document:

- bucket naming;
- folder convention;
- upload command;
- private bucket policy;
- how to store `gs://...` in the sheet;
- how to import into Supabase;
- how the app receives a signed URL.

### Task 4: Provision Test Asset

**Commands:**

```bash
gcloud config set project jogo-da-vida-497700
gcloud storage buckets create gs://parrot-trips-service-agreements-prod --location=southamerica-east1 --uniform-bucket-level-access
gcloud storage cp service_agreements/parrot_test_service_agreement.pdf gs://parrot-trips-service-agreements-prod/trips/TEST-2026-FULL/service-agreement.pdf
```

Then set `service_agreement_url` for `TEST-2026-FULL` to:

```text
gs://parrot-trips-service-agreements-prod/trips/TEST-2026-FULL/service-agreement.pdf
```

### Task 5: Verify

Run:

```bash
cd backend
poetry run pytest tests/services/test_service_agreement_service.py tests/integration/test_trip_routes.py -q
```

Then deploy backend and verify `/me/trip` returns a signed HTTPS URL for the test trip.


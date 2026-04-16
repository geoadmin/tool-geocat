# GeoNetwork Metadata Validation Tool

A Python script that connects to a GeoNetwork instance, validates metadata records against XSD and Schematron rules, and generates structured validation reports.

---

## Overview

`statistic-validation.py` authenticates against the GeoNetwork API, retrieves a list of metadata records, validates each one individually, and produces four output files summarising the results. It is designed to run against the **geocat.ch** environments (DEV, INT, PROD).

---

## Prerequisites

- **Python**: ArcGIS Pro environment recommended (`arcgispro-py3`)
- **Required packages**: `requests`, standard library (`csv`, `json`, `logging`, `os`, `datetime`)
- **Credentials**: a `.env` file (or environment variables) providing:
  ```
  GEOCAT_USERNAME=<your_username>
  GEOCAT_PASSWORD=<your_password>
  ```
- **Network**: corporate proxy is applied automatically if set in `config.py`

---

## Configuration

All settings are centralised in `config.py`:

| Setting | Description |
|---|---|
| `ENVIRONMENT` | Target environment: `'DEV'`, `'INT'`, or `'PROD'` |
| `API_URL` | Base URL of the GeoNetwork REST API (derived automatically from `ENVIRONMENT`) |
| `GEOCAT_USERNAME` / `GEOCAT_PASSWORD` | API credentials (loaded from environment variables) |
| `SERVER_SEARCH_QUERY` | Elasticsearch filter query (dict) used to select which records to validate. Default excludes harvested records and internal groups. |
| `SEARCH_PAGE_SIZE` | Number of records fetched per pagination page (default: `200`) |

---

## How to Run

```powershell
& "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" statistic-validation.py
```

The script reads its configuration from `config.py`; no command-line arguments are required.

---

## Input

UUIDs are fetched directly from the GeoNetwork Elasticsearch index using the filter defined in `SERVER_SEARCH_QUERY` in `config.py`. There is no CSV input — the server-side query is the only supported mode.

---

## Validation Method

The script calls `validate_all_individually()`, which performs **three API calls per record**:

1. `GET /api/0.1/records/{uuid}/editor` — open an editing session
2. `PUT /api/0.1/records/{uuid}/validate/internal` — trigger XSD + Schematron validation and collect errors
3. `DELETE /api/0.1/records/{uuid}/editor` — close the editing session (always executed, even on error)

This approach returns detailed, per-rule error messages. It takes roughly **4–5 seconds per record**.

---

## Output

Reports are written to a timestamped folder:

```
validation_reports_{ENVIRONMENT}_{YYYYMMDD_HHMMSS}/
```

| File | Description |
|---|---|
| `validation_errors.csv` | One row per record, with UUID, organisation, contact email, error count, and up to 10 error messages |
| `validation_statistics.json` | Full statistics as JSON: totals, error rate, most-common errors, error patterns |
| `validation_summary.txt` | Human-readable summary: global stats, top-15 errors, top-10 error patterns |
| `error_distribution.csv` | One row per distinct error message with its occurrence count |

Contact information (organisation name and email) is fetched from the GeoNetwork Elasticsearch index and added to `validation_errors.csv`.

---

## Known Limitations

- **HTTP 502 / 503 errors**: when the GeoNetwork server is under load, individual validation calls may fail. Affected records appear in the CSV with an `Editor HTTP 502` entry rather than real validation errors.
- **Execution time**: full validation of several thousand records can take **hours**. The script logs progress every 50 records.

---

## Helper Scripts

| Script | Purpose |
|---|---|
| `revalidate_errors.py` | Retries records that produced HTTP 502/503 errors in a previous run, merging results into existing reports |
| `extract_uuids_by_error.py` | Extracts UUIDs from a report filtered by a specific error message |
| `request_uuid_lucene.py` | Performs ad-hoc Lucene/Elasticsearch queries to retrieve UUIDs matching custom criteria |

# Multi-Source Candidate Data Transformer

A production-inspired multi-agent pipeline that ingests structured and unstructured candidate data, transforms it into a canonical candidate profile through normalization, entity resolution, conflict resolution, confidence scoring, provenance tracking, and configurable output generation.

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest
streamlit run app.py
```

On macOS/Linux, activate the virtual environment with:

```bash
source .venv/bin/activate
```

## Environment Variables

Create a local `.env` file from the example file:

```powershell
copy .env.example .env
```

Use placeholders like this. Do not commit real API keys.

```dotenv
LLM_PROVIDER=openrouter
LLM_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
LLM_API_KEY=your_llm_api_key_here

```

Notes:

- `LLM_API_KEY` is optional if you provide provider-specific keys.
- `.env` is ignored by Git and must stay local.

## Project Overview

This engine transforms candidate data from resumes, ATS exports, recruiter CSV files, and public profile URLs into canonical, explainable candidate records. It is designed for deterministic data transformation and grouping, with optional runtime JSON projection and validation output.

## Architecture Overview

```
[ Streamlit UI / Inputs ]
          |
          v
[ Source Detection ]
          |
          v
[ Extraction Adapters ]
   - resume PDF
   - ATS JSON
   - recruiter CSV
   - GitHub URL
   - LinkedIn URL
          |
          v
[ Raw Candidate Records ]
          |
          v
[ Duplicate Detection ]
          |
          v
[ Canonical Mapping ]
          |
          v
[ Normalization & Entity Resolution ]
          |
          v
[ Merge & Conflict Resolution ]
          |
          v
[ Confidence Scoring & Provenance ]
          |
          v
[ Projection (configurable) ]
          |
          v
[ Validation & Output ]
          |
          v
[ output/output.json ]
```

### Architecture explanation

- **Streamlit UI / Inputs**: user uploads files or enters URLs that become pipeline sources.
- **Source Detection**: the engine classifies each input as CSV, ATS JSON, resume PDF, GitHub, or LinkedIn.
- **Extraction Adapters**: each source type is converted into a raw candidate record with a common structure.
- **Raw Candidate Records**: all extracted records are collected and prepared for grouping.
- **Duplicate Detection**: records are grouped by identity signals such as email, phone, name, and social profiles.
- **Canonical Mapping**: raw source fields are mapped into a unified candidate schema.
- **Normalization & Entity Resolution**: field values are standardized and overlapping candidate details are resolved.
- **Merge & Conflict Resolution**: grouped records are merged into a single canonical profile per candidate, resolving conflicting values.
- **Confidence Scoring & Provenance**: each canonical profile earns confidence signals and provenance metadata for explainability.
- **Projection (optional)**: a runtime JSON config can reshape the output to include only requested fields.
- **Validation & Output**: final profiles are validated and written to `output/output.json`.

## Supported Input Sources

- Resume PDF
- ATS JSON object or array
- Recruiter CSV with one candidate per row
- GitHub profile URL
- LinkedIn profile URL

## Features

- Multi-source ingestion
- Multi-candidate aggregation
- Deterministic duplicate detection
- Canonical profile generation
- Provenance tracking
- Confidence scoring
- Runtime-configurable JSON projection
- Presentation validation warnings
- Streamlit review UI
- Partial failure handling for invalid individual inputs

## Implementation Screenshots

### 🏠 Streamlit UI

![Home Page](docs/screenshots/home.png)

---

### 📂 Upload Candidate Files

![Upload](docs/screenshots/upload-files.png)

---

### ⚙️ Processing Pipeline

![Processing](docs/screenshots/processing.png)

---

### 👤 Candidate Profile Cards

![Profile Cards](docs/screenshots/profile-card.png)

---

### 📄 Canonical Candidate JSON

![Candidate JSON](docs/screenshots/candidate-json.png)

---

### ⚙️ Configurable Output

![Config Output](docs/screenshots/config-output.png)

---

### 👨‍💼 Recruiter View

![Recruiter View](docs/screenshots/recruiter-output.png)

---

### 📈 Confidence Scoring

![Confidence](docs/screenshots/confidence.png)

---

### 🔍 Provenance Tracking

![Provenance](docs/screenshots/provenance.png)

## Repository Structure

```
candidate-transformer/
|-- app.py
|-- pipeline.py
|-- requirements.txt
|-- README.md
|-- .env.example
|-- config/
|-- output/
|-- projection/
|-- agents/
`-- tests/
```

## Installation

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Running The Application

```powershell
streamlit run app.py
```

The sidebar accepts:

- one recruiter CSV file
- one ATS JSON file
- multiple resume PDF files
- one GitHub profile URL
- one LinkedIn profile URL
- optional projection config JSON

## How to Use The Application

1. Start the app with `streamlit run app.py`.
2. Open the local Streamlit URL shown in the terminal.
3. Upload one or more resume PDF files.
4. Optionally upload a recruiter CSV file or ATS JSON export.
5. Paste a GitHub profile URL and/or a LinkedIn profile URL if available.
6. Upload an optional projection config JSON to control the final output fields.
7. Click `Process`.
8. Review the parsed candidate results in the UI and inspect `output/output.json` for the generated JSON.

Use the app to combine structured and unstructured candidate sources, then optionally filter the final output with a projection config.

## Running Quality Checks

```powershell
python -m pytest
```

## Sample Inputs

A cached sample input folder is included for reviewer convenience:

- `sample_inputs/github_cache.json` — deterministic GitHub profile cache data for offline review and repeatable testing.

This repo does not include a dedicated resume sample folder. Provide your own resume PDFs, ATS JSON, recruiter CSV, or public GitHub/LinkedIn URLs through the Streamlit UI.

## Output JSON Files

Generated pipeline artifacts are written to:

- `output/output.json`

## Regenerating Output Artifacts

Re-run the application or invoke `run_pipeline()` from `pipeline.py` with your input files and optional projection config. The default output path is `output/output.json`.

## Edge Cases Handled

- Multiple resume PDFs in one run
- Missing candidate fields processed without breaking the pipeline
- Invalid or malformed source inputs skipped gracefully
- Duplicate candidates grouped by deterministic identity signals
- Multiple source records merged into one canonical profile
- Projection config absent returns canonical output only
- Invalid projection config produces a clear failure path
- Conflicting field values resolved by the merge/conflict resolution layer

## Assumptions And Limitations

- Duplicate detection is deterministic and rule-based.
- The pipeline does not include OCR or DOCX parsing.
- GitHub extraction is based on public profile data only.
- LinkedIn URL handling is limited to a URL field and does not use an official LinkedIn API.
- There is no production authentication or persistent database storage.

## Submission Checklist

- Repository contains required source, config, projection logic, tests, and output handling.
- Local `.env`, logs, caches, and virtual environments are ignored.
- `requirements.txt` supports clone-and-run setup.
- README includes setup instructions, API key placeholders, and a clear runtime flow.

## Future Improvements

- Add a dedicated sample inputs folder for reviewer testing
- Add production-style GitHub profile caching
- Support additional resume formats such as DOCX
- Add richer UI summary cards and candidate switching
- Improve validation reporting and rule configuration

## Demo Video

Demo video link: TBD

# Aerial Tree Inspection Agent

A production AI agent built for Greenlight Ecology Ltd that 
automates the generation of bat survey aerial inspection 
Excel sheets. Surveyors submit tree and PRF (Potential Roost 
Feature) data via web form or audio upload — the agent 
validates the data and generates a pre-populated Excel file 
matching Greenlight Ecology's exact inspection template.

## What it does

Takes structured survey data for one or more trees and 
generates a populated .xlsm Excel file where:
- Each tree gets its own sheet (T13, T14 etc)
- All tree-level data is pre-filled (species, habitat, 
  weather conditions, W3W location)
- All PRF data is populated in the correct columns 
  (up to 10 PRFs per tree)
- PRF measurements, suitability ratings and inspection 
  notes all placed at exact cell positions
- Survey photos embedded in the PRF Photo rows
- Layout matches Sam's template exactly — ready to 
  review and sign off

## Two input methods

**Web form** — fill in tree and PRF details directly. 
All measurements and suitability ratings must come from 
the surveyor — the agent never calculates or estimates these.

**Audio upload** — record field notes on your phone and 
upload. Whisper transcribes the audio, GPT-4o-mini extracts 
text description fields only (feature type, inspection notes, 
conditions). Measurements and suitability ratings are never 
extracted from audio — the surveyor must enter these manually.

## Critical design decisions

- **No AI calculations** — PRF suitability, overall tree 
  suitability, and all measurements must come from the 
  surveyor. The AI only transcribes audio and extracts 
  descriptive text fields.
- **Pydantic v2 validation** — every survey submission is 
  validated before the Excel is built. Invalid suitability 
  ratings, out-of-range weather values, and missing required 
  fields are rejected with clear error messages.
- **Exact template matching** — the Excel output matches 
  Greenlight Ecology's template cell-by-cell, including 
  merged cells, formatting, colours and the dropdown 
  reference sheet.

## Stack

- **Backend:** FastAPI, Pydantic v2, OpenAI Whisper + 
  GPT-4o-mini, openpyxl, Pillow
- **Deployment:** Render
- **Client:** Greenlight Ecology Ltd

## API

- `POST /survey` — submit survey data as JSON, 
  returns survey_id and download_url
- `POST /audio` — upload audio file, returns 
  transcript and extracted text fields
- `POST /photos/{survey_id}/{tree_ref}/{prf_number}` 
  — upload PRF photo
- `GET /report/{survey_id}/download` — download 
  the generated .xlsm file
- `GET /health` — health check

API docs: https://aerial-inspection-agent.onrender.com/docs

## How to run locally

```bash
git clone https://github.com/Shab00/aerial-inspection-agent
cd aerial-inspection-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "OPENAI_API_KEY=your-key-here" > .env
uvicorn main:app --reload
```

Then open http://localhost:8000/docs to explore the API.

## What I would add next

- **Frontend** — GitHub Pages web form where Sam can fill 
  in survey data and record/upload audio field notes, then 
  download the generated Excel directly
- **Multi-survey batching** — submit multiple surveys at 
  once and get a single Excel with all trees
- **Re-inspection support** — submit re-inspection data 
  for existing surveys to populate the Re-inspection rows
- **Summary sheet** — auto-generate a summary sheet 
  listing all trees, their overall suitability, and PRF 
  counts

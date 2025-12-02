# Project Brief AI Assistant

A Python API that transforms project documents into business-friendly briefs and enables semantic search using Google's Gemini File Search API.

## Quick Start

### 1. Setup

```bash
# Clone and enter the project
cd project_brief_ai_assistant

# Create virtual environment
python -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_api_key_here
```

Get your API key from [Google AI Studio](https://aistudio.google.com/apikey).

### 3. Run the Server

```bash
uvicorn main:app --reload
```

Server runs at `http://127.0.0.1:8000`

API docs available at `http://127.0.0.1:8000/docs`

---

## API Endpoints

### POST /brief

Upload files and generate a project brief.

**Request:** `multipart/form-data` with one or more files

**Response:** JSON with project_id and brief

#### Example curl

```bash
# Single file
curl -X POST http://127.0.0.1:8000/brief \
  -F "files=@test_files/project_overview.md"

# Multiple files
curl -X POST http://127.0.0.1:8000/brief \
  -F "files=@test_files/project_overview.md" \
  -F "files=@test_files/functional_requirements.txt" \
  -F "files=@test_files/risk_and_concerns.txt" \
  -F "files=@test_files/skateholder_notes.md"
```

**Example Response:**

```json
{
  "project_id": "f65d3a2f-2fc7-4d03-bcca-66569d2949d0",
  "brief": "Talicada is a luxury Moroccan tour operator seeking to modernize their manual booking process. The MVP aims to centralize lead management, streamline itinerary creation with pricing, and reduce proposal turnaround time to under 24 hours. Key risks include the aggressive 6-8 week timeline, potential vendor response delays, and maintaining data privacy for high-end clients."
}
```

---

### POST /search

Semantic search over indexed project documents.

**Request:** `application/json` with:
- `project_id` (required): Project identifier from `/brief` response
- `query` (required): Your search question

**Response:** JSON with search results

#### Example curl

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"project_id": "f65d3a2f-2fc7-4d03-bcca-66569d2949d0", "query": "What are the main risks?"}'
```

**Example Response:**

```json
{
  "results": [
    {"file": "risk_and_concerns.txt", "snippet": "Slow vendor responses may delay proposals"},
    {"file": "project_overview.md", "snippet": "Timeline: 6-8 weeks for a usable pilot"}
  ]
}
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    main.py (FastAPI)                        │
│  ┌─────────────────┐         ┌─────────────────┐            │
│  │  POST /brief    │         │  POST /search   │            │
│  │  - File upload  │         │  - Query input  │            │
│  │  - Generate ID  │         │  - Resolve store│            │
│  └────────┬────────┘         └────────┬────────┘            │
│           │                           │                     │
│           │    project_stores dict    │                     │
│           │    (project_id → store)   │                     │
└───────────┼───────────────────────────┼─────────────────────┘
            │                           │
            ▼                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 gemini_client.py                            │
│  ┌──────────────────────────┐  ┌──────────────────────────┐ │
│  │ create_project_and_      │  │ semantic_search()        │ │
│  │ generate_brief()         │  │                          │ │
│  │                          │  │ - Query File Search Store│ │
│  │ - Create File Search     │  │ - Return structured JSON │ │
│  │   Store                  │  │                          │ │
│  │ - Upload files (temp)    │  └──────────────────────────┘ │
│  │ - Poll for indexing      │                               │
│  │ - Generate brief         │                               │
│  └──────────────────────────┘                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    prompts.py                               │
│  - PROMPT_BRIEF: Brief generation template                  │
│  - PROMPT_SEARCH: Semantic search template                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Google Gemini API                              │
│  - File Search Stores (RAG)                                 │
│  - gemini-2.5-flash model                                   │
└─────────────────────────────────────────────────────────────┘
```

### File Structure

```
project_brief_ai_assistant/
├── main.py              # FastAPI app, endpoints, request handling
├── gemini_client.py     # Gemini API integration, file upload, generation
├── prompts.py           # Prompt templates (PROMPT_BRIEF, PROMPT_SEARCH)
├── requirements.txt     # Python dependencies
├── .env                 # API key (not in repo)
├── README.md            # This file
└── test_files/          # Sample project documents
    ├── project_overview.md
    ├── functional_requirements.txt
    ├── risk_and_concerns.txt
    └── skateholder_notes.md
```

### Key Design Decisions

1. **Separation of Concerns**
   - `main.py`: HTTP layer, request/response handling
   - `gemini_client.py`: All Gemini API interactions
   - `prompts.py`: Prompt templates, easy to modify

2. **Temp File Strategy**
   - Gemini SDK expects file paths, not bytes
   - Files are written to temp, uploaded, then deleted
   - No persistent local storage needed

3. **In-Memory Store Mapping**
   - `project_stores` dict maps `project_id` → `store_name`
   - Simple for demo; use database for production

4. **Direct Upload to File Search Store**
   - Uses `upload_to_file_search_store()` (single step)
   - Simpler than upload + import approach

---

## Test Files

Sample documents are provided in `test_files/` for testing:

- `project_overview.md` - High-level project description
- `functional_requirements.txt` - MVP feature requirements
- `risk_and_concerns.txt` - Technical and business risks
- `skateholder_notes.md` - Stakeholder meeting notes

---

## Requirements

- Python 3.10+
- Google Gemini API key
- Dependencies in `requirements.txt`

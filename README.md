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

**Response:** JSON with project context, objectives, risks, and identifiers

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
  "project_context": "A travel CRM platform for a Morocco-based luxury travel agency...",
  "main_objectives": [
    "Centralize lead management and client tracking",
    "Build an itinerary creation tool with pricing",
    "Enable semantic search across all project data"
  ],
  "key_risks": [
    "Timeline pressure with 8-week MVP deadline",
    "Integration complexity with external booking systems",
    "Data migration from existing spreadsheets"
  ],
  "project_id": "f65d3a2f-2fc7-4d03-bcca-66569d2949d0",
  "store_name": "fileSearchStores/project-f65d3a2f-2fc7..."
}
```

---

### POST /search

Semantic search over indexed project documents.

**Request:** `application/json` with:
- `query` (required): Your search question
- `project_id` or `store_name`: Identifier from `/brief` response

**Response:** JSON with answer, relevant excerpts, and sources

#### Example curl

```bash
# Using project_id
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main technical risks?", "project_id": "f65d3a2f-2fc7-4d03-bcca-66569d2949d0"}'

# Using store_name directly
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What features are planned for the MVP?", "store_name": "fileSearchStores/project-f65d3a2f-2fc7..."}'
```

**Example Response:**

```json
{
  "answer": "The main technical risks include timeline pressure...",
  "relevant_excerpts": [
    "8-week timeline is aggressive for full MVP scope",
    "External API dependencies may cause delays"
  ],
  "sources": ["risk_and_concerns.txt", "project_overview.md"],
  "query": "What are the main technical risks?",
  "store_name": "fileSearchStores/project-f65d3a2f-2fc7..."
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

import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from gemini_client import create_project_and_generate_brief, semantic_search

app = FastAPI(title='AI Project Brief Assistant')

project_stores: dict[str, str] = {}


class SearchRequest(BaseModel):
    project_id: str
    query: str


@app.post('/brief')
async def create_brief(files: List[UploadFile] = File(...)):
    """
    Upload files and generate a project brief.

    - Accepts one or more files
    - Creates a file search store and indexes the files
    - Generates a friendly project brief using Gemini
    - Returns project_id for use with /search endpoint
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail='No files uploaded')

        file_datas = []
        for file in files:
            content = await file.read()
            file_datas.append(
                {
                    'name': file.filename,
                    'mime_type': (
                        file.content_type or 'application/octet-stream'
                    ),
                    'content': content,
                }
            )

        project_id = str(uuid.uuid4())
        print(f'Creating project {project_id} with {len(file_datas)} files...')

        brief = create_project_and_generate_brief(file_datas, project_id)

        # Store mapping for later searches
        project_stores[project_id] = brief['store_name']

        print(f'Brief generated for project {project_id}')
        return JSONResponse(content=brief)

    except Exception as e:
        import traceback

        print(f'Error: {e}\n{traceback.format_exc()}')
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/search')
async def search_project(request: SearchRequest):
    """
    Semantic search over indexed project documents.

    Content-Type: application/json

    Body:
    - project_id (required): Project identifier from /brief response
    - query (required): The search query
    """
    try:
        resolved_store = project_stores.get(request.project_id)
        if not resolved_store:
            raise HTTPException(
                status_code=404,
                detail=f"Project '{request.project_id}' not found."
            )

        if not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail='Query cannot be empty'
            )

        print(f"Searching store '{resolved_store}' for: {request.query}")
        result = semantic_search(resolved_store, request.query)

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        print(f'Error: {e}\n{traceback.format_exc()}')
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=8000)

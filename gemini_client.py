import os
import time
import json
import tempfile

from typing import List, Dict
from dotenv import load_dotenv

import google.genai as genai
from google.genai import types

from prompts import PROMPT_BRIEF, PROMPT_SEARCH

load_dotenv()

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))


def create_project_and_generate_brief(
    files_data: List[Dict],
    project_id: str
) -> Dict:
    """
    Create a file search store, upload files, and generate a project brief.

    Flow:
        create store ->
        temp file from bytes ->
        upload to store ->
        poll ->
        generate
    """
    # Create File Search Store
    store = client.file_search_stores.create(
        config={'display_name': f'project-{project_id}'}
    )
    print(f'Store created: {store.name}')

    # Upload + index each file
    for f in files_data:
        name = f['name']
        content = f['content']

        # Skip empty files
        if not content:
            print(f'Skipping {name} (empty file)')
            continue

        print(f'Processing {name} ({len(content)} bytes)')

        # Write bytes to a temp file because SDK expects file path
        suffix = os.path.splitext(name)[1] or '.txt'
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            # Upload directly to file search store
            operation = client.file_search_stores.upload_to_file_search_store(
                file=tmp_file_path,
                file_search_store_name=store.name,
                config={'display_name': name},
            )

            # Poll for completion
            while not operation.done:
                time.sleep(3)
                operation = client.operations.get(operation)

            if operation.error:
                raise RuntimeError(
                    f'Upload/indexing error for {name}: {operation.error}'
                )

            print(f'Indexed {name}')
        finally:
            # Clean up temp file
            os.unlink(tmp_file_path)

    # Generate brief using file search toool
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=PROMPT_BRIEF,
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(
                    file_search=types.FileSearch(
                        file_search_store_names=[store.name]
                    )
                )
            ]
        ),
    )

    # Extract and clean json response
    text = (
        response.text.strip()
        .removeprefix('```json')
        .removesuffix('```')
        .strip()
    )
    result = json.loads(text)

    return {
        'project_id': project_id,
        'brief': result.get('brief', ''),
        'store_name': store.name
    }


def semantic_search(store_name: str, query: str) -> Dict:
    """
    Perform semantic search over indexed files in a File Search Store.

    Uses Gemini with the File Search tool to
    answer the query based on indexed documents.
    """
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=PROMPT_SEARCH.format(query=query),
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(
                    file_search=types.FileSearch(
                        file_search_store_names=[store_name]
                    )
                )
            ]
        ),
    )

    # Extract and clean json response
    text = (
        response.text.strip()
        .removeprefix('```json')
        .removesuffix('```')
        .strip()
    )
    result = json.loads(text)

    return result

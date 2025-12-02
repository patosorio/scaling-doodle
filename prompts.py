PROMPT_BRIEF = '''
You are an expert business analyst.
Using ONLY the uploaded project documents,
create a concise, client-friendly project brief.

Return ONLY valid JSON in this exact format (no extra text, no markdown):

{
    "brief": "A single paragraph summarizing the project context, main objectives, and key risks in non-technical terms."
}

Keep it professional, concise, and under 150 words.
'''

PROMPT_SEARCH = '''
You are a helpful assistant. Using ONLY the indexed project documents,
answer the following query with relevant excerpts.

Query: {query}

Return ONLY valid JSON in this exact format (no extra text, no markdown):
{{
    "results": [
        {{"file": "filename", "snippet": "short relevant excerpt"}},
        {{"file": "filename", "snippet": "short relevant excerpt"}}
    ]
}}

Keep snippets concise and directly relevant to the query.
'''

import os

from dotenv import load_dotenv

from google import genai


load_dotenv()


client = genai.Client(
    api_key=os.getenv(
        "GEMINI_API_KEY"
    )
)


def generate_migration(
    code: str,
    migration_guidance: str
):

    prompt = f"""
You are an expert software migration assistant.

Migrate the following Python code according to
the provided migration documentation.

IMPORTANT:
- Preserve the original behavior of the code.
- Only make changes required for the migration.
- Return only the migrated Python code.
- Do not add explanations.
- Do not use markdown code fences.

ORIGINAL CODE:

{code}


MIGRATION DOCUMENTATION:

{migration_guidance}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    return response.text
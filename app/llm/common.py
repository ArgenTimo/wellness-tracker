from openai import OpenAI
from app.core.config import settings


client = OpenAI(api_key=settings.OPENAI_API_KEY)


def create_llm_query_func(model):
    def llm_query(messages: list[dict]) -> str:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return resp.choices[0].message.content

    return llm_query


def run_llm_security_query(messages: list[dict]):
    tools = [
        {
            "type": "file_search",
            "vector_store_ids": settings.SECURITY_VECTOR_STORE_IDS
        }
    ]
    response = client.responses.create(
        model=settings.OPENAI_BASE_MODEL,
        tools=tools,
        input=messages
    )

    return response.output_text


request_to_model_4o = create_llm_query_func(settings.OPENAI_BASE_MODEL)

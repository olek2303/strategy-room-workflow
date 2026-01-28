import os
from llama_index.llms.openai_like import OpenAILike
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

class BaseLLM(OpenAILike):
    """Base LLM class that extends OpenAILike functionality."""

    def __init__(self, model_name: str, **kwargs):
        api_key = os.getenv("API_KEY")
        api_base = os.getenv("API_BASE_URL")

        if api_key and api_base:
            kwargs["api_key"] = api_key
            kwargs["api_base"] = api_base
        else:
            raise ValueError("no api key or api base found in environment variables")

        kwargs['model'] = model_name
        kwargs['is_chat_model'] = True  # important for strategy room chatting

        super().__init__(**kwargs)
        print('connected to api base url')

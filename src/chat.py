import os
import warnings
from openai import OpenAI
from dotenv import load_dotenv
from dataclasses import dataclass
from openai.types.chat.chat_completion import ChatCompletion


@dataclass
class Response:
    @dataclass
    class Usage:
        prompt: int
        completion: int

    content: str
    usage: Usage


class Role:
    model: str
    prompt: str

    ALLOWED_GEN_PARAM = [
        "n",
        "stop",
        "top_p",
        "max_tokens",
        "temperature",
        "frequency_penalty",
        "max_completion_tokens",
    ]

    def __init__(self, prompt):
        is_env_loaded = load_dotenv()

        api_key = os.getenv("API_KEY", "")
        base_url = os.getenv("API_BASE_URL", None) or None
        model = os.getenv("MODEL", None) or None
        if not is_env_loaded or not api_key:
            raise ValueError("Please provide environment variables in .env file")
        if not model:
            warnings.warn("Model not specified, using GPT-4o-mini by default")
            model = "gpt_4o_mini"

        self.client = OpenAI(api_key=api_key, base_url=base_url)

        self.prompt = prompt
        self.model = model

    def chat(self, query: str, **generation_params) -> Response:
        for param in generation_params.keys():
            if param not in self.ALLOWED_GEN_PARAM:
                raise ValueError(f"Generation param {param} not implemented yet")

        response: ChatCompletion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": query},
            ],
            model=self.model,
            **generation_params,
        )

        return Response(
            response.choices[0].message.content,
            usage=Response.Usage(
                response.usage.prompt_tokens, response.usage.completion_tokens
            ),
        )

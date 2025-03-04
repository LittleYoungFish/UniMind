from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion


class Chat:
    def __init__(self, api_key: str, base_url: str = None):
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat(self, prompt: str, query: str, model: str, **generation_params):
        response: ChatCompletion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query},
            ],
            model=model,
            **generation_params
        )

        return response.choices[0].message.content

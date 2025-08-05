from codebase_to_llm.application.ports import LLMAdapterPort
from openai import OpenAI

from codebase_to_llm.domain.api_key import ApiKey
from codebase_to_llm.domain.result import Err, Ok, Result


class OpenAILLMAdapter(LLMAdapterPort):
    def generate_response(
        self, prompt: str, model: str, api_key: ApiKey
    ) -> Result[str, str]:
        print(f"Generating response for {model} with API key {api_key}")
        print(f"Prompt: {prompt}")
        print(f"Model: {model}")

        api_key_value = api_key.api_key_value().value()
        print("--------------------------------")

        client = OpenAI(api_key=api_key_value)
        try:
            response = client.responses.create(model=model, input=prompt)

            return Ok(response.output_text)
        except Exception as e:
            print(f"Error generating response: {e}")
            return Err(f"Error generating response: {e}")

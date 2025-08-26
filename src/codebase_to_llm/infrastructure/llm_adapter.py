from typing import Any
from codebase_to_llm.application.ports import LLMAdapterPort
from openai import OpenAI, Stream
from anthropic import Anthropic
from pydantic import BaseModel

from codebase_to_llm.domain.api_key import ApiKey
from codebase_to_llm.domain.result import Err, Ok, Result


class OpenAILLMAdapter(LLMAdapterPort):
    def _is_anthropic_model(self, model: str) -> bool:
        """Check if the model is an Anthropic Claude model."""
        return model.startswith("claude-") or "claude" in model.lower()

    def _is_openai_model(self, model: str) -> bool:
        """Check if the model is an OpenAI model."""
        return (
            model.startswith("gpt-")
            or model.startswith("o1-")
            or "gpt" in model.lower()
        )

    def generate_response(
        self,
        prompt: str,
        model: str,
        api_key: ApiKey,
        previous_response_id: str | None = None,
    ) -> Result[Stream[Any], str]:
        print(f"Generating response for {model} with API key {api_key}")
        print(f"Prompt: {prompt}")
        print(f"Model: {model}")

        api_key_value = api_key.api_key_value().value()
        print("--------------------------------")

        if self._is_anthropic_model(model):
            return Err("Streaming not implemented for Anthropic models")

        client = OpenAI(api_key=api_key_value)
        try:
            response: Stream = client.responses.create(
                model=model,
                input=prompt,
                stream=True,
                previous_response_id=previous_response_id,
            )

            return Ok(response)
        except Exception as e:
            print(f"Error generating response: {e}")
            return Err(f"Error generating response: {e}")

    def structured_output(
        self,
        prompt: str,
        model: str,
        api_key: ApiKey,
        response_format: type[BaseModel],
    ) -> Result[BaseModel, str]:
        api_key_value = api_key.api_key_value().value()

        if self._is_anthropic_model(model):
            return self._anthropic_structured_output(
                prompt, model, api_key_value, response_format
            )
        elif self._is_openai_model(model):
            return self._openai_structured_output(
                prompt, model, api_key_value, response_format
            )
        else:
            return Err(f"Unsupported model: {model}")

    def _openai_structured_output(
        self,
        prompt: str,
        model: str,
        api_key_value: str,
        response_format: type[BaseModel],
    ) -> Result[BaseModel, str]:
        client = OpenAI(api_key=api_key_value)
        try:
            response = client.beta.chat.completions.parse(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Extract the requested information from the provided content.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format=response_format,
            )
            parsed = response.choices[0].message.parsed
            if parsed is None:
                return Err("Failed to parse structured output")
            return Ok(parsed)
        except Exception as e:
            return Err(f"Error generating structured output: {e}")

    def _anthropic_structured_output(
        self,
        prompt: str,
        model: str,
        api_key_value: str,
        response_format: type[BaseModel],
    ) -> Result[BaseModel, str]:
        client = Anthropic(api_key=api_key_value)

        # Get the JSON schema from the Pydantic model
        schema = response_format.model_json_schema()

        # Create a tool definition for structured output
        from anthropic.types import ToolParam, ToolChoiceToolParam, MessageParam

        tool_definition: ToolParam = {
            "name": "record_structured_output",
            "description": f"Record the extracted information using the specified schema for {response_format.__name__}",
            "input_schema": schema,
        }

        tool_choice: ToolChoiceToolParam = {
            "type": "tool",
            "name": "record_structured_output",
        }

        message: MessageParam = {
            "role": "user",
            "content": prompt,
        }

        try:
            response = client.messages.create(
                model=model,
                max_tokens=8192,
                tools=[tool_definition],
                tool_choice=tool_choice,
                messages=[message],
            )

            # Extract the tool use from the response
            if response.content:
                for block in response.content:
                    if hasattr(block, "type") and block.type == "tool_use":
                        if block.name == "record_structured_output":
                            try:
                                # The input contains the structured data
                                parsed = response_format.model_validate(block.input)
                                return Ok(parsed)
                            except ValueError as parse_error:
                                return Err(
                                    f"Failed to validate structured output: {parse_error}. Input: {block.input}"
                                )

            return Err("No tool use found in response")

        except Exception as e:
            return Err(f"Error generating structured output with Anthropic: {e}")

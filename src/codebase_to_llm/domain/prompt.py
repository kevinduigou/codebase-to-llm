from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing_extensions import final
import re

from .value_object import ValueObject
from .result import Result, Ok, Err


@dataclass(frozen=True)
class PromptHasBeenModifiedEvent:
    """Event indicating that the prompt has been modified."""

    new_prompt: Prompt


@dataclass(frozen=True)
class FileAddedAsPromptVariableEvent:
    """Event indicating that a file has been added as a prompt variable."""

    file_path: str
    variable_key: str
    content: str


@final
@dataclass(frozen=True)
class PromptVariable(ValueObject):
    """Value object representing a user prompt variable."""

    key: str
    content: str


def set_prompt_variable(prompt: Prompt, variable_key: str, content: str) -> Prompt:
    """Set a prompt variable."""
    new_variables = [var for var in prompt.get_variables() if var.key != variable_key]
    new_variables.append(PromptVariable(variable_key, content))
    return Prompt(prompt.get_content(), new_variables)


@final
@dataclass(frozen=True)
class Prompt(ValueObject):
    """Value object representing a user prompt."""

    _content: str
    _variables: list[PromptVariable]

    @staticmethod
    def try_create(
        content: str, variables: list[PromptVariable] = []
    ) -> Result["Prompt", str]:
        if not content or not content.strip():
            return Err("Prompt cannot be empty")

        keys = sorted(list(set(re.findall(r"\{\{(.*?)\}\}", content))))
        new_variables = []
        for key_from_prompt in keys:
            for variable in variables:
                if variable.key == key_from_prompt:
                    # Use Previous Variable
                    new_variables.append(variable)
                    content = content.replace(
                        f"{{{{{key_from_prompt}}}}}", variable.content
                    )
                    break
            else:
                # runs only if no break occurred in the for loop above,
                # i.e., no variable with a matching key was found.
                # Create a new variable with empty content
                new_variables.append(PromptVariable(key_from_prompt, ""))

        return Ok(Prompt(content, new_variables))

    def get_variables(self) -> list[PromptVariable]:
        return deepcopy(self._variables)

    def get_content(self) -> str:
        return self._content

    def full_text(self) -> Result[str, str]:
        variables_keys_with_empty_content = [
            var.key for var in self._variables if var.content == ""
        ]

        if len(variables_keys_with_empty_content) > 0:
            return Err(
                f"Prompt contains varable not set {variables_keys_with_empty_content}"
            )

        content = self._content
        # Replace variable within {{}} with the variable content
        for variable in self._variables:
            content = content.replace(f"{{{{{variable.key}}}}}", variable.content)

        return Ok(content)

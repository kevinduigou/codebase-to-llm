from __future__ import annotations

import json
from pathlib import Path

from codebase_to_llm.application.ports import ApiKeyRepositoryPort
from codebase_to_llm.domain.api_key import (
    ApiKeys,
    ApiKey,
    ApiKeyId,
)
from codebase_to_llm.domain.result import Result, Ok, Err


class FileSystemApiKeyRepository(ApiKeyRepositoryPort):
    """File system implementation of API key repository using encrypted JSON storage."""

    __slots__ = ("_file_path",)
    _file_path: Path

    def __init__(self, file_path: Path | None = None):
        if file_path is None:
            # Default to user's home directory
            self._file_path = Path.home() / ".dcc_api_keys.json"
        else:
            self._file_path = file_path

    def load_api_keys(self) -> Result[ApiKeys, str]:
        """Loads API keys from the file system."""
        try:
            if not self._file_path.exists():
                # Return empty collection if file doesn't exist
                return Ok(ApiKeys(()))

            with open(self._file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate JSON structure
            if not isinstance(data, dict) or "api_keys" not in data:
                return Err("Invalid API keys file format")

            api_keys_data = data["api_keys"]
            if not isinstance(api_keys_data, list):
                return Err("Invalid API keys data format")

            # Convert JSON data to domain objects
            api_keys_list = []
            for key_data in api_keys_data:
                if not isinstance(key_data, dict):
                    return Err("Invalid API key data format")

                required_fields = ["id", "url_provider", "api_key_value"]
                for field in required_fields:
                    if field not in key_data:
                        return Err(f"Missing required field: {field}")

                api_key_result = ApiKey.try_create(
                    key_data["id"], key_data["url_provider"], key_data["api_key_value"]
                )

                if api_key_result.is_err():
                    return Err(f"Invalid API key in file: {api_key_result.err()}")

                api_keys_list.append(api_key_result.ok())

            # Create ApiKeys collection
            api_keys_result = ApiKeys.try_create(tuple(api_keys_list))
            if api_keys_result.is_err():
                return Err(f"Invalid API keys collection: {api_keys_result.err()}")

            return Ok(api_keys_result.ok())

        except json.JSONDecodeError as e:
            return Err(f"Failed to parse API keys file: {str(e)}")
        except OSError as e:
            return Err(f"Failed to read API keys file: {str(e)}")
        except Exception as e:
            return Err(f"Unexpected error loading API keys: {str(e)}")

    def save_api_keys(self, api_keys: ApiKeys) -> Result[None, str]:
        """Saves API keys to the file system."""
        try:
            # Convert domain objects to JSON data
            api_keys_data = []
            for api_key in api_keys.api_keys():
                key_data = {
                    "id": api_key.id().value(),
                    "url_provider": api_key.url_provider().value(),
                    "api_key_value": api_key.api_key_value().value(),
                }
                api_keys_data.append(key_data)

            data = {"api_keys": api_keys_data, "version": "1.0"}

            # Ensure directory exists
            self._file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to temporary file first, then rename for atomic operation
            temp_file = self._file_path.with_suffix(".tmp")

            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_file.replace(self._file_path)

            return Ok(None)

        except OSError as e:
            return Err(f"Failed to write API keys file: {str(e)}")
        except Exception as e:
            return Err(f"Unexpected error saving API keys: {str(e)}")

    def find_api_key_by_id(self, api_key_id: ApiKeyId) -> Result[ApiKey, str]:
        """Finds an API key by its ID."""
        api_keys_result = self.load_api_keys()
        if api_keys_result.is_err():
            return Err(api_keys_result.err())

        api_keys = api_keys_result.ok()
        return api_keys.find_by_id(api_key_id)

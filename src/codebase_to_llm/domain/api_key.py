from __future__ import annotations

from typing import Tuple
from typing_extensions import final

from codebase_to_llm.domain.value_object import ValueObject
from codebase_to_llm.domain.result import Result, Ok, Err


@final
class ApiKeyId(ValueObject):
    """Unique identifier for an API key."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def try_create(value: str) -> Result["ApiKeyId", str]:
        trimmed_value = value.strip()
        if not trimmed_value:
            return Err("API Key ID cannot be empty.")
        if len(trimmed_value) > 100:
            return Err("API Key ID cannot exceed 100 characters.")
        return Ok(ApiKeyId(trimmed_value))

    def __init__(self, value: str) -> None:
        self._value = value

    def value(self) -> str:
        return self._value


@final
class UrlProvider(ValueObject):
    """URL of the API provider (e.g., https://api.openai.com)."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def try_create(value: str) -> Result["UrlProvider", str]:
        trimmed_value = value.strip()
        if not trimmed_value:
            return Err("URL Provider cannot be empty.")

        # Basic URL validation
        if not (
            trimmed_value.startswith("http://") or trimmed_value.startswith("https://")
        ):
            return Err("URL Provider must start with http:// or https://")

        if len(trimmed_value) > 500:
            return Err("URL Provider cannot exceed 500 characters.")

        return Ok(UrlProvider(trimmed_value))

    def __init__(self, value: str) -> None:
        self._value = value

    def value(self) -> str:
        return self._value


@final
class ApiKeyValue(ValueObject):
    """The actual API key value (sensitive data)."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def try_create(value: str) -> Result["ApiKeyValue", str]:
        trimmed_value = value.strip()
        if not trimmed_value:
            return Err("API Key value cannot be empty.")
        if len(trimmed_value) < 10:
            return Err("API Key value must be at least 10 characters.")
        if len(trimmed_value) > 1000:
            return Err("API Key value cannot exceed 1000 characters.")
        return Ok(ApiKeyValue(trimmed_value))

    def __init__(self, value: str) -> None:
        self._value = value

    def value(self) -> str:
        return self._value

    def masked_value(self) -> str:
        """Returns a masked version for display purposes."""
        if len(self._value) <= 10:
            return "*" * len(self._value)
        return self._value[:4] + "*" * (len(self._value) - 8) + self._value[-4:]


@final
class ApiKey(ValueObject):
    """An API key with its provider URL and value."""

    __slots__ = ("_id", "_url_provider", "_api_key_value")
    _id: ApiKeyId
    _url_provider: UrlProvider
    _api_key_value: ApiKeyValue

    @staticmethod
    def try_create(
        id_value: str, url_provider: str, api_key_value: str
    ) -> Result["ApiKey", str]:
        id_result = ApiKeyId.try_create(id_value)
        if id_result.is_err():
            return Err(f"Invalid API Key ID: {id_result.err()}")

        url_result = UrlProvider.try_create(url_provider)
        if url_result.is_err():
            return Err(f"Invalid URL Provider: {url_result.err()}")

        key_result = ApiKeyValue.try_create(api_key_value)
        if key_result.is_err():
            return Err(f"Invalid API Key Value: {key_result.err()}")

        id_obj = id_result.ok()
        url_obj = url_result.ok()
        key_obj = key_result.ok()
        if id_obj is None or url_obj is None or key_obj is None:
            return Err("Unexpected error: one of the value objects is None")
        return Ok(ApiKey(id_obj, url_obj, key_obj))

    def __init__(
        self, id: ApiKeyId, url_provider: UrlProvider, api_key_value: ApiKeyValue
    ) -> None:
        self._id = id
        self._url_provider = url_provider
        self._api_key_value = api_key_value

    def id(self) -> ApiKeyId:
        return self._id

    def url_provider(self) -> UrlProvider:
        return self._url_provider

    def api_key_value(self) -> ApiKeyValue:
        return self._api_key_value

    def update_url_provider(self, new_url_provider: UrlProvider) -> "ApiKey":
        """Returns a new ApiKey with updated URL provider."""
        return ApiKey(self._id, new_url_provider, self._api_key_value)

    def update_api_key_value(self, new_api_key_value: ApiKeyValue) -> "ApiKey":
        """Returns a new ApiKey with updated API key value."""
        return ApiKey(self._id, self._url_provider, new_api_key_value)


@final
class ApiKeys(ValueObject):
    """Immutable collection of API keys."""

    __slots__ = ("_api_keys",)
    _api_keys: Tuple[ApiKey, ...]

    @staticmethod
    def try_create(api_keys: Tuple[ApiKey, ...]) -> Result["ApiKeys", str]:
        # Check for duplicate IDs
        ids = [key.id().value() for key in api_keys]
        if len(ids) != len(set(ids)):
            return Err("Duplicate API Key IDs are not allowed.")

        return Ok(ApiKeys(api_keys))

    def __init__(self, api_keys: Tuple[ApiKey, ...]) -> None:
        self._api_keys = api_keys

    def api_keys(self) -> Tuple[ApiKey, ...]:
        return self._api_keys

    def add_api_key(self, api_key: ApiKey) -> Result["ApiKeys", str]:
        """Returns a new ApiKeys collection with the added API key."""
        # Check if ID already exists
        for existing_key in self._api_keys:
            if existing_key.id().value() == api_key.id().value():
                return Err(f'API Key with ID "{api_key.id().value()}" already exists.')

        new_keys = self._api_keys + (api_key,)
        return Ok(ApiKeys(new_keys))

    def remove_api_key(self, api_key_id: ApiKeyId) -> Result["ApiKeys", str]:
        """Returns a new ApiKeys collection with the API key removed."""
        new_keys = tuple(
            key for key in self._api_keys if key.id().value() != api_key_id.value()
        )

        if len(new_keys) == len(self._api_keys):
            return Err(f'API Key with ID "{api_key_id.value()}" not found.')

        return Ok(ApiKeys(new_keys))

    def update_api_key(self, updated_api_key: ApiKey) -> Result["ApiKeys", str]:
        """Returns a new ApiKeys collection with the API key updated."""
        new_keys = []
        found = False

        for key in self._api_keys:
            if key.id().value() == updated_api_key.id().value():
                new_keys.append(updated_api_key)
                found = True
            else:
                new_keys.append(key)

        if not found:
            return Err(f'API Key with ID "{updated_api_key.id().value()}" not found.')

        return Ok(ApiKeys(tuple(new_keys)))

    def find_by_id(self, api_key_id: ApiKeyId) -> Result[ApiKey, str]:
        """Finds an API key by its ID."""
        for key in self._api_keys:
            if key.id().value() == api_key_id.value():
                return Ok(key)

        return Err(f'API Key with ID "{api_key_id.value()}" not found.')

    def find_by_url_provider(self, provider_name: str) -> Result[ApiKey, str]:
        """Finds an API key by its URL provider."""
        for key in self._api_keys:
            if key.url_provider().value() == provider_name:
                return Ok(key)

        return Err(f'API Key with provider "{provider_name}" not found.')

    def is_empty(self) -> bool:
        return len(self._api_keys) == 0

    def count(self) -> int:
        return len(self._api_keys)


# Domain Events
@final
class ApiKeyAddedEvent(ValueObject):
    """Event raised when an API key is added."""

    __slots__ = ("_api_key",)
    _api_key: ApiKey

    def __init__(self, api_key: ApiKey) -> None:
        self._api_key = api_key

    def api_key(self) -> ApiKey:
        return self._api_key


@final
class ApiKeyRemovedEvent(ValueObject):
    """Event raised when an API key is removed."""

    __slots__ = ("_api_key_id",)
    _api_key_id: ApiKeyId

    def __init__(self, api_key_id: ApiKeyId) -> None:
        self._api_key_id = api_key_id

    def api_key_id(self) -> ApiKeyId:
        return self._api_key_id


@final
class ApiKeyUpdatedEvent(ValueObject):
    """Event raised when an API key is updated."""

    __slots__ = ("_api_key",)
    _api_key: ApiKey

    def __init__(self, api_key: ApiKey) -> None:
        self._api_key = api_key

    def api_key(self) -> ApiKey:
        return self._api_key

from __future__ import annotations

from typing import Tuple
from typing_extensions import final

from codebase_to_llm.domain.value_object import ValueObject
from codebase_to_llm.domain.result import Result, Ok, Err
from codebase_to_llm.domain.api_key import ApiKeyId
from codebase_to_llm.domain.user import UserId


@final
class ModelId(ValueObject):
    """Unique identifier for a model."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def try_create(value: str) -> Result["ModelId", str]:
        trimmed_value = value.strip()
        if not trimmed_value:
            return Err("Model ID cannot be empty.")
        if len(trimmed_value) > 100:
            return Err("Model ID cannot exceed 100 characters.")
        return Ok(ModelId(trimmed_value))

    def __init__(self, value: str) -> None:
        self._value = value

    def value(self) -> str:
        return self._value


@final
class ModelName(ValueObject):
    """Name of the underlying LLM model."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def try_create(value: str) -> Result["ModelName", str]:
        trimmed_value = value.strip()
        if not trimmed_value:
            return Err("Model name cannot be empty.")
        if len(trimmed_value) > 200:
            return Err("Model name cannot exceed 200 characters.")
        return Ok(ModelName(trimmed_value))

    def __init__(self, value: str) -> None:
        self._value = value

    def value(self) -> str:
        return self._value


@final
class Model(ValueObject):
    """A model linked to an API key and owned by a user."""

    __slots__ = ("_id", "_user_id", "_name", "_api_key_id")
    _id: ModelId
    _user_id: UserId
    _name: ModelName
    _api_key_id: ApiKeyId

    @staticmethod
    def try_create(
        id_value: str,
        user_id_value: str,
        name: str,
        api_key_id_value: str,
    ) -> Result["Model", str]:
        id_result = ModelId.try_create(id_value)
        if id_result.is_err():
            return Err(f"Invalid model ID: {id_result.err()}")

        user_id_result = UserId.try_create(user_id_value)
        if user_id_result.is_err():
            return Err(f"Invalid user ID: {user_id_result.err()}")

        name_result = ModelName.try_create(name)
        if name_result.is_err():
            return Err(f"Invalid model name: {name_result.err()}")

        api_key_id_result = ApiKeyId.try_create(api_key_id_value)
        if api_key_id_result.is_err():
            return Err(f"Invalid API key ID: {api_key_id_result.err()}")

        id_obj = id_result.ok()
        user_id_obj = user_id_result.ok()
        name_obj = name_result.ok()
        api_key_id_obj = api_key_id_result.ok()
        if (
            id_obj is None
            or user_id_obj is None
            or name_obj is None
            or api_key_id_obj is None
        ):
            return Err("Invalid model data.")

        return Ok(Model(id_obj, user_id_obj, name_obj, api_key_id_obj))

    def __init__(
        self,
        id_: ModelId,
        user_id: UserId,
        name: ModelName,
        api_key_id: ApiKeyId,
    ) -> None:
        self._id = id_
        self._user_id = user_id
        self._name = name
        self._api_key_id = api_key_id

    def id(self) -> ModelId:
        return self._id

    def user_id(self) -> UserId:
        return self._user_id

    def name(self) -> ModelName:
        return self._name

    def api_key_id(self) -> ApiKeyId:
        return self._api_key_id


@final
class Models(ValueObject):
    """Immutable collection of models."""

    __slots__ = ("_models",)
    _models: Tuple[Model, ...]

    @staticmethod
    def try_create(models: Tuple[Model, ...]) -> Result["Models", str]:
        ids = [model.id().value() for model in models]
        if len(ids) != len(set(ids)):
            return Err("Duplicate model IDs are not allowed.")
        return Ok(Models(models))

    def __init__(self, models: Tuple[Model, ...]) -> None:
        self._models = models

    def models(self) -> Tuple[Model, ...]:
        return self._models

    def add_model(self, model: Model) -> Result["Models", str]:
        for existing in self._models:
            if existing.id().value() == model.id().value():
                return Err(f'Model with ID "{model.id().value()}" already exists.')
        new_models = self._models + (model,)
        return Ok(Models(new_models))

    def remove_model(self, model_id: ModelId) -> Result["Models", str]:
        new_models = tuple(
            model for model in self._models if model.id().value() != model_id.value()
        )
        if len(new_models) == len(self._models):
            return Err(f'Model with ID "{model_id.value()}" not found.')
        return Ok(Models(new_models))

    def update_model(self, updated_model: Model) -> Result["Models", str]:
        new_models: list[Model] = []
        found = False
        for model in self._models:
            if model.id().value() == updated_model.id().value():
                new_models.append(updated_model)
                found = True
            else:
                new_models.append(model)
        if not found:
            return Err(f'Model with ID "{updated_model.id().value()}" not found.')
        return Ok(Models(tuple(new_models)))

    def find_by_id(self, model_id: ModelId) -> Result[Model, str]:
        for model in self._models:
            if model.id().value() == model_id.value():
                return Ok(model)
        return Err(f'Model with ID "{model_id.value()}" not found.')

    def is_empty(self) -> bool:
        return len(self._models) == 0

    def count(self) -> int:
        return len(self._models)


@final
class ModelAddedEvent(ValueObject):
    """Event raised when a model is added."""

    __slots__ = ("_model",)
    _model: Model

    def __init__(self, model: Model) -> None:
        self._model = model

    def model(self) -> Model:
        return self._model


@final
class ModelRemovedEvent(ValueObject):
    """Event raised when a model is removed."""

    __slots__ = ("_model_id",)
    _model_id: ModelId

    def __init__(self, model_id: ModelId) -> None:
        self._model_id = model_id

    def model_id(self) -> ModelId:
        return self._model_id


@final
class ModelUpdatedEvent(ValueObject):
    """Event raised when a model is updated."""

    __slots__ = ("_model",)
    _model: Model

    def __init__(self, model: Model) -> None:
        self._model = model

    def model(self) -> Model:
        return self._model

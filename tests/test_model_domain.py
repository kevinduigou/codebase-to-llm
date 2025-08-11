import pytest

from codebase_to_llm.domain.model import (
    ModelId,
    ModelName,
    Model,
    Models,
    ModelAddedEvent,
    ModelRemovedEvent,
    ModelUpdatedEvent,
)

USER_ID = "user-1"


class TestModelId:
    def test_try_create_valid_id(self):
        result = ModelId.try_create("model-1")
        assert result.is_ok()
        model_id = result.ok()
        assert model_id is not None
        assert model_id.value() == "model-1"

    def test_try_create_empty_id_fails(self):
        result = ModelId.try_create("")
        assert result.is_err()


class TestModelName:
    def test_try_create_valid_name(self):
        result = ModelName.try_create("gpt-4")
        assert result.is_ok()
        name = result.ok()
        assert name is not None
        assert name.value() == "gpt-4"

    def test_try_create_empty_name_fails(self):
        result = ModelName.try_create("")
        assert result.is_err()


class TestModel:
    def test_try_create_valid_model(self):
        result = Model.try_create("model-1", USER_ID, "gpt-4", "key-1")
        assert result.is_ok()
        model = result.ok()
        assert model is not None
        assert model.id().value() == "model-1"
        assert model.name().value() == "gpt-4"
        assert model.api_key_id().value() == "key-1"


class TestModelsCollection:
    def test_add_and_find_model(self):
        model_res = Model.try_create("model-1", USER_ID, "gpt-4", "key-1")
        assert model_res.is_ok()
        model = model_res.ok()
        assert model is not None
        models = Models(())
        added_res = models.add_model(model)
        assert added_res.is_ok()
        added_models = added_res.ok()
        assert added_models is not None
        find_res = added_models.find_by_id(model.id())
        assert find_res.is_ok()

    def test_remove_model(self):
        model_res = Model.try_create("model-1", USER_ID, "gpt-4", "key-1")
        assert model_res.is_ok()
        model = model_res.ok()
        assert model is not None
        models = Models((model,))
        removed_res = models.remove_model(model.id())
        assert removed_res.is_ok()
        removed_models = removed_res.ok()
        assert removed_models is not None
        assert removed_models.is_empty()


class TestEvents:
    def test_model_added_event(self):
        model_res = Model.try_create("model-1", USER_ID, "gpt-4", "key-1")
        assert model_res.is_ok()
        model = model_res.ok()
        assert model is not None
        event = ModelAddedEvent(model)
        assert event.model().id().value() == "model-1"

    def test_model_removed_event(self):
        id_res = ModelId.try_create("model-1")
        assert id_res.is_ok()
        model_id = id_res.ok()
        assert model_id is not None
        event = ModelRemovedEvent(model_id)
        assert event.model_id().value() == "model-1"

    def test_model_updated_event(self):
        model_res = Model.try_create("model-1", USER_ID, "gpt-4", "key-1")
        assert model_res.is_ok()
        model = model_res.ok()
        assert model is not None
        event = ModelUpdatedEvent(model)
        assert event.model().id().value() == "model-1"

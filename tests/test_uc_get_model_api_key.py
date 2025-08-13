from codebase_to_llm.application.ports import ApiKeyRepositoryPort, ModelRepositoryPort
from codebase_to_llm.application.uc_get_model_api_key import GetModelApiKeyUseCase
from codebase_to_llm.domain.api_key import ApiKey
from codebase_to_llm.domain.model import Model, ModelId
from codebase_to_llm.domain.result import Err, Ok

USER_ID = "user-1"


class DummyApiKeyRepo(ApiKeyRepositoryPort):
    def __init__(self) -> None:
        api_key_res = ApiKey.try_create(
            "k1", USER_ID, "https://api.openai.com", "sk-1234567890"
        )
        assert api_key_res.is_ok()
        self._api_key = api_key_res.ok()

    def load_api_keys(self):  # type: ignore[override]
        return Ok(None)

    def save_api_keys(self, api_keys):  # type: ignore[override]
        return Ok(None)

    def find_api_key_by_id(self, api_key_id):  # type: ignore[override]
        if self._api_key and self._api_key.id().value() == api_key_id.value():
            return Ok(self._api_key)
        return Err("not found")


class DummyModelRepo(ModelRepositoryPort):
    def __init__(self) -> None:
        model_res = Model.try_create("m1", USER_ID, "gpt-4.1", "k1")
        assert model_res.is_ok()
        self._model = model_res.ok()

    def load_models(self):  # type: ignore[override]
        return Ok(None)

    def save_models(self, models):  # type: ignore[override]
        return Ok(None)

    def find_model_by_id(self, model_id):  # type: ignore[override]
        if self._model and self._model.id().value() == model_id.value():
            return Ok(self._model)
        return Err("not found")


def test_get_model_api_key_use_case() -> None:
    api_repo: ApiKeyRepositoryPort = DummyApiKeyRepo()
    model_repo: ModelRepositoryPort = DummyModelRepo()
    use_case = GetModelApiKeyUseCase()

    model_id_res = ModelId.try_create("m1")
    assert model_id_res.is_ok()
    model_id = model_id_res.ok()
    assert model_id is not None

    result = use_case.execute(model_id, model_repo, api_repo)
    assert result.is_ok()
    result_value = result.ok()
    assert result_value is not None
    model_name, api_key = result_value
    assert model_name == "gpt-4.1"
    assert api_key.id().value() == "k1"

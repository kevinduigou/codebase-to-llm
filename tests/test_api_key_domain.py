from codebase_to_llm.domain.api_key import (
    ApiKeyId,
    UrlProvider,
    ApiKeyValue,
    ApiKey,
    ApiKeys,
    ApiKeyAddedEvent,
    ApiKeyRemovedEvent,
    ApiKeyUpdatedEvent,
)


class TestApiKeyId:
    def test_try_create_valid_id_succeeds(self):
        result = ApiKeyId.try_create("openai-key-1")
        assert result.is_ok()
        api_key_id = result.ok()
        assert api_key_id is not None
        assert api_key_id.value() == "openai-key-1"

    def test_try_create_empty_id_fails(self):
        result = ApiKeyId.try_create("")
        assert result.is_err()
        assert "cannot be empty" in (result.err() or "")

    def test_try_create_whitespace_only_id_fails(self):
        result = ApiKeyId.try_create("   ")
        assert result.is_err()
        assert "cannot be empty" in (result.err() or "")

    def test_try_create_too_long_id_fails(self):
        long_id = "a" * 101
        result = ApiKeyId.try_create(long_id)
        assert result.is_err()
        assert "cannot exceed 100 characters" in (result.err() or "")

    def test_try_create_trims_whitespace(self):
        result = ApiKeyId.try_create("  openai-key-1  ")
        assert result.is_ok()
        api_key_id = result.ok()
        assert api_key_id is not None
        assert api_key_id.value() == "openai-key-1"


class TestUrlProvider:
    def test_try_create_valid_https_url_succeeds(self):
        result = UrlProvider.try_create("https://api.openai.com")
        assert result.is_ok()
        url_provider = result.ok()
        assert url_provider is not None
        assert url_provider.value() == "https://api.openai.com"

    def test_try_create_valid_http_url_succeeds(self):
        result = UrlProvider.try_create("http://localhost:8080")
        assert result.is_ok()
        url_provider = result.ok()
        assert url_provider is not None
        assert url_provider.value() == "http://localhost:8080"

    def test_try_create_empty_url_fails(self):
        result = UrlProvider.try_create("")
        assert result.is_err()
        assert "cannot be empty" in (result.err() or "")

    def test_try_create_invalid_protocol_fails(self):
        result = UrlProvider.try_create("ftp://example.com")
        assert result.is_err()
        assert "must start with http://" in (result.err() or "")

    def test_try_create_no_protocol_fails(self):
        result = UrlProvider.try_create("api.openai.com")
        assert result.is_err()
        assert "must start with http://" in (result.err() or "")

    def test_try_create_too_long_url_fails(self):
        long_url = "https://" + "a" * 500
        result = UrlProvider.try_create(long_url)
        assert result.is_err()
        assert "cannot exceed 500 characters" in (result.err() or "")


class TestApiKeyValue:
    def test_try_create_valid_key_succeeds(self):
        result = ApiKeyValue.try_create("sk-1234567890abcdef")
        assert result.is_ok()
        api_key_value = result.ok()
        assert api_key_value is not None
        assert api_key_value.value() == "sk-1234567890abcdef"

    def test_try_create_empty_key_fails(self):
        result = ApiKeyValue.try_create("")
        assert result.is_err()
        assert "cannot be empty" in (result.err() or "")

    def test_try_create_too_short_key_fails(self):
        result = ApiKeyValue.try_create("short")
        assert result.is_err()
        assert "must be at least 10 characters" in (result.err() or "")

    def test_try_create_too_long_key_fails(self):
        long_key = "a" * 1001
        result = ApiKeyValue.try_create(long_key)
        assert result.is_err()
        assert "cannot exceed 1000 characters" in (result.err() or "")

    def test_masked_value_short_key(self):
        key = ApiKeyValue("1234567890")
        assert key.masked_value() == "**********"

    def test_masked_value_long_key(self):
        key = ApiKeyValue("sk-1234567890abcdefghijklmnop")
        masked = key.masked_value()
        assert masked.startswith("sk-1")
        assert masked.endswith("mnop")
        assert "*" in masked
        assert len(masked) == len(key.value())


class TestApiKey:
    def test_try_create_valid_api_key_succeeds(self):
        result = ApiKey.try_create(
            "openai-key-1", "https://api.openai.com", "sk-1234567890abcdef"
        )
        assert result.is_ok()
        api_key = result.ok()
        assert api_key is not None
        assert api_key.id().value() == "openai-key-1"
        assert api_key.url_provider().value() == "https://api.openai.com"
        assert api_key.api_key_value().value() == "sk-1234567890abcdef"

    def test_try_create_invalid_id_fails(self):
        result = ApiKey.try_create("", "https://api.openai.com", "sk-1234567890abcdef")
        assert result.is_err()
        assert "Invalid API Key ID" in (result.err() or "")

    def test_try_create_invalid_url_fails(self):
        result = ApiKey.try_create("openai-key-1", "invalid-url", "sk-1234567890abcdef")
        assert result.is_err()
        assert "Invalid URL Provider" in (result.err() or "")

    def test_try_create_invalid_key_value_fails(self):
        result = ApiKey.try_create("openai-key-1", "https://api.openai.com", "short")
        assert result.is_err()
        assert "Invalid API Key Value" in (result.err() or "")

    def test_update_url_provider_returns_new_instance(self):
        api_key_result = ApiKey.try_create(
            "openai-key-1", "https://api.openai.com", "sk-1234567890abcdef"
        )
        assert api_key_result.is_ok()
        api_key = api_key_result.ok()
        assert api_key is not None

        new_url_result = UrlProvider.try_create("https://api.anthropic.com")
        assert new_url_result.is_ok()
        new_url = new_url_result.ok()
        assert new_url is not None

        updated_key = api_key.update_url_provider(new_url)

        assert updated_key.url_provider().value() == "https://api.anthropic.com"
        assert updated_key.id().value() == api_key.id().value()
        assert updated_key.api_key_value().value() == api_key.api_key_value().value()
        # Original should be unchanged
        assert api_key.url_provider().value() == "https://api.openai.com"


class TestApiKeys:
    def test_try_create_empty_collection_succeeds(self):
        result = ApiKeys.try_create(())
        assert result.is_ok()
        api_keys = result.ok()
        assert api_keys is not None
        assert api_keys.is_empty()
        assert api_keys.count() == 0

    def test_try_create_with_duplicate_ids_fails(self):
        key1_result = ApiKey.try_create(
            "key-1", "https://api.openai.com", "sk-1234567890abcdef"
        )
        assert key1_result.is_ok()
        key1 = key1_result.ok()
        assert key1 is not None
        key2_result = ApiKey.try_create(
            "key-1", "https://api.anthropic.com", "sk-abcdef1234567890"
        )
        assert key2_result.is_ok()
        key2 = key2_result.ok()
        assert key2 is not None

        result = ApiKeys.try_create((key1, key2))
        assert result.is_err()
        assert "Duplicate API Key IDs" in (result.err() or "")

    def test_add_api_key_succeeds(self):
        api_keys = ApiKeys(())

        key_result = ApiKey.try_create(
            "key-1", "https://api.openai.com", "sk-1234567890abcdef"
        )
        assert key_result.is_ok()
        key = key_result.ok()
        assert key is not None

        result = api_keys.add_api_key(key)
        assert result.is_ok()

        updated_keys = result.ok()
        assert updated_keys is not None
        assert updated_keys.count() == 1
        assert not updated_keys.is_empty()

    def test_add_duplicate_api_key_fails(self):
        key_result = ApiKey.try_create(
            "key-1", "https://api.openai.com", "sk-1234567890abcdef"
        )
        assert key_result.is_ok()
        key = key_result.ok()
        assert key is not None

        api_keys = ApiKeys((key,))

        duplicate_key_result = ApiKey.try_create(
            "key-1", "https://api.anthropic.com", "sk-abcdef1234567890"
        )
        assert duplicate_key_result.is_ok()
        duplicate_key = duplicate_key_result.ok()
        assert duplicate_key is not None

        result = api_keys.add_api_key(duplicate_key)
        assert result.is_err()
        assert "already exists" in (result.err() or "")

    def test_remove_api_key_succeeds(self):
        key_result = ApiKey.try_create(
            "key-1", "https://api.openai.com", "sk-1234567890abcdef"
        )
        assert key_result.is_ok()
        key = key_result.ok()
        assert key is not None

        api_keys = ApiKeys((key,))

        result = api_keys.remove_api_key(key.id())
        assert result.is_ok()

        updated_keys = result.ok()
        assert updated_keys is not None
        assert updated_keys.is_empty()

    def test_remove_nonexistent_api_key_fails(self):
        api_keys = ApiKeys(())

        id_result = ApiKeyId.try_create("nonexistent")
        assert id_result.is_ok()
        id_val = id_result.ok()
        assert id_val is not None

        result = api_keys.remove_api_key(id_val)
        assert result.is_err()
        assert "not found" in (result.err() or "")

    def test_update_api_key_succeeds(self):
        key_result = ApiKey.try_create(
            "key-1", "https://api.openai.com", "sk-1234567890abcdef"
        )
        assert key_result.is_ok()
        key = key_result.ok()
        assert key is not None

        api_keys = ApiKeys((key,))

        new_url_result = UrlProvider.try_create("https://api.anthropic.com")
        assert new_url_result.is_ok()
        new_url = new_url_result.ok()
        assert new_url is not None
        updated_key = key.update_url_provider(new_url)

        result = api_keys.update_api_key(updated_key)
        assert result.is_ok()

        updated_keys = result.ok()
        assert updated_keys is not None
        found_key_result = updated_keys.find_by_id(key.id())
        assert found_key_result.is_ok()
        found_key = found_key_result.ok()
        assert found_key is not None
        assert found_key.url_provider().value() == "https://api.anthropic.com"

    def test_find_by_id_succeeds(self):
        key_result = ApiKey.try_create(
            "key-1", "https://api.openai.com", "sk-1234567890abcdef"
        )
        assert key_result.is_ok()
        key = key_result.ok()
        assert key is not None

        api_keys = ApiKeys((key,))

        result = api_keys.find_by_id(key.id())
        assert result.is_ok()
        found_key = result.ok()
        assert found_key is not None
        assert found_key.id().value() == "key-1"

    def test_find_by_id_fails_when_not_found(self):
        api_keys = ApiKeys(())

        id_result = ApiKeyId.try_create("nonexistent")
        assert id_result.is_ok()
        id_val = id_result.ok()
        assert id_val is not None

        result = api_keys.find_by_id(id_val)
        assert result.is_err()
        assert "not found" in (result.err() or "")


class TestEvents:
    def test_api_key_added_event(self):
        key_result = ApiKey.try_create(
            "key-1", "https://api.openai.com", "sk-1234567890abcdef"
        )
        assert key_result.is_ok()
        key = key_result.ok()
        assert key is not None

        event = ApiKeyAddedEvent(key)
        assert event.api_key().id().value() == "key-1"

    def test_api_key_removed_event(self):
        id_result = ApiKeyId.try_create("key-1")
        assert id_result.is_ok()
        id_val = id_result.ok()
        assert id_val is not None

        event = ApiKeyRemovedEvent(id_val)
        assert event.api_key_id().value() == "key-1"

    def test_api_key_updated_event(self):
        key_result = ApiKey.try_create(
            "key-1", "https://api.openai.com", "sk-1234567890abcdef"
        )
        assert key_result.is_ok()
        key = key_result.ok()
        assert key is not None

        event = ApiKeyUpdatedEvent(key)
        assert event.api_key().id().value() == "key-1"

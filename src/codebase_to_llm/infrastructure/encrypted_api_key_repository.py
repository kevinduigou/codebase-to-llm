from __future__ import annotations

import json
import base64
from pathlib import Path

from codebase_to_llm.application.ports import ApiKeyRepositoryPort
from codebase_to_llm.domain.api_key import ApiKeys, ApiKey, ApiKeyId
from codebase_to_llm.domain.result import Result, Ok, Err

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False


class EncryptedApiKeyRepository(ApiKeyRepositoryPort):
    """Encrypted file system implementation of API key repository.

    Note: Requires 'cryptography' package to be installed.
    Falls back to plain text if encryption is not available.
    """

    __slots__ = ("_file_path", "_password", "_user_id")
    _file_path: Path
    _password: bytes
    _user_id: str

    def __init__(
        self,
        user_id: str,
        file_path: Path | None = None,
        password: str = "default_password",
    ):
        self._user_id = user_id
        if file_path is None:
            self._file_path = Path.home() / ".dcc_api_keys_encrypted.json"
        else:
            self._file_path = file_path

        self._password = password.encode("utf-8")

        if not ENCRYPTION_AVAILABLE:
            print(
                "Warning: Cryptography package not available. API keys will be stored in plain text."
            )

    def _get_cipher(self) -> Fernet | None:
        """Creates a Fernet cipher for encryption/decryption."""
        if not ENCRYPTION_AVAILABLE:
            return None

        # Generate a key from password using PBKDF2
        salt = b"stable_salt_for_api_keys"  # In production, use a random salt per file
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._password))
        return Fernet(key)

    def _encrypt_data(self, data: str) -> str:
        """Encrypts data if encryption is available."""
        cipher = self._get_cipher()
        if cipher is None:
            return data  # Return plain text if encryption not available

        encrypted_data = cipher.encrypt(data.encode("utf-8"))
        return base64.urlsafe_b64encode(encrypted_data).decode("utf-8")

    def _decrypt_data(self, encrypted_data: str) -> Result[str, str]:
        """Decrypts data if encryption is available."""
        cipher = self._get_cipher()
        if cipher is None:
            return Ok(encrypted_data)  # Return as-is if encryption not available

        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode("utf-8"))
            decrypted_data = cipher.decrypt(decoded_data)
            return Ok(decrypted_data.decode("utf-8"))
        except Exception as e:
            return Err(f"Failed to decrypt data: {str(e)}")

    def load_api_keys(self) -> Result[ApiKeys, str]:
        """Loads and decrypts API keys from the file system."""
        try:
            if not self._file_path.exists():
                return Ok(ApiKeys(()))

            with open(self._file_path, "r", encoding="utf-8") as f:
                encrypted_content = f.read()

            # Decrypt the content
            decrypted_result = self._decrypt_data(encrypted_content)
            if decrypted_result.is_err():
                return Err(decrypted_result.err() or "Failed to decrypt data.")

            decrypted_content = decrypted_result.ok()
            if decrypted_content is None:
                return Err("Decrypted content is None.")

            # Parse JSON
            try:
                data = json.loads(decrypted_content)
            except json.JSONDecodeError as e:
                return Err(f"Failed to parse decrypted API keys: {str(e)}")

            # Validate and convert to domain objects (same logic as FileSystemApiKeyRepository)
            if not isinstance(data, dict) or "api_keys" not in data:
                return Err("Invalid API keys file format")

            api_keys_data = data["api_keys"]
            if not isinstance(api_keys_data, list):
                return Err("Invalid API keys data format")

            api_keys_list = []
            for key_data in api_keys_data:
                if not isinstance(key_data, dict):
                    return Err("Invalid API key data format")

                required_fields = ["id", "url_provider", "api_key_value"]
                for field in required_fields:
                    if field not in key_data:
                        return Err(f"Missing required field: {field}")

                api_key_result = ApiKey.try_create(
                    key_data["id"],
                    self._user_id,
                    key_data["url_provider"],
                    key_data["api_key_value"],
                )

                if api_key_result.is_ok():
                    api_key = api_key_result.ok()
                    if api_key is not None:
                        api_keys_list.append(api_key)

            api_keys_result = ApiKeys.try_create(tuple(api_keys_list))
            if api_keys_result.is_err():
                return Err(
                    api_keys_result.err()
                    or "Unknown error creating ApiKeys collection."
                )
            api_keys = api_keys_result.ok()
            if api_keys is None:
                return Err("Failed to create ApiKeys collection.")

            return Ok(api_keys)

        except OSError as e:
            return Err(f"Failed to read API keys file: {str(e)}")
        except Exception as e:
            return Err(f"Unexpected error loading API keys: {str(e)}")

    def save_api_keys(self, api_keys: ApiKeys) -> Result[None, str]:
        """Encrypts and saves API keys to the file system."""
        try:
            # Convert to JSON
            api_keys_data = []
            for api_key in api_keys.api_keys():
                key_data = {
                    "id": api_key.id().value(),
                    "url_provider": api_key.url_provider().value(),
                    "api_key_value": api_key.api_key_value().value(),
                }
                api_keys_data.append(key_data)

            data = {"api_keys": api_keys_data, "version": "1.0"}

            json_content = json.dumps(data, indent=2, ensure_ascii=False)

            # Encrypt the content
            encrypted_content = self._encrypt_data(json_content)

            # Ensure directory exists
            self._file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to temporary file first, then rename for atomic operation
            temp_file = self._file_path.with_suffix(".tmp")

            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(encrypted_content)

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
            return Err(api_keys_result.err() or "Unknown error loading API keys.")

        api_keys = api_keys_result.ok()
        if api_keys is None:
            return Err("Failed to load ApiKeys collection.")
        return api_keys.find_by_id(api_key_id)

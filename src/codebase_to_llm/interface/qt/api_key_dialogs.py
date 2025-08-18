from __future__ import annotations

import uuid

from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QTextEdit,
)
from PySide6.QtCore import Qt

from codebase_to_llm.application.ports import ApiKeyRepositoryPort
from codebase_to_llm.application.uc_add_api_key import AddApiKeyUseCase
from codebase_to_llm.application.uc_update_api_key import UpdateApiKeyUseCase
from codebase_to_llm.application.uc_remove_api_key import RemoveApiKeyUseCase
from codebase_to_llm.application.uc_load_api_keys import LoadApiKeysUseCase
from codebase_to_llm.domain.api_key import ApiKey


class ApiKeyFormDialog(QDialog):
    """Dialog for adding or editing an API key."""

    __slots__ = (
        "_id_edit",
        "_url_edit",
        "_key_edit",
        "_is_edit_mode",
        "_original_api_key",
        "_api_key_repo",
        "_user_id",
    )

    def __init__(
        self,
        api_key_repo: ApiKeyRepositoryPort,
        user_id: str,
        api_key: ApiKey | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._api_key_repo = api_key_repo
        self._user_id = user_id
        self._is_edit_mode = api_key is not None
        self._original_api_key = api_key

        self.setWindowTitle("Edit API Key" if self._is_edit_mode else "Add API Key")
        self.setModal(True)
        self.resize(500, 300)

        self._setup_ui()

        if self._is_edit_mode and api_key:
            self._populate_fields(api_key)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Form layout
        form_layout = QFormLayout()

        # ID field
        self._id_edit = QLineEdit()
        if self._is_edit_mode:
            self._id_edit.setEnabled(False)  # ID cannot be changed in edit mode
            self._id_edit.setToolTip("API Key ID cannot be changed")
        else:
            self._id_edit.setPlaceholderText(
                "e.g., openai-key-1 (leave empty to auto-generate)"
            )
            self._id_edit.setToolTip("Unique identifier for this API key")
        form_layout.addRow("ID:", self._id_edit)

        # URL Provider field
        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText("e.g., https://api.openai.com")
        self._url_edit.setToolTip("Base URL of the API provider")
        form_layout.addRow("URL Provider:", self._url_edit)

        # API Key field
        self._key_edit = QTextEdit()
        self._key_edit.setPlaceholderText("Enter your API key here...")
        self._key_edit.setToolTip("The actual API key value (will be stored securely)")
        self._key_edit.setMaximumHeight(100)
        form_layout.addRow("API Key:", self._key_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_save)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _populate_fields(self, api_key: ApiKey) -> None:
        """Populates the form fields with existing API key data."""
        self._id_edit.setText(api_key.id().value())
        self._url_edit.setText(api_key.url_provider().value())
        self._key_edit.setPlainText(api_key.api_key_value().value())

    def _on_save(self) -> None:
        """Handles the save button click."""
        try:
            # Get form values
            id_value = self._id_edit.text().strip()
            url_value = self._url_edit.text().strip()
            key_value = self._key_edit.toPlainText().strip()

            # Auto-generate ID if empty in add mode
            if not self._is_edit_mode and not id_value:
                id_value = f"api-key-{str(uuid.uuid4())[:8]}"

            # Validate required fields
            if not id_value:
                QMessageBox.warning(self, "Validation Error", "ID is required.")
                return

            if not url_value:
                QMessageBox.warning(
                    self, "Validation Error", "URL Provider is required."
                )
                return

            if not key_value:
                QMessageBox.warning(self, "Validation Error", "API Key is required.")
                return

            # Execute the appropriate use case
            if self._is_edit_mode:
                update_use_case = UpdateApiKeyUseCase(self._api_key_repo)
                update_result = update_use_case.execute(id_value, url_value, key_value)
                if update_result.is_err():
                    QMessageBox.critical(
                        self,
                        "Failed to update API Key",
                        update_result.err()
                        or "Unknown error occurred while trying to update API key.",
                    )
                    return
                # Success
                self.accept()
                return
            else:
                add_use_case = AddApiKeyUseCase(self._api_key_repo)
                add_result = add_use_case.execute(
                    self._user_id, id_value, url_value, key_value
                )
                if add_result.is_err():
                    QMessageBox.critical(
                        self,
                        "Failed to add API Key",
                        add_result.err()
                        or "Unknown error occurred while trying to add API key.",
                    )
                    return
                # Success
                self.accept()
                return

        except Exception as e:
            QMessageBox.critical(
                self, "Unexpected Error", f"An unexpected error occurred: {str(e)}"
            )


class ApiKeyManagerDialog(QDialog):
    """Main dialog for managing API keys."""

    __slots__ = (
        "_api_key_repo",
        "_user_id",
        "_list_widget",
        "_add_btn",
        "_edit_btn",
        "_delete_btn",
        "_selected_api_key",
        "_load_use_case",
    )

    def __init__(
        self,
        api_key_repo: ApiKeyRepositoryPort,
        user_id: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._api_key_repo = api_key_repo
        self._user_id = user_id
        self._selected_api_key: ApiKey | None = None
        self._load_use_case = LoadApiKeysUseCase(api_key_repo)

        self.setWindowTitle("Manage API Keys")
        self.setModal(True)
        self.resize(600, 400)

        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)

        # Left side - API key list
        left_layout = QVBoxLayout()

        list_label = QLabel("API Keys:")
        list_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(list_label)

        self._list_widget = QListWidget()
        self._list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._list_widget.currentItemChanged.connect(self._on_selection_changed)
        self._list_widget.itemDoubleClicked.connect(self._on_edit)
        left_layout.addWidget(self._list_widget)

        layout.addLayout(left_layout, 2)  # 2/3 of the width

        # Right side - buttons
        button_layout = QVBoxLayout()

        self._add_btn = QPushButton("Add API Key")
        self._add_btn.clicked.connect(self._on_add)
        button_layout.addWidget(self._add_btn)

        self._edit_btn = QPushButton("Edit API Key")
        self._edit_btn.clicked.connect(self._on_edit)
        self._edit_btn.setEnabled(False)
        button_layout.addWidget(self._edit_btn)

        self._delete_btn = QPushButton("Delete API Key")
        self._delete_btn.clicked.connect(self._on_delete)
        self._delete_btn.setEnabled(False)
        button_layout.addWidget(self._delete_btn)

        button_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout, 1)  # 1/3 of the width

    def _refresh_list(self) -> None:
        """Refreshes the API key list."""
        self._list_widget.clear()
        self._selected_api_key = None
        self._update_button_states()

        # Load API keys
        result = self._load_use_case.execute()
        if result.is_err():
            QMessageBox.critical(
                self, "Load Error", f"Failed to load API keys: {result.err()}"
            )
            return

        api_keys = result.ok()
        if api_keys is None:
            QMessageBox.critical(
                self, "Load Error", "Failed to load API keys: result is None."
            )
            return

        # Populate list
        for api_key in api_keys.api_keys():
            item = QListWidgetItem()

            # Display format: "ID - URL (masked key)"
            masked_key = api_key.api_key_value().masked_value()
            display_text = f"{api_key.id().value()} - {api_key.url_provider().value()}"
            item.setText(display_text)
            item.setToolTip(f"API Key: {masked_key}")

            # Store the API key object in the item
            item.setData(Qt.ItemDataRole.UserRole, api_key)

            self._list_widget.addItem(item)

    def _on_selection_changed(
        self, current: QListWidgetItem | None, previous: QListWidgetItem | None
    ) -> None:
        """Handles selection change in the list."""
        if current:
            self._selected_api_key = current.data(Qt.ItemDataRole.UserRole)
        else:
            self._selected_api_key = None

        self._update_button_states()

    def _update_button_states(self) -> None:
        """Updates the enabled state of buttons based on selection."""
        has_selection = self._selected_api_key is not None
        self._edit_btn.setEnabled(has_selection)
        self._delete_btn.setEnabled(has_selection)

    def _on_add(self) -> None:
        """Handles the add button click."""
        dialog = ApiKeyFormDialog(self._api_key_repo, self._user_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_list()

    def _on_edit(self) -> None:
        """Handles the edit button click."""
        if not self._selected_api_key:
            return

        dialog = ApiKeyFormDialog(
            self._api_key_repo,
            self._user_id,
            self._selected_api_key,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_list()

    def _on_delete(self) -> None:
        """Handles the delete button click."""
        if not self._selected_api_key:
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the API key '{self._selected_api_key.id().value()}'?\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Execute delete use case
        use_case = RemoveApiKeyUseCase(self._api_key_repo)
        result = use_case.execute(self._selected_api_key.id().value())

        if result.is_err():
            QMessageBox.critical(
                self, "Delete Error", f"Failed to delete API key: {result.err()}"
            )
            return

        # Success - refresh the list
        self._refresh_list()
        QMessageBox.information(
            self,
            "Success",
            f"API key '{self._selected_api_key.id().value()}' has been deleted.",
        )

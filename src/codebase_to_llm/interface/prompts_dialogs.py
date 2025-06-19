from __future__ import annotations

from typing import List

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QAbstractItemView,
)

from codebase_to_llm.domain.favorite_prompts import FavoritePrompt, FavoritePrompts
from codebase_to_llm.infrastructure.filesystem_favorite_prompts_repository import (
    FavoritePromptsRepository,
)


class PromptDialogForm(QDialog):
    """Dialog to edit a single prompt."""

    def __init__(self, current_content: str, repo: FavoritePromptsRepository, name: str = "") -> None:
        super().__init__()
        self.setWindowTitle("Edit Prompt")
        self._repo = repo
        layout = QVBoxLayout(self)

        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        self._name_edit = QLineEdit()
        self._name_edit.setText(name)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self._name_edit)
        layout.addLayout(name_layout)

        self._edit = QPlainTextEdit()
        self._edit.setPlainText(current_content)
        layout.addWidget(self._edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Save")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
        buttons.accepted.connect(self.accept)  # type: ignore[arg-type]
        buttons.rejected.connect(self.reject)  # type: ignore[arg-type]
        layout.addWidget(buttons)

    def text(self) -> str:
        return self._edit.toPlainText()

    def name(self) -> str:
        return self._name_edit.text()


class PromptsManagerDialog(QDialog):
    """Dialog to manage all favorite prompts."""

    def __init__(self, repo: FavoritePromptsRepository) -> None:
        super().__init__()
        self.setWindowTitle("Manage Favorite Prompts")
        self._repo = repo
        self._selected_index: int | None = None
        self._prompts: List[FavoritePrompt] = []

        layout = QHBoxLayout(self)

        self._list_widget = QListWidget()
        self._list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list_widget.currentRowChanged.connect(self._on_selected)
        layout.addWidget(self._list_widget, 1)

        button_layout = QVBoxLayout()
        self._new_btn = QPushButton("New Prompt")
        self._delete_btn = QPushButton("Delete Prompt")
        self._modify_btn = QPushButton("Modify Prompt")
        self._new_btn.clicked.connect(self._on_new)
        self._delete_btn.clicked.connect(self._on_delete)
        self._modify_btn.clicked.connect(self._on_modify)
        button_layout.addWidget(self._new_btn)
        button_layout.addWidget(self._delete_btn)
        button_layout.addWidget(self._modify_btn)
        button_layout.addStretch(1)
        layout.addLayout(button_layout)

        self._load_prompts()

    def _load_prompts(self) -> None:
        result = self._repo.load_prompts()
        if result.is_ok():
            val = result.ok()
            assert val is not None
            self._prompts = list(val.prompts())
        else:
            self._prompts = []
        self._refresh_list()
        if self._prompts:
            self._list_widget.setCurrentRow(0)

    def _refresh_list(self) -> None:
        self._list_widget.clear()
        for prompt in self._prompts:
            self._list_widget.addItem(prompt.name())

    def _on_selected(self, idx: int) -> None:
        self._selected_index = idx if 0 <= idx < len(self._prompts) else None

    def _on_new(self) -> None:
        dialog = PromptDialogForm("", self._repo, name="")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.name().strip()
            content = dialog.text()
            if not name:
                QMessageBox.warning(self, "Validation Error", "Prompt name cannot be empty.")
                return
            result = FavoritePrompt.try_create(name, content)
            if result.is_err():
                QMessageBox.warning(self, "Validation Error", result.err() or "Invalid prompt.")
                return
            self._prompts.append(result.ok())
            self._refresh_list()
            self._list_widget.setCurrentRow(len(self._prompts) - 1)
            prompts_obj = FavoritePrompts(tuple(self._prompts))
            save_result = self._repo.save_prompts(prompts_obj)
            if save_result.is_err():
                QMessageBox.critical(self, "Save Error", save_result.err() or "Failed to save prompts.")

    def _on_modify(self) -> None:
        idx = self._selected_index
        if idx is not None and 0 <= idx < len(self._prompts):
            prompt = self._prompts[idx]
            dialog = PromptDialogForm(prompt.content(), self._repo, name=prompt.name())
            if dialog.exec() == QDialog.DialogCode.Accepted:
                name = dialog.name().strip()
                content = dialog.text()
                if not name:
                    QMessageBox.warning(self, "Validation Error", "Prompt name cannot be empty.")
                    return
                result = FavoritePrompt.try_create(name, content)
                if result.is_err():
                    QMessageBox.warning(self, "Validation Error", result.err() or "Invalid prompt.")
                    return
                self._prompts[idx] = result.ok()
                self._refresh_list()
                self._list_widget.setCurrentRow(idx)
                prompts_obj = FavoritePrompts(tuple(self._prompts))
                save_result = self._repo.save_prompts(prompts_obj)
                if save_result.is_err():
                    QMessageBox.critical(self, "Save Error", save_result.err() or "Failed to save prompts.")

    def _on_delete(self) -> None:
        idx = self._selected_index
        if idx is not None and 0 <= idx < len(self._prompts):
            del self._prompts[idx]
            self._refresh_list()
            self._selected_index = None
            prompts_obj = FavoritePrompts(tuple(self._prompts))
            save_result = self._repo.save_prompts(prompts_obj)
            if save_result.is_err():
                QMessageBox.critical(self, "Save Error", save_result.err() or "Failed to save prompts.")



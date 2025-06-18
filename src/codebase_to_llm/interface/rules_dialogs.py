"""Dialogs used to manage rules in the GUI."""

from __future__ import annotations

from typing import List, cast

from PySide6.QtWidgets import (
    QAbstractItemView,
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
)

from codebase_to_llm.domain.rules import Rule, Rules
from codebase_to_llm.infrastructure.filesystem_rules_repository import RulesRepository


class RulesDialogForm(QDialog):
    """Dialog to edit a single rule."""

    __slots__ = ("_name_edit", "_desc_edit", "_edit", "_rules_repo")

    def __init__(
        self,
        current_rules: str,
        rules_repo: RulesRepository,
        name: str = "",
        description: str = "",
    ) -> None:
        super().__init__()
        self.setWindowTitle("Edit Rules")
        layout = QVBoxLayout(self)

        name_desc_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        self._name_edit = QLineEdit()
        self._name_edit.setText(name)
        desc_label = QLabel("Description:")
        self._desc_edit = QLineEdit()
        self._desc_edit.setText(description)
        name_desc_layout.addWidget(name_label)
        name_desc_layout.addWidget(self._name_edit)
        name_desc_layout.addWidget(desc_label)
        name_desc_layout.addWidget(self._desc_edit)
        layout.addLayout(name_desc_layout)

        self._edit = QPlainTextEdit()
        self._edit.setPlainText(current_rules)
        layout.addWidget(self._edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Save")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
        buttons.accepted.connect(self.accept)  # type: ignore[arg-type]
        buttons.rejected.connect(self.reject)  # type: ignore[arg-type]
        layout.addWidget(buttons)
        self._rules_repo = rules_repo

    def text(self) -> str:
        return self._edit.toPlainText()

    def name(self) -> str:
        return self._name_edit.text()

    def description(self) -> str:
        return self._desc_edit.text()

    def accept(self) -> None:  # noqa: D401
        return super().accept()


class RulesManagerDialog(QDialog):
    """Dialog to manage all rules."""

    def __init__(self, current_rules: str, rules_repo: RulesRepository):
        super().__init__()
        self.setWindowTitle("Manage Rules")
        self._rules_repo = rules_repo
        self._selected_index: int | None = None
        self._rules: List[Rule] = []

        layout = QHBoxLayout(self)

        self._list_widget = QListWidget()
        self._list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._list_widget.currentRowChanged.connect(self._on_rule_selected)
        layout.addWidget(self._list_widget, 1)

        button_layout = QVBoxLayout()
        self._new_btn = QPushButton("New Rule")
        self._delete_btn = QPushButton("Delete Rule")
        self._modify_btn = QPushButton("Modify Rule")
        self._new_btn.clicked.connect(self._on_new)
        self._delete_btn.clicked.connect(self._on_delete)
        self._modify_btn.clicked.connect(self._on_modify)
        button_layout.addWidget(self._new_btn)
        button_layout.addWidget(self._delete_btn)
        button_layout.addWidget(self._modify_btn)
        button_layout.addStretch(1)
        layout.addLayout(button_layout)

        self._load_rules()

    def _load_rules(self) -> None:
        from codebase_to_llm.domain.rules import Rules

        rules_result = self._rules_repo.load_rules()
        if rules_result.is_ok():
            rules_obj = rules_result.ok()
            assert rules_obj is not None
            self._rules = list(rules_obj.rules())
        else:
            self._rules = []
        self._refresh_list()
        if self._rules:
            self._list_widget.setCurrentRow(0)

    def _refresh_list(self) -> None:
        self._list_widget.clear()
        for rule in self._rules:
            desc = rule.description() or ""
            label = f"{rule.name()} — {desc}" if desc else rule.name()
            self._list_widget.addItem(label)

    def _on_rule_selected(self, idx: int) -> None:
        self._selected_index = idx if 0 <= idx < len(self._rules) else None

    def _on_new(self) -> None:
        dialog = RulesDialogForm("", self._rules_repo, name="", description="")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            from codebase_to_llm.domain.rules import Rule, Rules

            name = dialog.name().strip()
            desc = dialog.description().strip()
            content = dialog.text()
            if not name:
                QMessageBox.warning(
                    self, "Validation Error", "Rule name cannot be empty."
                )
                return
            rule_result = Rule.try_create(name, content, desc)
            if rule_result.is_err():
                QMessageBox.warning(
                    self, "Validation Error", rule_result.err() or "Invalid rule."
                )
                return
            rule = cast(Rule, rule_result.ok())
            self._rules.append(rule)
            self._refresh_list()
            self._list_widget.setCurrentRow(len(self._rules) - 1)
            rules_obj = Rules(tuple(self._rules))
            save_result = self._rules_repo.save_rules(rules_obj)
            if save_result.is_err():
                QMessageBox.critical(
                    self, "Save Error", save_result.err() or "Failed to save rules."
                )

    def _on_modify(self) -> None:
        idx = self._selected_index
        if idx is not None and 0 <= idx < len(self._rules):
            rule = self._rules[idx]
            dialog = RulesDialogForm(
                rule.content(),
                self._rules_repo,
                name=rule.name(),
                description=rule.description() or "",
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                from codebase_to_llm.domain.rules import Rule, Rules

                name = dialog.name().strip()
                desc = dialog.description().strip()
                content = dialog.text()
                if not name:
                    QMessageBox.warning(
                        self, "Validation Error", "Rule name cannot be empty."
                    )
                    return
                rule_result = Rule.try_create(name, content, desc)
                if rule_result.is_err():
                    QMessageBox.warning(
                        self, "Validation Error", rule_result.err() or "Invalid rule."
                    )
                    return
                rule = cast(Rule, rule_result.ok())
                self._rules[idx] = rule
                self._refresh_list()
                self._list_widget.setCurrentRow(idx)
                rules_obj = Rules(tuple(self._rules))
                save_result = self._rules_repo.save_rules(rules_obj)
                if save_result.is_err():
                    QMessageBox.critical(
                        self, "Save Error", save_result.err() or "Failed to save rules."
                    )

    def _on_delete(self) -> None:
        idx = self._selected_index
        if idx is not None and 0 <= idx < len(self._rules):
            rule_to_delete: Rule = self._rules[idx]
            rule_to_delete_name = rule_to_delete.name()
            del self._rules[idx]
            self._refresh_list()
            self._selected_index = None
        current_rules = self._rules_repo.load_rules()
        if current_rules.is_ok():
            rules_obj = current_rules.ok()
            if rules_obj is not None:
                new_rules = rules_obj.remove_rule(rule_to_delete_name)
                self._rules_repo.save_rules(new_rules)
            else:
                QMessageBox.critical(self, "Save Error", "Failed to load rules.")
        else:
            QMessageBox.critical(
                self, "Save Error", current_rules.err() or "Failed to save rules."
            )

    def text(self) -> str:
        from codebase_to_llm.domain.rules import Rules

        rules_obj = Rules(tuple(self._rules))
        return rules_obj.to_text()

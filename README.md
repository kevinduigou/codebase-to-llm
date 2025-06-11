# Desktop Context Copier

Simple, immutable, Rust‑flavoured desktop utility that lets you:

1. Browse any directory from the **left panel** (tree view).
2. Drag‑and‑drop files into the **right panel** for collection.
3. Hit **Copy Context** to send to the clipboard:
   * the filtered directory tree (tagged `<tree_structure>`), and
   * the full contents of every collected file (tagged by path).

## Installation

```shell
# Install dependencies with **uv**
uv pip install -r requirements.txt

# Run the application
python main.py
```

## VSCode Setup

To run and debug the application easily in VSCode:

1. Open the project folder in VSCode.
2. Ensure you have the Python extension installed.
3. Use the provided launch configuration:
   - Go to the Run & Debug panel (Ctrl+Shift+D).
   - Select "Run Desktop Context Copier" and press F5 to launch.

If you do not see the configuration, ensure `.vscode/launch.json` exists as below.

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run Desktop Context Copier",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal"
        }
    ]
}
```

## Architectural notes

* **Hexagonal Architecture** (Ports/Adapters) keeps the GUI replaceable.
* **DDD**: all business rules (tree rendering) live in `domain/`.
* **Result** type eliminates exceptions in domain & application layers.
* **Immutable code** — `@final`, `__slots__`, and pure functions.

## Testing

```shell
pytest -q
```

## TODO

* Behave E2E scenarios.
* Celery task for huge directory export.
* Dark‑mode stylesheet for GUI.

# Enjoy!
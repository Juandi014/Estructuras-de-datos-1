
import json
import tkinter as tk
from tkinter import filedialog


# ------------------------------------------------------------------
# Public entry point
# ------------------------------------------------------------------

def load_file(avl_tree, bst_tree=None):
    """
    Opens a file dialog, reads the selected JSON file,
    auto-detects the mode (TOPOLOGIA or INSERCION),
    and loads the data into the provided tree(s).

    Returns:
        str: The detected mode ("TOPOLOGIA" or "INSERCION").
    """
    path = _open_file_dialog()
    raw = _read_file(path)
    data = _parse_json(raw)
    mode = _detect_mode(data)
    _load_by_mode(mode, data, avl_tree, bst_tree)
    return mode


# ------------------------------------------------------------------
# File dialog and reading
# ------------------------------------------------------------------

def _open_file_dialog() -> str:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    path = filedialog.askopenfilename(
        title="Select a SkyBalance JSON file",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
    )
    root.destroy()

    if not path:
        raise ValueError("No file was selected.")

    return path


def _read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        raise ValueError(f"Could not read file '{path}': {e}")


def _parse_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")


# ------------------------------------------------------------------
# AUTO DETECTION OF MODE (NEW)
# ------------------------------------------------------------------

def _detect_mode(data: dict) -> str:
    """
    Auto-detects the mode when 'tipo' is missing.
    - If it has top-level 'codigo' and children (izquierdo/derecho) → TOPOLOGIA
    - If it has a 'vuelos' list → INSERCION
    """
    if "tipo" in data:
        mode = str(data["tipo"]).upper()
        if mode in ("TOPOLOGIA", "INSERCION"):
            return mode

    # Auto-detection fallback
    if "codigo" in data and ("izquierdo" in data or "derecho" in data):
        return "TOPOLOGIA"

    if "vuelos" in data and isinstance(data["vuelos"], list):
        return "INSERCION"

    raise ValueError(
        "Could not detect mode. JSON must contain either:\n"
        "- 'tipo': 'TOPOLOGIA' or 'INSERCION', or\n"
        "- top-level 'codigo' with 'izquierdo'/'derecho' (topology), or\n"
        "- a 'vuelos' array (insertion)."
    )


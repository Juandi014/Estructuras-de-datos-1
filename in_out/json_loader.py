"""
json_loader.py
--------------
Handles reading and parsing of JSON files for the SkyBalance system.
Supports two modes:
  - TOPOLOGIA : Rebuilds the AVL tree from an existing tree structure.
  - INSERCION  : Builds the AVL and BST trees by inserting flights one by one.

Opens a file dialog so the user can browse for the JSON file.
"""

import json
import tkinter as tk
from tkinter import filedialog


# ------------------------------------------------------------------
# Public entry point
# ------------------------------------------------------------------

def load_file(avl_tree, bst_tree=None):
    """
    Opens a file dialog, reads the selected JSON file, detects its mode,
    and loads the data into the provided tree(s).

    Args:
        avl_tree : AVLTree instance to populate.
        bst_tree : BSTTree instance (only used in INSERCION mode). Can be None.

    Returns:
        str: The detected mode ("TOPOLOGIA" or "INSERCION").

    Raises:
        ValueError: If no file is selected, the JSON is invalid,
                    or the "tipo" field is missing or unrecognized.
    """
    path = _open_file_dialog()
    raw = _read_file(path)
    data = _parse_json(raw)
    mode = _extract_mode(data)
    _load_by_mode(mode, data, avl_tree, bst_tree)
    return mode


# ------------------------------------------------------------------
# File dialog
# ------------------------------------------------------------------

def _open_file_dialog() -> str:
    """
    Opens a native file dialog filtered to JSON files.

    Returns:
        str: Absolute path to the selected file.

    Raises:
        ValueError: If the user closes the dialog without selecting a file.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the empty tkinter window.
    root.attributes("-topmost", True)  # Dialog appears on top of Pygame window.

    path = filedialog.askopenfilename(
        title="Select a SkyBalance JSON file",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
    )
    root.destroy()

    if not path:
        raise ValueError("No file was selected.")

    return path


# ------------------------------------------------------------------
# File reading
# ------------------------------------------------------------------

def _read_file(path: str) -> str:
    """
    Reads the raw text content of a file.

    Args:
        path: Absolute path to the file.

    Returns:
        str: Raw file content.

    Raises:
        ValueError: If the file cannot be read.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        raise ValueError(f"Could not read file '{path}': {e}")


# ------------------------------------------------------------------
# JSON parsing
# ------------------------------------------------------------------

def _parse_json(raw: str) -> dict:
    """
    Parses a raw JSON string into a Python dictionary.

    Args:
        raw: Raw JSON string.

    Returns:
        dict: Parsed JSON content.

    Raises:
        ValueError: If the string is not valid JSON.
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")


# ------------------------------------------------------------------
# Mode detection
# ------------------------------------------------------------------

def _extract_mode(data: dict) -> str:
    """
    Reads the 'tipo' field from the JSON and validates it.

    Args:
        data: Parsed JSON dictionary.

    Returns:
        str: Either "TOPOLOGIA" or "INSERCION".

    Raises:
        ValueError: If 'tipo' is missing or not a recognized value.
    """
    if "tipo" not in data:
        raise ValueError(
            "The JSON file is missing the required 'tipo' field. "
            "Expected 'TOPOLOGIA' or 'INSERCION'."
        )

    mode = str(data["tipo"]).upper()

    if mode not in ("TOPOLOGIA", "INSERCION"):
        raise ValueError(
            f"Unrecognized mode '{data['tipo']}'. "
            "Expected 'TOPOLOGIA' or 'INSERCION'."
        )

    return mode


# ------------------------------------------------------------------
# Loading strategies
# ------------------------------------------------------------------

def _load_by_mode(mode: str, data: dict, avl_tree, bst_tree) -> None:
    """
    Delegates loading to the correct strategy based on the detected mode.

    Args:
        mode     : "TOPOLOGIA" or "INSERCION".
        data     : Full parsed JSON dictionary.
        avl_tree : AVLTree instance to populate.
        bst_tree : BSTTree instance (only used in INSERCION mode).
    """
    if mode == "TOPOLOGIA":
        _load_topology(data, avl_tree)
    else:
        _load_insertion(data, avl_tree, bst_tree)


def _load_topology(data: dict, avl_tree) -> None:
    """
    Loads a TOPOLOGIA JSON into the AVL tree.
    The existing tree structure is preserved — no rebalancing is performed.

    Args:
        data     : Full parsed JSON dictionary (root node is the top-level object).
        avl_tree : AVLTree instance to populate.

    Raises:
        ValueError: If the topology data is missing or malformed.
    """
    # In topology mode the root node data sits at the top level of the JSON.
    # We strip 'tipo' so fromTopology receives a clean flight+children dict.
    tree_data = {k: v for k, v in data.items() if k != "tipo"}

    if "codigo" not in tree_data:
        raise ValueError(
            "Topology JSON is missing the root node. "
            "Expected a 'codigo' field at the top level."
        )

    avl_tree.fromTopology(tree_data)


def _load_insertion(data: dict, avl_tree, bst_tree) -> None:
    """
    Loads an INSERCION JSON into the AVL tree and optionally the BST.
    Flights are sorted by priority before insertion.

    Args:
        data     : Full parsed JSON dictionary with a 'vuelos' list.
        avl_tree : AVLTree instance to populate.
        bst_tree : BSTTree instance to populate (skipped if None).

    Raises:
        ValueError: If the 'vuelos' list is missing or empty.
    """
    flights = data.get("vuelos")

    if not flights:
        raise ValueError(
            "Insertion JSON is missing the 'vuelos' list or it is empty."
        )

    sorted_flights = _sort_by_priority(flights)

    avl_tree.fromInsertionList(sorted_flights)

    if bst_tree is not None:
        bst_tree.fromInsertionList(sorted_flights)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _sort_by_priority(flights: list) -> list:
    """
    Sorts a list of flight dictionaries by their 'prioridad' field
    in ascending order (priority 1 enters before priority 2, etc.).
    Flights with no priority field default to 0 (inserted first).

    Args:
        flights: List of flight dictionaries.

    Returns:
        list: Sorted list of flight dictionaries.
    """
    return sorted(flights, key=lambda f: f.get("prioridad", 0))
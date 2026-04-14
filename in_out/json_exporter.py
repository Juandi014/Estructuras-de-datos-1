
import json
import tkinter as tk
from tkinter import filedialog


# ------------------------------------------------------------------
# Public entry point
# ------------------------------------------------------------------

def export_file(avl_tree) -> str:
    """
    Serializes the AVL tree and saves it to a user-selected JSON file.

    Args:
        avl_tree: AVLTree instance to export.

    Returns:
        str: Absolute path where the file was saved.

    Raises:
        ValueError: If the tree is empty, no destination is selected,
                    or the file cannot be written.
    """
    _validate_tree(avl_tree)
    path = _open_save_dialog()
    data = _serialize_tree(avl_tree)
    _write_file(path, data)
    return path


# ------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------

def _validate_tree(avl_tree) -> None:
    """
    Ensures the tree is not empty before attempting to export.

    Args:
        avl_tree: AVLTree instance to validate.

    Raises:
        ValueError: If the tree has no root node.
    """
    if avl_tree.getRoot() is None:
        raise ValueError("Cannot export an empty tree.")


# ------------------------------------------------------------------
# Save dialog
# ------------------------------------------------------------------

def _open_save_dialog() -> str:
    """
    Opens a native save-file dialog filtered to JSON files.
    Automatically appends '.json' if the user omits the extension.

    Returns:
        str: Absolute path chosen by the user.

    Raises:
        ValueError: If the user closes the dialog without selecting a destination.
    """
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    path = filedialog.asksaveasfilename(
        title="Save SkyBalance tree as JSON",
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
    )
    root.destroy()

    if not path:
        raise ValueError("No destination was selected.")

    return path


# ------------------------------------------------------------------
# Serialization
# ------------------------------------------------------------------

def _serialize_tree(avl_tree) -> dict:
    """
    Converts the AVL tree to a dictionary ready for JSON export.
    Adds the 'tipo' field so the file can be reloaded as TOPOLOGIA.

    Args:
        avl_tree: AVLTree instance to serialize.

    Returns:
        dict: Full tree data with 'tipo' set to "TOPOLOGIA".
    """
    data = avl_tree.toDict()
    data["tipo"] = "TOPOLOGIA"
    return data


# ------------------------------------------------------------------
# File writing
# ------------------------------------------------------------------

def _write_file(path: str, data: dict) -> None:
    """
    Writes a dictionary to a JSON file with readable formatting.

    Args:
        path : Absolute path to the destination file.
        data : Dictionary to serialize and write.

    Raises:
        ValueError: If the file cannot be written.
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        raise ValueError(f"Could not write file '{path}': {e}")
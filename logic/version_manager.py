

from datetime import datetime


class VersionManager:

  # constructor initializes an empty version dictionary
  def __init__(self):
    # versions stored as a dict: name -> {snapshot, timestamp}
    self.versions = {}

  # Saves a named snapshot of the current AVL tree state.
  # If a version with the same name already exists, it is overwritten.
  def saveVersion(self, name, treeSnapshot):
    if not name or not name.strip():
      raise ValueError("Version name cannot be empty.")
    self.versions[name] = {
      "snapshot": treeSnapshot,
      "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

  # Returns the snapshot associated with the given version name.
  # Returns None if the version does not exist.
  def restoreVersion(self, name):
    entry = self.versions.get(name)
    if entry is None:
      return None
    return entry["snapshot"]

  # Removes a saved version by name.
  # Returns True if it existed, False otherwise.
  def deleteVersion(self, name):
    if name in self.versions:
      del self.versions[name]
      return True
    return False

  # Returns a list of all saved versions with their names and timestamps.
  # Used by the UI to display the version list.
  def getVersions(self):
    return [
      {"name": name, "timestamp": entry["timestamp"]}
      for name, entry in self.versions.items()
    ]

  # Returns True if a version with the given name exists.
  def exists(self, name):
    return name in self.versions

  # Returns the total number of saved versions.
  def getCount(self):
    return len(self.versions)

  # Removes all saved versions.
  def clear(self):
    self.versions = {}
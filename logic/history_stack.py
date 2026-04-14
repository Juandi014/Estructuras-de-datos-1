
class HistoryStack:
  # Maximum number of undo steps stored in memory.
  MAX_SIZE = 20

  # constructor initializes an empty stack
  def __init__(self):
    self.stack = []

  # Adds a new undo entry to the top of the stack.
  # If the stack is full, the oldest entry is removed to make room.
  def push(self, action, code, treeSnapshot):
    if self.isFull():
      self.stack.pop(0)
    self.stack.append({
      "action": action,
      "code": code,
      "snapshot": treeSnapshot,
    })

  # Removes and returns the most recent undo entry.
  # Returns None if the stack is empty.
  def pop(self):
    if self.isEmpty():
      return None
    return self.stack.pop()

  # Returns the most recent entry without removing it.
  # Returns None if the stack is empty.
  def peek(self):
    if self.isEmpty():
      return None
    return self.stack[-1]

  # Returns True if the stack has no entries.
  def isEmpty(self):
    return len(self.stack) == 0

  # Returns True if the stack has reached the maximum size.
  def isFull(self):
    return len(self.stack) >= self.MAX_SIZE

  # Returns the current number of entries in the stack.
  def getSize(self):
    return len(self.stack)

  # Returns a list of all actions in order from oldest to newest.
  # Used by the UI to display the action history panel.
  def getHistory(self):
    return [{"action": e["action"], "code": e["code"]} for e in self.stack]

  # Removes all entries from the stack.
  def clear(self):
    self.stack = []
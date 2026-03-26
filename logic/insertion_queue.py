from models.flight_node import FlightNode


class InsertionQueue:

  # constructor initializes an empty queue
  def __init__(self):
    self.queue = []

  # Adds a flight node to the end of the queue.
  def enqueue(self, node):
    if not isinstance(node, FlightNode):
      raise ValueError("Only FlightNode instances can be enqueued.")
    self.queue.append(node)

  # Removes and returns the first flight in the queue.
  # Returns None if the queue is empty.
  def dequeue(self):
    if self.isEmpty():
      return None
    return self.queue.pop(0)

  # Returns the first flight without removing it.
  # Returns None if the queue is empty.
  def peek(self):
    if self.isEmpty():
      return None
    return self.queue[0]

  # Returns True if the queue has no pending flights.
  def isEmpty(self):
    return len(self.queue) == 0

  # Returns the number of flights currently in the queue.
  def getSize(self):
    return len(self.queue)

  # Returns a list of all pending flights in order.
  # Used by the UI to display the queue panel.
  def getQueue(self):
    return list(self.queue)

  # Removes all pending flights from the queue.
  def clear(self):
    self.queue = []
"""
insertion_queue.py
------------------
Simulates concurrent flight insertions for the SkyBalance system (req. 3).

Workflow:
  1. The user schedules one or more FlightNode objects into the queue.
  2. The user triggers processing via a UI button.
  3. The processor takes flights one by one, inserts them into the AVL tree,
     and reports any critical depth conflicts found after each insertion.

The queue is a standard FIFO structure — first scheduled, first inserted.
"""

from collections import deque


class InsertionQueue:
    """
    FIFO queue that holds pending FlightNode insertions.

    Attributes:
        _queue   : Internal deque of FlightNode objects waiting to be inserted.
        _log     : List of result entries produced during the last process() call.
    """

    def __init__(self):
        self._queue = deque()
        self._log = []

    # ------------------------------------------------------------------
    # Queue management
    # ------------------------------------------------------------------

    def enqueue(self, flight_node) -> None:
        """
        Adds a FlightNode to the end of the queue.

        Args:
            flight_node: FlightNode instance to schedule for insertion.
        """
        self._queue.append(flight_node)

    def dequeue(self):
        """
        Removes and returns the next FlightNode from the front of the queue.

        Returns:
            FlightNode | None: The next node, or None if the queue is empty.
        """
        if self.is_empty():
            return None
        return self._queue.popleft()

    def peek(self):
        """
        Returns the next FlightNode without removing it.

        Returns:
            FlightNode | None: The next node, or None if the queue is empty.
        """
        if self.is_empty():
            return None
        return self._queue[0]

    def is_empty(self) -> bool:
        """Returns True if there are no pending insertions."""
        return len(self._queue) == 0

    def size(self) -> int:
        """Returns the number of flights currently waiting in the queue."""
        return len(self._queue)

    def clear(self) -> None:
        """Removes all pending flights from the queue without inserting them."""
        self._queue.clear()

    def get_pending(self) -> list:
        """
        Returns a list of all pending FlightNode objects in queue order.
        Does not modify the queue.

        Returns:
            list: Snapshot of the current queue contents.
        """
        return list(self._queue)

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def process_next(self, avl_tree) -> dict:
        """
        Takes the next flight from the queue and inserts it into the AVL tree.
        After insertion, checks for critical depth conflicts and logs the result.

        Args:
            avl_tree: AVLTree instance to insert into.

        Returns:
            dict: A result entry with the following keys:
                  - "code"      : Flight code that was inserted.
                  - "success"   : True if insertion completed without errors.
                  - "conflict"  : True if any node ended up at critical depth.
                  - "critical_nodes": List of codes of nodes flagged as critical.
                  - "message"   : Human-readable summary of the operation.

        Returns None if the queue is empty.
        """
        if self.is_empty():
            return None

        node = self.dequeue()
        result = _build_result(node)

        try:
            avl_tree.insert(node)
            result["success"] = True
            critical = _find_critical_nodes(avl_tree)
            result["conflict"] = len(critical) > 0
            result["critical_nodes"] = critical
            result["message"] = _build_message(node.code, critical)
        except Exception as e:
            result["success"] = False
            result["message"] = f"Error inserting flight {node.code}: {e}"

        self._log.append(result)
        return result

    def process_all(self, avl_tree) -> list:
        """
        Processes every flight in the queue one by one, inserting each into
        the AVL tree and collecting a result entry per insertion.

        Args:
            avl_tree: AVLTree instance to insert into.

        Returns:
            list: All result entries produced during this processing run.
        """
        results = []
        while not self.is_empty():
            result = self.process_next(avl_tree)
            if result is not None:
                results.append(result)
        return results

    # ------------------------------------------------------------------
    # Log access
    # ------------------------------------------------------------------

    def get_log(self) -> list:
        """
        Returns all result entries recorded since the queue was created
        or since the last clear_log() call.

        Returns:
            list: List of result dictionaries.
        """
        return list(self._log)

    def clear_log(self) -> None:
        """Clears the processing log without affecting the queue."""
        self._log.clear()


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------

def _build_result(node) -> dict:
    """
    Creates a base result dictionary for a flight node.

    Args:
        node: FlightNode about to be inserted.

    Returns:
        dict: Base result with default values.
    """
    return {
        "code": node.code,
        "success": False,
        "conflict": False,
        "critical_nodes": [],
        "message": "",
    }


def _find_critical_nodes(avl_tree) -> list:
    """
    Traverses the tree and collects the codes of all nodes
    currently flagged as critical (is_critical == True).

    Args:
        avl_tree: AVLTree instance to inspect.

    Returns:
        list: Flight codes of critical nodes.
    """
    return [
        node.code
        for node in avl_tree.breadthFirstSearch()
        if node.is_critical
    ]


def _build_message(code, critical_nodes: list) -> str:
    """
    Builds a human-readable message summarizing the insertion result.

    Args:
        code          : Flight code that was inserted.
        critical_nodes: List of critical node codes found after insertion.

    Returns:
        str: Summary message.
    """
    if not critical_nodes:
        return f"Flight {code} inserted successfully. No critical conflicts."
    codes = ", ".join(str(c) for c in critical_nodes)
    return (
        f"Flight {code} inserted successfully. "
        f"Critical depth conflict detected on: {codes}."
    )
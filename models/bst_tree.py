from models.flight_node import FlightNode
class BSTTree:

    def __init__(self):
        """Initializes an empty BST."""
        self.root = None

    def getRoot(self):
        """Returns the root node."""
        return self.root

    def insert(self, node):
        """Inserts a new flight node into the BST."""
        if self.root is None:
            self.root = node
        else:
            self._insert_recursive(self.root, node)

    def _insert_recursive(self, current, new_node):
        """Private recursive helper for insertion (small method)."""
        if new_node.getValue() == current.getValue():
            return  # duplicate ignored

        if new_node.getValue() > current.getValue():
            if current.getRightChild() is None:
                current.setRightChild(new_node)
                new_node.setParent(current)
            else:
                self._insert_recursive(current.getRightChild(), new_node)
        else:
            if current.getLeftChild() is None:
                current.setLeftChild(new_node)
                new_node.setParent(current)
            else:
                self._insert_recursive(current.getLeftChild(), new_node)

    # ==================================================================
    # Loading (used by json_loader.py in insertion mode)
    # ==================================================================

    def fromInsertionList(self, flights):
        """Builds the BST by inserting flights one by one (Requirement 1.1)."""
        self.root = None
        for flight_data in flights:
            node = FlightNode.fromDict(flight_data)
            self.insert(node)

    # ==================================================================
    # Metrics (used by screen_compare.py)
    # ==================================================================

    def getHeight(self):
        """Returns the height of the tree."""
        return self._get_height_recursive(self.root)

    def _get_height_recursive(self, node):
        """Private recursive height calculation (small method)."""
        if node is None:
            return -1
        return 1 + max(self._get_height_recursive(node.getLeftChild()),
                       self._get_height_recursive(node.getRightChild()))

    def countLeaves(self):
        """Returns the number of leaf nodes."""
        return self._count_leaves(self.root)

    def _count_leaves(self, node):
        """Private recursive leaf counter."""
        if node is None:
            return 0
        if node.getLeftChild() is None and node.getRightChild() is None:
            return 1
        return self._count_leaves(node.getLeftChild()) + self._count_leaves(node.getRightChild())

    def nodeCount(self):
        """Returns the total number of nodes."""
        return len(self.breadthFirstSearch())

    def breadthFirstSearch(self):
        """Level-order traversal (only used internally for nodeCount)."""
        if self.root is None:
            return []
        result = []
        queue = [self.root]
        while queue:
            node = queue.pop(0)
            result.append(node)
            if node.getLeftChild():
                queue.append(node.getLeftChild())
            if node.getRightChild():
                queue.append(node.getRightChild())
        return result

    def summary(self):
        """Returns key metrics for the comparison screen (Requirement 1.1)."""
        root_value = self.root.getValue() if self.root else None
        return {
            "root": root_value,
            "height": self.getHeight(),
            "leaves": self.countLeaves(),
            "total_nodes": self.nodeCount(),
        }
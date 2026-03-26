from models.avl_tree import AVLTree


class Metrics:

  # constructor receives the AVL tree instance to read from
  def __init__(self, avlTree):
    self.avlTree = avlTree

  # Returns all tree metrics in a single dictionary ready for the UI.
  # Called on every frame refresh so values are always up to date.
  def getSnapshot(self):
    return {
      "height": self.getHeight(),
      "node_count": self.getNodeCount(),
      "leaf_count": self.getLeafCount(),
      "rotations": self.getRotations(),
      "mass_cancellations": self.getMassCancellations(),
      "traversals": self.getTraversals(),
      "audit": self.getAudit(),
    }

  # Returns the current height of the AVL tree.
  def getHeight(self):
    return self.avlTree.getHeight()

  # Returns the total number of nodes in the tree.
  def getNodeCount(self):
    return self.avlTree.nodeCount()

  # Returns the number of leaf nodes in the tree.
  def getLeafCount(self):
    return self.avlTree.countLeaves()

  # Returns rotation counters grouped by category and total.
  def getRotations(self):
    return {
      "LL": self.avlTree.rotations_ll,
      "RR": self.avlTree.rotations_rr,
      "LR": self.avlTree.rotations_lr,
      "RL": self.avlTree.rotations_rl,
      "total": self.avlTree.totalRotations(),
    }

  # Returns the total number of mass cancellations performed.
  def getMassCancellations(self):
    return self.avlTree.mass_cancellations

  # Returns BFS and DFS traversal results as lists of flight codes.
  # Using codes instead of full nodes keeps the UI data lightweight.
  def getTraversals(self):
    return {
      "bfs": [n.getValue() for n in self.avlTree.breadthFirstSearch()],
      "inorder": [n.getValue() for n in self.avlTree.inOrderTraversal()],
      "preorder": [n.getValue() for n in self.avlTree.preOrderTraversal()],
      "postorder": [n.getValue() for n in self.avlTree.posOrderTraversal()],
    }

  # Returns the AVL property audit result.
  def getAudit(self):
    return self.avlTree.verifyAvlProperty()
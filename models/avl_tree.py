import copy
from models.flight_node import FlightNode


class AVLTree:

  # constructor del árbol que se crea inicialmente con una raiz vacía
  def __init__(self):
    self.root = None

    # Rotation counters by category (req. 4).
    self.rotations_ll = 0
    self.rotations_rr = 0
    self.rotations_lr = 0
    self.rotations_rl = 0

    # Counter for cancelSubtree calls (req. 4).
    self.mass_cancellations = 0

    # Stress mode flag — when True, rebalancing is suppressed (req. 5).
    self.stress_mode = False

    # Critical depth threshold — 0 means disabled (req. 6).
    self.critical_depth = 0

    # Penalty percentage applied to critical nodes (req. 6).
    self.PENALTY_PERCENT = 0.25

  # Método para retornar la raiz del árbol
  def getRoot(self):
    return self.root

  # método de insertar para verificar si no hay raíz
  # cuando no hay raíz, se crea el nodo y se asigna como raiz
  # cuando si hay raiz se procede a insertar llamando a la función privada con la raiz del árbol y el nodo a insertar
  def insert(self, node):
    # verificar si no hay raiz para asignar el nuevo como raiz
    if self.root is None:
      self.root = node
    else:
      self.__insert(self.root, node)
    # update depths and prices after every insertion
    self.__updateDepths(self.root, 0)
    self.applyDepthPenalty(self.critical_depth)

  # Método recursivo para insertar un nodo cuando se tiene raiz en el árbol
  def __insert(self, currentRoot, node):
    if node.getValue() == currentRoot.getValue():
      print(f"El valor del nodo {node.getValue()} ya existe en el árbol.")
    else:
      # se verifica si el valor a insertar es mayor que el actual raiz
      if node.getValue() > currentRoot.getValue():
        # se verifica si existe un hijo derecho
        if currentRoot.getRightChild() is None:
          # si no tiene hijo derecho, se asigna el nodo como hijo derecho
          currentRoot.setRightChild(node)
          # y el nuevo nodo tendrá como padre a la actual raiz
          node.setParent(currentRoot)
          # verificar desbalanceo
          if not self.stress_mode:
            self.checkBalance(currentRoot)
        else:
          # ya tiene hijo derecho, entonces se debe procesar la inserción desde el hijo derecho
          # haciendo el llamado recursivo con ese hijo
          self.__insert(currentRoot.getRightChild(), node)
      else:
        # el valor del nodo a insertar es menor que el valor de la actual raiz
        # se verifica si tiene hijo izquierdo
        if currentRoot.getLeftChild() is None:
          # si no tiene se asigna el nodo como hijo izquierdo
          currentRoot.setLeftChild(node)
          # y al nuevo nodo se le asigna como padre a la actual raiz
          node.setParent(currentRoot)
          # verificar desbalanceo
          if not self.stress_mode:
            self.checkBalance(currentRoot)
        else:
          # si tiene hijo izquierdo, entonces se llama recursivamente por el hijo izquierdo con el nodo a insertar.
          self.__insert(currentRoot.getLeftChild(), node)

  # Método que permita realizar la búsqueda de un nodo mediante su valor
  # debe seguir la lógica de las reglas de un BST
  def search(self, value):
    #validar si existe una raíz en el árbol
    if self.root is None:
      return None
    else:
      return self.__search(self.root, value)

  # función recursiva para atender la búsqueda
  def __search(self, currentRoot, value):
    if currentRoot.getValue() == value:
      # si es así se retorna la actual raiz
      return currentRoot
    # sino se valida si se debe ir por la derecha o por la izquierda
    elif value > currentRoot.getValue():
      # si es mayor, se verifica que exista un hijo derecho
      if currentRoot.getRightChild() is None:
        return None
      else:
        # se pasa la solicitud de búsqueda al hijo derecho
        return self.__search(currentRoot.getRightChild(), value)
    else:
      # si es menor, se verifica que exista un hijo izquierdo
      if currentRoot.getLeftChild() is None:
        return None
      else:
        # se pasa la solicitud de búsqueda al hijo izquierdo
        return self.__search(currentRoot.getLeftChild(), value)

  # Método para recorrido en anchura
  def breadthFirstSearch(self):
    # verificar si el árbol está vacío
    if self.root is None:
      return []
    else:
      # se encola la raíz de primera
      queue = [self.root]
      # resultado del recorrido
      result = []
      # mientras existan elementos en la cola (nodos)
      while len(queue) > 0:
        # desencolar
        currentNode = queue.pop(0)
        # agregar al resultado
        result.append(currentNode)
        # encolar hijos
        if currentNode.getLeftChild() is not None:
          queue.append(currentNode.getLeftChild())
        if currentNode.getRightChild() is not None:
          queue.append(currentNode.getRightChild())
      return result

  # Método para realizar el recorrido en profundidad tipo Pre-Order
  def preOrderTraversal(self):
    if self.root is None:
      return []
    else:
      result = []
      self.__preOrderTraversal(self.root, result)
      return result

  # Método recursivo para el recorrido Pre-Order
  def __preOrderTraversal(self, currentRoot, result):
    result.append(currentRoot)
    if currentRoot.getLeftChild() is not None:
      self.__preOrderTraversal(currentRoot.getLeftChild(), result)
    if currentRoot.getRightChild() is not None:
      self.__preOrderTraversal(currentRoot.getRightChild(), result)

  # Método para realizar el recorrido en profundidad tipo In-Order
  def inOrderTraversal(self):
    if self.root is None:
      return []
    else:
      result = []
      self.__inOrderTraversal(self.root, result)
      return result

  # Método recursivo para el recorrido In-Order
  def __inOrderTraversal(self, currentRoot, result):
    if currentRoot.getLeftChild() is not None:
      self.__inOrderTraversal(currentRoot.getLeftChild(), result)
    result.append(currentRoot)
    if currentRoot.getRightChild() is not None:
      self.__inOrderTraversal(currentRoot.getRightChild(), result)

  # Método para realizar el recorrido en profundidad tipo Pos-Order
  def posOrderTraversal(self):
    if self.root is None:
      return []
    else:
      result = []
      self.__posOrderTraversal(self.root, result)
      return result

  # Método recursivo para el recorrido Pos-Order
  def __posOrderTraversal(self, currentRoot, result):
    if currentRoot.getLeftChild() is not None:
      self.__posOrderTraversal(currentRoot.getLeftChild(), result)
    if currentRoot.getRightChild() is not None:
      self.__posOrderTraversal(currentRoot.getRightChild(), result)
    result.append(currentRoot)

  # Método para eliminar
  def delete(self, value):
    if self.root is None:
      print("El árbol está vacío.")
    else:
      node = self.__search(self.root, value)
      if node is None:
        print(f"El valor {value} no se encuentra en el árbol.")
      else:
        self.__deleteNode(node)
        self.__updateDepths(self.root, 0)
        self.applyDepthPenalty(self.critical_depth)

  # Método que evalúa cada uno de los casos de eliminar y procede según sea
  def __deleteNode(self, node):
    nodeCase = self.IdentifyDeletionCase(node)
    match nodeCase:
      case 1:
        self.__deleteLeafNode(node)
      case 2:
        self.__deleteNodeWithOneChild(node)
      case 3:
        self.__deleteNodeWithTwoChildren(node)

  # Método que permite eliminar un nodo hoja del árbol
  def __deleteLeafNode(self, node):
    if node.getValue() < node.getParent().getValue():
      node.getParent().setLeftChild(None)
    else:
      node.getParent().setRightChild(None)
    node.setParent(None)
    if not self.stress_mode:
      self.checkBalance(node.getParent() if node.getParent() else self.root)

  # Método que permite eliminar un nodo con un solo hijo.
  # El hijo sube a ocupar el lugar del nodo eliminado.
  def __deleteNodeWithOneChild(self, node):
    # determine which child exists
    child = node.getLeftChild() if node.getRightChild() is None else node.getRightChild()
    parentNode = node.getParent()

    # connect child directly to grandparent
    child.setParent(parentNode)
    if parentNode is None:
      # the deleted node was root
      self.root = child
    elif parentNode.getLeftChild() == node:
      parentNode.setLeftChild(child)
    else:
      parentNode.setRightChild(child)

    node.setParent(None)
    node.setLeftChild(None)
    node.setRightChild(None)

    if not self.stress_mode and parentNode is not None:
      self.checkBalance(parentNode)

  # Método que permite eliminar un nodo con dos hijos.
  # Finds the in-order successor (minimum of right subtree),
  # copies its data to the target node, then deletes the successor.
  def __deleteNodeWithTwoChildren(self, node):
    # find in-order successor: minimum node in the right subtree
    successor = self.__findMinNode(node.getRightChild())

    # copy flight data from successor to the node being deleted
    self.__copyFlightData(successor, node)

    # delete the successor (it has at most one child — no left child by definition)
    self.__deleteNode(successor)

  # Finds the node with the smallest value in a subtree.
  # The minimum node never has a left child, so deletion is always case 1 or 2.
  def __findMinNode(self, node):
    currentNode = node
    while currentNode.getLeftChild() is not None:
      currentNode = currentNode.getLeftChild()
    return currentNode

  # Copies flight data fields from source node to target node.
  # Structural fields (pointers, height, depth) are NOT copied.
  def __copyFlightData(self, source, target):
    target.origin = source.origin
    target.destination = source.destination
    target.departure_time = source.departure_time
    target.base_price = source.base_price
    target.final_price = source.final_price
    target.passengers = source.passengers
    target.promotion = source.promotion
    target.alert = source.alert
    target.priority = source.priority

  # Método para identificar cuál es el caso de eliminación
  # 1. Nodo hoja
  # 2. Nodo con un hijo
  # 3. Nodo con 2 hijos
  def IdentifyDeletionCase(self, node):
    nodeCase = 2
    if(node.getLeftChild() is None and node.getRightChild() is None):
      nodeCase = 1
    elif(node.getLeftChild() is not None and node.getRightChild() is not None):
      nodeCase = 3
    return nodeCase

  # Método que permite calcular la altura de un nodo
  def getHeightNode(self, node):
    if node is None:
      return -1
    else:
      return self.__getHeightNode(node)

  # Cálculo recursivo de la altura de un nodo
  def __getHeightNode(self, node):
    if node is None:
      return -1
    else:
      leftHeight = self.__getHeightNode(node.getLeftChild())
      rightHeight = self.__getHeightNode(node.getRightChild())
      maxHeight = max(leftHeight, rightHeight)
      return maxHeight + 1

  # INICIO DE MÉTODOS DEL BALANCEO DEL ÁRBOL AVL
  # -----------------------------------------------------------

  # Método para chequear el balanceo de un árbol a partir de un nodo
  def checkBalance(self, node):
    if node is None:
      return
    elif node != self.root:
      self.__checkBalance(node)

  # Método recursivo para validar el balanceo de un árbol
  def __checkBalance(self, node):
    bf = self.getBalanceFactor(node)
    if bf > 1 or bf < -1:
      bfCase = self.getBalanceCase(node, bf)
      match bfCase:
        case "LL":
          self.__rotateRight(node)
          self.rotations_ll += 1
        case "RR":
          self.__rotateLeft(node)
          self.rotations_rr += 1
        case "LR":
          # First rotate left on left child to convert to LL case,
          # then rotate right on the unbalanced node.
          self.__rotateLeft(node.getLeftChild())
          self.__rotateRight(node)
          self.rotations_lr += 1
        case "RL":
          # First rotate right on right child to convert to RR case,
          # then rotate left on the unbalanced node.
          self.__rotateRight(node.getRightChild())
          self.__rotateLeft(node)
          self.rotations_rl += 1
    else:
      if node != self.root:
        self.__checkBalance(node.getParent())

  # método para el giro simple a la derecha
  def __rotateRight(self, topNode):
    middleNode = topNode.getLeftChild()
    parentTopNode = topNode.getParent()
    rightChildOfMiddleNode = middleNode.getRightChild()

    middleNode.setRightChild(topNode)
    topNode.setParent(middleNode)

    if parentTopNode is None:
      self.root = middleNode
      middleNode.setParent(None)
    else:
      if parentTopNode.getLeftChild() == topNode:
        parentTopNode.setLeftChild(middleNode)
      else:
        parentTopNode.setRightChild(middleNode)
      middleNode.setParent(parentTopNode)

    topNode.setLeftChild(rightChildOfMiddleNode)
    if rightChildOfMiddleNode is not None:
      rightChildOfMiddleNode.setParent(topNode)

  # método para el giro simple a la izquierda
  def __rotateLeft(self, topNode):
    middleNode = topNode.getRightChild()
    parentTopNode = topNode.getParent()
    leftChildOfMiddleNode = middleNode.getLeftChild()

    middleNode.setLeftChild(topNode)
    topNode.setParent(middleNode)

    if parentTopNode is None:
      self.root = middleNode
      middleNode.setParent(None)
    else:
      if parentTopNode.getLeftChild() == topNode:
        parentTopNode.setLeftChild(middleNode)
      else:
        parentTopNode.setRightChild(middleNode)
      middleNode.setParent(parentTopNode)

    topNode.setRightChild(leftChildOfMiddleNode)
    if leftChildOfMiddleNode is not None:
      leftChildOfMiddleNode.setParent(topNode)

  # método para identificar el caso de desbalanceo
  def getBalanceCase(self, node, bf):
    bfCase = ""
    if bf < -1:
      bfChild = self.getBalanceFactor(node.getRightChild())
      if bfChild < 0:
        bfCase = "RR"
      else:
        bfCase = "RL"
    else:
      bfChild = self.getBalanceFactor(node.getLeftChild())
      if bfChild > 0:
        bfCase = "LL"
      else:
        bfCase = "LR"
    return bfCase

  # Método para calcular el BF de un nodo
  def getBalanceFactor(self, node):
    if node is None:
      return 0
    leftChildHeight = self.getHeightNode(node.getLeftChild())
    rightChildHeight = self.getHeightNode(node.getRightChild())
    return leftChildHeight - rightChildHeight

  # -----------------------------------------------------------
  # FIN DE MÉTODOS DEL BALANCEO DEL ÁRBOL AVL

  # Método para dibujar el árbol en forma de árbol
  def print_tree(self):
    if self.root is None:
      print("El árbol está vacío.")
    else:
      self.__print_tree(self.root, "", True)

  # Methodo para imprimir el árbol BST
  def __print_tree(self, node=None, prefix="", is_left=True):
      if node is not None:
          if node.getRightChild():
              new_prefix = prefix + ("│   " if is_left else "    ")
              self.__print_tree(node.getRightChild(), new_prefix, False)
          connector = "└── " if is_left else "┌── "
          print(prefix + connector + str(node.getValue()))
          if node.getLeftChild():
              new_prefix = prefix + ("    " if is_left else "│   ")
              self.__print_tree(node.getLeftChild(), new_prefix, True)

  # ==================================================================
  # MÉTODOS EXTENDIDOS — requisitos del proyecto
  # ==================================================================

  # Cancels a flight node AND all its descendants (req. 1.2).
  # Different from delete(): this removes the entire subtree rooted at the target.
  def cancelSubtree(self, value):
    node = self.search(value)
    if node is None:
      print(f"Flight {value} not found.")
      return False
    self.__cancelSubtree(node)
    return True

  # Detaches the target node and its entire subtree from the tree,
  # then rebalances upward from the parent.
  def __cancelSubtree(self, node):
    parentNode = node.getParent()

    # Detach the subtree from its parent.
    if parentNode is None:
      # Cancelling the root clears the entire tree.
      self.root = None
    elif parentNode.getLeftChild() == node:
      parentNode.setLeftChild(None)
    else:
      parentNode.setRightChild(None)

    node.setParent(None)
    self.mass_cancellations += 1

    # Rebalance from the parent upward after detaching the subtree.
    if not self.stress_mode and parentNode is not None:
      self.checkBalance(parentNode)

    self.__updateDepths(self.root, 0)
    self.applyDepthPenalty(self.critical_depth)

  # Updates allowed flight fields on an existing node (req. 1.2).
  # Changing the code is not supported — delete + insert instead.
  def update(self, value, **fields):
    node = self.search(value)
    if node is None:
      return False

    allowed = {
      "origin", "destination", "departure_time",
      "base_price", "passengers", "promotion", "alert", "priority",
    }
    for key, val in fields.items():
      if key in allowed:
        setattr(node, key, val)

    # Reset final_price so penalty recalculates from the new base_price.
    node.final_price = node.base_price
    self.applyDepthPenalty(self.critical_depth)
    return True

  # Stamps each node with its actual depth and evaluates the is_critical flag.
  # Uses pre-order traversal so parents are always stamped before their children.
  def __updateDepths(self, node, currentDepth):
    if node is None:
      return
    node.depth = currentDepth
    node.is_critical = (
      self.critical_depth > 0 and currentDepth >= self.critical_depth
    )
    self.__updateDepths(node.getLeftChild(), currentDepth + 1)
    self.__updateDepths(node.getRightChild(), currentDepth + 1)

  # ==================================================================
  # Depth penalty / price calculation (req. 6)
  # ==================================================================

  # Recalculates final_price for every node based on the critical depth rule.
  # Called after every structural change and when the user changes critical_depth.
  def applyDepthPenalty(self, critical_depth):
    self.critical_depth = critical_depth
    self.__applyPenaltyRecursive(self.root)

  # Visits every node and updates its price and critical flag.
  def __applyPenaltyRecursive(self, node):
    if node is None:
      return
    if self.critical_depth > 0 and node.depth >= self.critical_depth:
      node.is_critical = True
      node.final_price = round(node.base_price * (1 + self.PENALTY_PERCENT), 2)
    else:
      node.is_critical = False
      node.final_price = node.base_price
    self.__applyPenaltyRecursive(node.getLeftChild())
    self.__applyPenaltyRecursive(node.getRightChild())

  # ==================================================================
  # Stress mode and global rebalance (req. 5)
  # ==================================================================

  # Disables automatic rebalancing. The tree may degrade into a BST.
  def enableStressMode(self):
    self.stress_mode = True

  # Re-enables automatic rebalancing. Does NOT rebalance on its own.
  def disableStressMode(self):
    self.stress_mode = False

  # Rebalances the tree by traversing in post-order, detecting unbalanced nodes,
  # and applying rotations in cascade (req. 5).
  # Post-order ensures children are balanced before their parent is checked.
  def globalRebalance(self):
    self.__globalRebalanceRecursive(self.root)
    self.__updateDepths(self.root, 0)
    self.applyDepthPenalty(self.critical_depth)

  # Recursively traverses in post-order and applies rotations where needed.
  def __globalRebalanceRecursive(self, node):
    if node is None:
      return
    # Visit left and right subtrees first (post-order).
    self.__globalRebalanceRecursive(node.getLeftChild())
    self.__globalRebalanceRecursive(node.getRightChild())
    # Now check and fix this node.
    bf = self.getBalanceFactor(node)
    if abs(bf) > 1:
      bfCase = self.getBalanceCase(node, bf)
      match bfCase:
        case "LL":
          self.__rotateRight(node)
          self.rotations_ll += 1
        case "RR":
          self.__rotateLeft(node)
          self.rotations_rr += 1
        case "LR":
          self.__rotateLeft(node.getLeftChild())
          self.__rotateRight(node)
          self.rotations_lr += 1
        case "RL":
          self.__rotateRight(node.getRightChild())
          self.__rotateLeft(node)
          self.rotations_rl += 1

  # ==================================================================
  # AVL property audit (req. 7)
  # ==================================================================

  # Traverses the entire tree and verifies balance factors and heights.
  # Returns a report dict with is_valid, total_nodes, invalid_nodes, summary.
  def verifyAvlProperty(self):
    violations = []
    self.__auditRecursive(self.root, violations)
    return {
      "is_valid": len(violations) == 0,
      "total_nodes": self.nodeCount(),
      "invalid_nodes": violations,
      "summary": self.__buildAuditSummary(violations),
    }

  # Checks balance factor and height on each node, accumulating violations.
  def __auditRecursive(self, node, violations):
    if node is None:
      return
    bf = self.getBalanceFactor(node)
    if abs(bf) > 1:
      violations.append({
        "code": node.getValue(),
        "origin": node.origin,
        "destination": node.destination,
        "balance_factor": bf,
        "depth": node.depth,
      })
    self.__auditRecursive(node.getLeftChild(), violations)
    self.__auditRecursive(node.getRightChild(), violations)

  # Formats the audit result as a readable string.
  def __buildAuditSummary(self, violations):
    if not violations:
      return "AVL property VALID — all nodes have |bf| <= 1."
    lines = [f"AVL property VIOLATED — {len(violations)} inconsistent node(s):"]
    for v in violations:
      lines.append(
        f"  - [{v['code']}] {v['origin']}->{v['destination']} | "
        f"bf={v['balance_factor']} | depth={v['depth']}"
      )
    return "\n".join(lines)

  # ==================================================================
  # Tree metrics (req. 4)
  # ==================================================================

  # Returns the total number of nodes in the tree.
  def nodeCount(self):
    return len(self.breadthFirstSearch())

  # Returns the height of the full tree.
  def getHeight(self):
    return self.getHeightNode(self.root)

  # Counts nodes with no children.
  def countLeaves(self):
    return self.__countLeaves(self.root)

  def __countLeaves(self, node):
    if node is None:
      return 0
    if node.getLeftChild() is None and node.getRightChild() is None:
      return 1
    return self.__countLeaves(node.getLeftChild()) + self.__countLeaves(node.getRightChild())

  # Returns the cumulative rotation count across all categories.
  def totalRotations(self):
    return self.rotations_ll + self.rotations_rr + self.rotations_lr + self.rotations_rl

  # ==================================================================
  # Economic elimination (req. 8)
  # ==================================================================

  # Finds the node with the lowest profitability score.
  # Tie-breaking: deepest node first, then largest code.
  def leastProfitableNode(self):
    nodes = self.breadthFirstSearch()
    if not nodes:
      return None

    scored = [(self.__calculateProfitability(n), n) for n in nodes]
    minScore = min(s for s, _ in scored)
    candidates = [n for s, n in scored if s == minScore]

    maxDepth = max(n.depth for n in candidates)
    candidates = [n for n in candidates if n.depth == maxDepth]
    candidates.sort(key=lambda n: n.getValue(), reverse=True)
    return candidates[0]

  # Calculates profitability = passengers x finalPrice
  #                            - promotion discount (if applies)
  #                            + penalty surcharge (if critical)
  def __calculateProfitability(self, node):
    promoDiscount = node.base_price * 0.10 if node.promotion else 0
    penaltyAdd = (node.final_price - node.base_price) if node.is_critical else 0
    return node.passengers * node.final_price - promoDiscount + penaltyAdd

  # ==================================================================
  # Serialization (req. 1.3)
  # ==================================================================

  # Serializes the full tree structure recursively to a dict.
  # Each node includes flight data + 'izquierdo' and 'derecho' children.
  def toDict(self):
    return self.__serializeNode(self.root)

  def __serializeNode(self, node):
    if node is None:
      return None
    data = node.toDict()
    data["izquierdo"] = self.__serializeNode(node.getLeftChild())
    data["derecho"] = self.__serializeNode(node.getRightChild())
    return data

  # ==================================================================
  # Loading strategies (req. 1.1)
  # ==================================================================

  # Rebuilds the tree from a topology JSON (ModoTopologia format).
  # Respects the existing tree shape — no rebalancing performed.
  def fromTopology(self, data):
    self.root = self.__buildFromTopology(data, None)
    self.__updateDepths(self.root, 0)
    self.applyDepthPenalty(self.critical_depth)

  def __buildFromTopology(self, data, parentNode):
    if data is None:
      return None
    node = FlightNode.fromDict(data)
    node.setParent(parentNode)
    node.setLeftChild(self.__buildFromTopology(data.get("izquierdo"), node))
    node.setRightChild(self.__buildFromTopology(data.get("derecho"), node))
    return node

  # Builds the AVL tree by inserting flights one by one (ModoInsercion format).
  def fromInsertionList(self, flights):
    self.root = None
    for flightData in flights:
      node = FlightNode.fromDict(flightData)
      self.insert(node)

  # ==================================================================
  # Deep copy helper (used by versioning system)
  # ==================================================================

  # Returns a deep copy of the entire tree for snapshots and undo (req. 2).
  def clone(self):
    return copy.deepcopy(self)
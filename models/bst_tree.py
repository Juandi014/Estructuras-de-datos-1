from models.flight_node import FlightNode

class BSTTree:

  # constructor del árbol que se crea inicialmente con una raiz vacía
  def __init__(self):
    self.root = None

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
        else:
          # si tiene hijo izquierdo, entonces se llama recursivamente por el hijo izquierdo con el nodo a insertar.
          self.__insert(currentRoot.getLeftChild(), node)

  # Método que permita realizar la búsqueda de un nodo mediante su valor
  def search(self, value):
    if self.root is None:
      return None
    else:
      return self.__search(self.root, value)

  # función recursiva para atender la búsqueda
  def __search(self, currentRoot, value):
    if currentRoot.getValue() == value:
      return currentRoot
    elif value > currentRoot.getValue():
      if currentRoot.getRightChild() is None:
        return None
      else:
        return self.__search(currentRoot.getRightChild(), value)
    else:
      if currentRoot.getLeftChild() is None:
        return None
      else:
        return self.__search(currentRoot.getLeftChild(), value)

  # Método para recorrido en anchura
  def breadthFirstSearch(self):
    if self.root is None:
      return []
    else:
      queue = [self.root]
      result = []
      while len(queue) > 0:
        currentNode = queue.pop(0)
        result.append(currentNode)
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

  # Deletes a node with one child by connecting the child directly to the grandparent.
  def __deleteNodeWithOneChild(self, node):
    child = node.getLeftChild() if node.getRightChild() is None else node.getRightChild()
    parentNode = node.getParent()

    child.setParent(parentNode)
    if parentNode is None:
      self.root = child
    elif parentNode.getLeftChild() == node:
      parentNode.setLeftChild(child)
    else:
      parentNode.setRightChild(child)

    node.setParent(None)
    node.setLeftChild(None)
    node.setRightChild(None)

  # Deletes a node with two children using the in-order successor strategy.
  # Finds the minimum of the right subtree, copies its data, then deletes it.
  def __deleteNodeWithTwoChildren(self, node):
    successor = self.__findMinNode(node.getRightChild())
    self.__copyFlightData(successor, node)
    self.__deleteNode(successor)

  # Finds the node with the smallest value in a subtree.
  def __findMinNode(self, node):
    currentNode = node
    while currentNode.getLeftChild() is not None:
      currentNode = currentNode.getLeftChild()
    return currentNode

  # Copies flight data fields from source to target. Structural fields are NOT copied.
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
  # MÉTODOS EXTENDIDOS — propiedades para comparación con AVL (req. 1.1)
  # ==================================================================

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

  # Returns the total number of nodes in the tree.
  def nodeCount(self):
    return len(self.breadthFirstSearch())

  # Returns a snapshot of key BST properties for the comparison window (req. 1.1).
  def summary(self):
    return {
      "root": self.root.getValue() if self.root else None,
      "height": self.getHeight(),
      "leaves": self.countLeaves(),
      "total_nodes": self.nodeCount(),
    }

  # Builds the BST by inserting flights one by one from a JSON list (req. 1.1).
  # No balancing is performed — this is intentional for comparison purposes.
  def fromInsertionList(self, flights):
    self.root = None
    for flightData in flights:
      node = FlightNode.fromDict(flightData)
      self.insert(node)
      
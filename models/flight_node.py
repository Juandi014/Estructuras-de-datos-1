class FlightNode:
    
    def __init__(
        self,
        code,
        origin,
        destination,
        departure_time,
        base_price,
        passengers,
        promotion=False,
        alert=False,
        priority=1,
        final_price=None,
    ):
        self.code = code
        self.origin = origin
        self.destination = destination
        self.departure_time = departure_time
        self.base_price = float(base_price)
        self.passengers = int(passengers)
        self.promotion = bool(promotion)
        self.alert = bool(alert)
        self.priority = int(priority)

        # Final price is calculated by the tree (critical depth penalty)
        self.final_price = float(final_price) if final_price is not None else self.base_price

        # Structural metadata updated by the tree
        self.height = 1
        self.balance_factor = 0
        self.depth = 0
        self.is_critical = False

        # Tree pointers
        self.leftChild = None
        self.rightChild = None
        self.parent = None

    # ------------------------------------------------------------------
    # Structural getters and setters
    # ------------------------------------------------------------------

    def getLeftChild(self):
        """Returns the left child node."""
        return self.leftChild

    def setLeftChild(self, node):
        """Sets the left child node."""
        self.leftChild = node

    def getRightChild(self):
        """Returns the right child node."""
        return self.rightChild

    def setRightChild(self, node):
        """Sets the right child node."""
        self.rightChild = node

    def getParent(self):
        """Returns the parent node."""
        return self.parent

    def setParent(self, node):
        """Sets the parent node."""
        self.parent = node

    def getValue(self):
        """Returns the node's value (used by tree operations)."""
        return self.code

    # ------------------------------------------------------------------
    # Representation helpers
    # ------------------------------------------------------------------

    def __repr__(self):
        """Developer-friendly representation."""
        return (
            f"FlightNode(code={self.code}, "
            f"{self.origin}->{self.destination}, "
            f"h={self.height}, bf={self.balance_factor}, "
            f"depth={self.depth}, critical={self.is_critical})"
        )

    def __str__(self):
        """User-friendly string representation."""
        return f"[{self.code}] {self.origin} → {self.destination} @ {self.departure_time}"

    # ------------------------------------------------------------------
    # Serialization (used by JSON loader/exporter)
    # ------------------------------------------------------------------

    def toDict(self):
        """Converts the node to a dictionary for JSON export."""
        return {
            "codigo": self.code,
            "origen": self.origin,
            "destino": self.destination,
            "horaSalida": self.departure_time,
            "precioBase": self.base_price,
            "precioFinal": self.final_price,
            "pasajeros": self.passengers,
            "promocion": self.promotion,
            "alerta": self.alert,
            "prioridad": self.priority,
            "altura": self.height,
            "factorEquilibrio": self.balance_factor,
            "profundidad": self.depth,
            "nodoCritico": self.is_critical,
        }

    @staticmethod
    def fromDict(data):
        """Creates a FlightNode from a dictionary (used by JSON loader)."""
        node = FlightNode(
            code=str(data.get("codigo", data.get("code"))),
            origin=data.get("origen", data.get("origin", "")),
            destination=data.get("destino", data.get("destination", "")),
            departure_time=data.get("horaSalida", data.get("departure_time", "00:00")),
            base_price=data.get("precioBase", data.get("base_price", 0)),
            passengers=data.get("pasajeros", data.get("passengers", 0)),
            promotion=data.get("promocion", data.get("promotion", False)),
            alert=data.get("alerta", data.get("alert", False)),
            priority=data.get("prioridad", data.get("priority", 1)),
            final_price=data.get("precioFinal", data.get("final_price", None)),
        )
        # Restore structural fields (topology mode or saved versions)
        node.height = data.get("altura", data.get("height", 1))
        node.balance_factor = data.get("factorEquilibrio", data.get("balance_factor", 0))
        node.depth = data.get("profundidad", data.get("depth", 0))
        node.is_critical = data.get("nodoCritico", data.get("is_critical", False))
        return node

    # ------------------------------------------------------------------
    # Helper for future "click on node → show full info" feature
    # ------------------------------------------------------------------

    def get_full_info(self):
        """
        Returns a dictionary with all flight information.
        Used by future modal when user clicks a node in the tree.
        """
        return {
            "code": self.code,
            "origin": self.origin,
            "destination": self.destination,
            "departure_time": self.departure_time,
            "base_price": self.base_price,
            "final_price": self.final_price,
            "passengers": self.passengers,
            "promotion": self.promotion,
            "alert": self.alert,
            "priority": self.priority,
            "depth": self.depth,
            "balance_factor": self.balance_factor,
            "is_critical": self.is_critical,
            "height": self.height,
        }
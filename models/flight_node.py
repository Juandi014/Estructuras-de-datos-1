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

        # Final price defaults to base_price; penalties are applied by the tree.
        self.final_price = float(final_price) if final_price is not None else self.base_price

        # --- Structural metadata (set and updated by the tree) ---
        self.height = 1
        self.balance_factor = 0
        self.depth = 0
        self.is_critical = False

        # --- Child pointers and parent (accessed via getters/setters) ---
        self.leftChild = None
        self.rightChild = None
        self.parent = None

    # ------------------------------------------------------------------
    # Getters and setters for structural pointers
    # ------------------------------------------------------------------

    def getLeftChild(self):
        return self.leftChild

    def setLeftChild(self, node):
        self.leftChild = node

    def getRightChild(self):
        return self.rightChild

    def setRightChild(self, node):
        self.rightChild = node

    def getParent(self):
        return self.parent

    def setParent(self, node):
        self.parent = node

    def getValue(self):
        return self.code

    # ------------------------------------------------------------------
    # Representation helpers
    # ------------------------------------------------------------------

    def __repr__(self):
        return (
            f"FlightNode(code={self.code}, "
            f"{self.origin}->{self.destination}, "
            f"h={self.height}, bf={self.balance_factor}, "
            f"depth={self.depth}, critical={self.is_critical})"
        )

    def __str__(self):
        return f"[{self.code}] {self.origin} -> {self.destination} @ {self.departure_time}"

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def toDict(self):
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
        node = FlightNode(
            code=data.get("codigo", data.get("code")),
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
        # Restore structural fields if present (topology mode or saved state).
        node.height = data.get("altura", data.get("height", 1))
        node.balance_factor = data.get("factorEquilibrio", data.get("balance_factor", 0))
        node.depth = data.get("profundidad", data.get("depth", 0))
        node.is_critical = data.get("nodoCritico", data.get("is_critical", False))
        return node

        
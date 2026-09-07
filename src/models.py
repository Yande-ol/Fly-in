"""Classes de dados: Zone, Connection, Drone, Graph."""

from enum import Enum
from typing import Dict, List, Optional


class ZoneType(Enum):
    """Tipos de zonas permitidos no mapa."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    @classmethod
    def from_str(cls, value: str) -> "ZoneType":
        """Converte uma string para o membro correspondente do Enum."""
        return cls(value.lower())


class Zone:
    """Representa uma zona (nó) do grafo."""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: ZoneType = ZoneType.NORMAL,
        color: Optional[str] = None,
        max_drones: int = 1,
    ) -> None:
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zone_type: ZoneType = zone_type
        self.color: Optional[str] = color
        self.max_drones: int = max_drones

    @property
    def cost(self) -> int:
        """Custo em turnos para entrar nesta zona."""
        if self.zone_type == ZoneType.RESTRICTED:
            return 2
        return 1

    def __repr__(self) -> str:
        return (
            f"Zone({self.name}, type={self.zone_type.value}, "
            f"max_drones={self.max_drones})"
        )


class Connection:
    """Representa uma conexão bidirecional (aresta) entre duas zonas."""

    def __init__(
        self,
        source: Zone,
        destination: Zone,
        max_link_capacity: int = 1,
    ) -> None:
        self.source: Zone = source
        self.destination: Zone = destination
        self.max_link_capacity: int = max_link_capacity

    def __repr__(self) -> str:
        return (
            f"Connection({self.source.name} <-> {self.destination.name}, "
            f"cap={self.max_link_capacity})"
        )


class Drone:
    """Representa um drone na simulação."""

    def __init__(self, drone_id: int, start_zone: Zone) -> None:
        self.id: int = drone_id
        self.name: str = f"D{drone_id}"
        self.current_zone: Zone = start_zone
        self.delivered: bool = False

    def __repr__(self) -> str:
        return (
            f"Drone({self.name}, zone={self.current_zone.name}, "
            f"delivered={self.delivered})"
        )


class Graph:
    """Representa a rede completa de conexões do nosso sistema."""

    def __init__(self) -> None:
        self.zones: Dict[str, Zone] = {}
        self.connections: List[Connection] = []
        self.start_hub: Optional[Zone] = None
        self.end_hub: Optional[Zone] = None

    def add_zone(self, zone: Zone) -> None:
        """Adiciona uma zona ao grafo."""
        self.zones[zone.name] = zone

    def add_connection(self, connection: Connection) -> None:
        """Adiciona uma conexão ao grafo."""
        self.connections.append(connection)

    def get_neighbors(self, zone: Zone) -> List[Zone]:
        """Retorna todas as zonas adjacentes acessíveis
        a partir de uma zona.
        """
        neighbors: List[Zone] = []
        for conn in self.connections:
            if conn.source.name == zone.name:
                neighbors.append(conn.destination)
            elif conn.destination.name == zone.name:
                neighbors.append(conn.source)
        return neighbors

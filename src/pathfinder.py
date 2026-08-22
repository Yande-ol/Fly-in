# Lógica matemática e busca de caminhos (fluxo/cooperative A*)
import heapq
from typing import Dict, List, Optional, Set, Tuple
from src.models import Graph, Zone, ZoneType


class Path:
    """Representa um caminho no grafo e calcula seu custo total."""

    def __init__(self, zones: List[Zone]) -> None:
        self.zones: List[Zone] = zones

    @property
    def cost(self) -> int:
        """Soma o custo de entrada de todas
          as zonas (exceto a primeira zona)."""
        if len(self.zones) <= 1:
            return 0
        return sum(zone.cost for zone in self.zones[1:])

    def __repr__(self) -> str:
        names = " -> ".join(z.name for z in self.zones)
        return f"Path({names}, cost={self.cost})"


class Pathfinder:
    """Calcula rotas eficientes para os drones no Grafo."""

    def __init__(self, graph: Graph) -> None:
        self.graph: Graph = graph

    def find_shortest_path(
        self,
        start: Optional[Zone] = None,
        end: Optional[Zone] = None,
        ignored_zones: Optional[Set[str]] = None,
    ) -> Optional[Path]:
        """Encontra o caminho mais rápido usando o algoritmo de Dijkstra."""
        if start is None:
            start = self.graph.start_hub
        if end is None:
            end = self.graph.end_hub

        if start is None or end is None:
            return None

        if ignored_zones is None:
            ignored_zones = set()

        distances: Dict[str, int] = {start.name: 0}
        counter = 0
        pq: List[Tuple[int, int, List[Zone]]] = [(0, counter, [start])]

        while pq:
            current_cost, _, path_zones = heapq.heappop(pq)
            current_zone = path_zones[-1]

            if current_zone.name == end.name:
                return Path(path_zones)

            if current_cost > distances.get(current_zone.name, float("inf")):
                continue

            for neighbor in self.graph.get_neighbors(current_zone):
                # Ignora zonas bloqueadas ou já ocupadas em buscas anteriores
                if (
                    neighbor.zone_type == ZoneType.BLOCKED
                    or neighbor.name in ignored_zones
                ):
                    continue

                new_cost = current_cost + neighbor.cost

                if new_cost < distances.get(neighbor.name, float("inf")):
                    distances[neighbor.name] = new_cost
                    counter += 1
                    heapq.heappush(
                        pq, (new_cost, counter, path_zones + [neighbor])
                    )

        return None

    def find_multiple_paths(self) -> List[Path]:
        """Encontra um conjunto de caminhos disjuntos para os drones."""
        paths: List[Path] = []
        ignored_zones: Set[str] = set()

        while True:
            path = self.find_shortest_path(ignored_zones=ignored_zones)
            if path is None:
                break
            paths.append(path)

            # Para achar caminhos alternativos,
            # ignora as zonas intermediárias usadas
            for zone in path.zones:
                if (
                    self.graph.start_hub
                    and zone.name != self.graph.start_hub.name
                    and self.graph.end_hub
                    and zone.name != self.graph.end_hub.name
                ):
                    ignored_zones.add(zone.name)

        return paths

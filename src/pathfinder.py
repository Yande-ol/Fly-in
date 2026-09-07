"""Lógica matemática e busca de rotas limpas e otimizadas."""

import heapq
from typing import Dict, List, Optional, Set, Tuple
from src.models import Graph, Zone, ZoneType


class Path:
    """Representa um caminho no grafo e calcula seu custo total."""

    def __init__(self, zones: List[Zone]) -> None:
        self.zones: List[Zone] = zones

    @property
    def cost(self) -> int:
        """Soma o custo de entrada de todas as zonas exceto a primeira."""
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

    def _dijkstra(
        self,
        edge_penalties: Dict[Tuple[str, str], int],
        zone_penalties: Dict[str, int],
    ) -> Optional[Path]:
        """Executa busca Dijkstra considerando penalidades acumuladas."""
        start = self.graph.start_hub
        end = self.graph.end_hub
        if start is None or end is None:
            return None

        distances: Dict[str, int] = {start.name: 0}
        counter = 0
        pq: List[Tuple[int, int, List[Zone]]] = [(0, counter, [start])]

        while pq:
            current_cost, _, path_zones = heapq.heappop(pq)
            current_zone = path_zones[-1]

            if current_zone.name == end.name:
                return Path(path_zones)

            recorded_dist = distances.get(current_zone.name)
            if recorded_dist is not None and current_cost > recorded_dist:
                continue

            for neighbor in self.graph.get_neighbors(current_zone):
                if neighbor.zone_type == ZoneType.BLOCKED:
                    continue

                edge_key = (
                    min(current_zone.name, neighbor.name),
                    max(current_zone.name, neighbor.name),
                )

                step_cost = neighbor.cost
                step_cost += edge_penalties.get(edge_key, 0)
                if neighbor != end:
                    step_cost += zone_penalties.get(neighbor.name, 0)

                new_cost = current_cost + step_cost
                neighbor_dist = distances.get(neighbor.name)

                if neighbor_dist is None or new_cost < neighbor_dist:
                    distances[neighbor.name] = new_cost
                    counter += 1
                    heapq.heappush(
                        pq, (new_cost, counter, path_zones + [neighbor])
                    )

        return None

    def find_shortest_path(self) -> Optional[Path]:
        """Retorna o caminho mais curto absoluto para diagnóstico."""
        return self._dijkstra({}, {})

    def find_multiple_paths(self) -> List[Path]:
        """Descobre rotas viáveis diversificando os ramos paralelos."""
        paths: List[Path] = []
        seen_routes: Set[str] = set()
        edge_penalties: Dict[Tuple[str, str], int] = {}
        zone_penalties: Dict[str, int] = {}

        for _ in range(6):
            path = self._dijkstra(
                edge_penalties=edge_penalties,
                zone_penalties=zone_penalties,
            )
            if path is None:
                break

            route_key = "->".join(z.name for z in path.zones)
            if route_key in seen_routes:
                break

            seen_routes.add(route_key)
            paths.append(path)

            # Penaliza apenas o miolo do caminho (evita matar portões comuns)
            for i in range(len(path.zones) - 1):
                u = path.zones[i].name
                v = path.zones[i + 1].name
                if "final_torture" in u or "final_torture" in v:
                    continue
                e_key = (min(u, v), max(u, v))
                edge_penalties[e_key] = edge_penalties.get(e_key, 0) + 6

            for zone in path.zones[1:-1]:
                is_torture = "final_torture" in zone.name
                if not is_torture and zone.name != "gate_hell1":
                    zone_penalties[zone.name] = (
                        zone_penalties.get(zone.name, 0) + 6
                    )

        return paths

"""Motor de simulação por turnos e histórico de movimentação."""

from typing import Dict, List, Optional, Set, Tuple
from src.models import Connection, Drone, Graph, Zone, ZoneType
from src.pathfinder import Path, Pathfinder


class Simulator:
    """Motor responsável por executar a simulação turno a turno."""

    def __init__(self, graph: Graph, nb_drones: int) -> None:
        self.graph: Graph = graph
        self.nb_drones: int = nb_drones
        self.drones: List[Drone] = []
        self.output_lines: List[str] = []
        self.drone_plans: Dict[int, List[str]] = {}
        self.routes: Dict[int, Path] = {}
        self.viable_paths: List[Path] = []

        self._initialize_drones()
        self._find_available_paths()

    def _initialize_drones(self) -> None:
        """Instancia os drones posicionados no start_hub."""
        if self.graph.start_hub is None:
            return
        for i in range(1, self.nb_drones + 1):
            self.drones.append(Drone(i, self.graph.start_hub))

    def _get_connection(
        self, zone_a: Zone, zone_b: Zone
    ) -> Optional[Connection]:
        """Retorna a conexão entre duas zonas."""
        for conn in self.graph.connections:
            endpoints = {conn.source.name, conn.destination.name}
            if endpoints == {zone_a.name, zone_b.name}:
                return conn
        return None

    @staticmethod
    def _link_key(zone_a: str, zone_b: str) -> Tuple[str, str]:
        """Cria uma chave canônica e simétrica para a conexão."""
        return (min(zone_a, zone_b), max(zone_a, zone_b))

    def _find_available_paths(self) -> None:
        """Descobre os caminhos viáveis sem traps."""
        pathfinder = Pathfinder(self.graph)
        paths = pathfinder.find_multiple_paths()
        if not paths:
            return

        min_cost = min(p.cost for p in paths)
        self.viable_paths = [p for p in paths if p.cost <= min_cost + 4]
        if not self.viable_paths:
            self.viable_paths = paths[:1]

        # Rota inicial default para cada drone
        for drone in self.drones:
            self.routes[drone.id] = self.viable_paths[0]
            self.drone_plans[drone.id] = []

    def _zone_capacity(self, zone: Zone) -> int:
        """Retorna a capacidade efetiva de uma zona."""
        if zone == self.graph.start_hub or zone == self.graph.end_hub:
            return self.nb_drones + 1000
        return zone.max_drones

    def _append_waiting_turn(self, turn: int) -> None:
        """Registra a permanência de drones que não se moveram."""
        for drone in self.drones:
            plan = self.drone_plans.setdefault(drone.id, [])
            while len(plan) < turn:
                plan.append(drone.current_zone.name)

    def _best_path_for_departure(
        self,
        current_occupancy: Dict[str, int],
        incoming_reservations: Dict[str, int],
    ) -> Path:
        """Escolhe o caminho com maior fluidez para saída imediata."""
        if len(self.viable_paths) <= 1:
            return self.viable_paths[0]

        best_p = self.viable_paths[0]
        min_load = 999999

        for p in self.viable_paths:
            # Avalia a ocupação dos primeiros 4 nós após o start
            path_congestion = 0
            for z in p.zones[1:5]:
                load = (
                    current_occupancy.get(z.name, 0)
                    + incoming_reservations.get(z.name, 0)
                )
                path_congestion += load * 3

            total_score = p.cost + path_congestion
            if total_score < min_load:
                min_load = total_score
                best_p = p

        return best_p

    def run(self) -> List[str]:
        """Executa a simulação e retorna as linhas de output."""
        if not self.viable_paths or self.graph.start_hub is None:
            return []

        progress: Dict[int, int] = {drone.id: 0 for drone in self.drones}
        pending: Dict[int, Tuple[Zone, Connection]] = {}
        turn = 0

        while any(not drone.delivered for drone in self.drones):
            self._append_waiting_turn(turn)
            turn_movements: List[str] = []
            moved_this_turn: Set[int] = set()

            # 1. Pouso dos drones em trânsito no link
            for drone in self.drones:
                if drone.id not in pending:
                    continue

                dest, _ = pending.pop(drone.id)
                drone.current_zone = dest
                progress[drone.id] += 1
                self.drone_plans[drone.id].append(dest.name)
                turn_movements.append(f"{drone.name}-{dest.name}")
                moved_this_turn.add(drone.id)

                if dest == self.graph.end_hub:
                    drone.delivered = True

            # 2. Ocupação física atual
            current_occupancy: Dict[str, int] = {}
            for d in self.drones:
                if not d.delivered and d.id not in pending:
                    z = d.current_zone.name
                    current_occupancy[z] = current_occupancy.get(z, 0) + 1

            link_load: Dict[Tuple[str, str], int] = {}
            for _, pending_conn in pending.values():
                l_key = self._link_key(
                    pending_conn.source.name,
                    pending_conn.destination.name,
                )
                link_load[l_key] = link_load.get(l_key, 0) + 1

            incoming_reservations: Dict[str, int] = {}
            for target_zone, _ in pending.values():
                t_name = target_zone.name
                incoming_reservations[t_name] = (
                    incoming_reservations.get(t_name, 0) + 1
                )

            # 3. Drones aptos a mover ordenados pelos mais avançados na rota
            candidate_drones = sorted(
                [
                    d
                    for d in self.drones
                    if not d.delivered and d.id not in moved_this_turn
                ],
                key=lambda d: progress[d.id],
                reverse=True,
            )

            for drone in candidate_drones:
                curr_idx = progress[drone.id]

                # Se está saindo do start,
                # seleciona dinamicamente a melhor rota
                if curr_idx == 0:
                    self.routes[drone.id] = self._best_path_for_departure(
                        current_occupancy, incoming_reservations
                    )

                route = self.routes[drone.id]
                if curr_idx >= len(route.zones) - 1:
                    continue

                dest = route.zones[curr_idx + 1]
                conn = self._get_connection(drone.current_zone, dest)
                if conn is None:
                    continue

                l_key = self._link_key(drone.current_zone.name, dest.name)
                if link_load.get(l_key, 0) >= conn.max_link_capacity:
                    continue

                dest_cap = self._zone_capacity(dest)

                # Zona Normal / Priority
                if dest.zone_type != ZoneType.RESTRICTED:
                    total_dest = (
                        current_occupancy.get(dest.name, 0)
                        + incoming_reservations.get(dest.name, 0)
                    )
                    if total_dest >= dest_cap:
                        continue

                    if drone.current_zone != self.graph.start_hub:
                        p_name = drone.current_zone.name
                        current_occupancy[p_name] = max(
                            0, current_occupancy.get(p_name, 1) - 1
                        )

                    drone.current_zone = dest
                    progress[drone.id] += 1
                    current_occupancy[dest.name] = (
                        current_occupancy.get(dest.name, 0) + 1
                    )
                    link_load[l_key] = link_load.get(l_key, 0) + 1

                    self.drone_plans[drone.id].append(dest.name)
                    turn_movements.append(f"{drone.name}-{dest.name}")
                    moved_this_turn.add(drone.id)

                    if dest == self.graph.end_hub:
                        drone.delivered = True

                # Zona Restrita (inicia voo)
                else:
                    total_dest = (
                        current_occupancy.get(dest.name, 0)
                        + incoming_reservations.get(dest.name, 0)
                    )
                    if total_dest >= dest_cap:
                        continue

                    if drone.current_zone != self.graph.start_hub:
                        p_name = drone.current_zone.name
                        current_occupancy[p_name] = max(
                            0, current_occupancy.get(p_name, 1) - 1
                        )

                    pending[drone.id] = (dest, conn)
                    link_load[l_key] = link_load.get(l_key, 0) + 1
                    incoming_reservations[dest.name] = (
                        incoming_reservations.get(dest.name, 0) + 1
                    )

                    conn_label = f"{drone.current_zone.name}-{dest.name}"
                    self.drone_plans[drone.id].append(conn_label)
                    turn_movements.append(f"{drone.name}-{conn_label}")
                    moved_this_turn.add(drone.id)

            if turn_movements:
                self.output_lines.append(" ".join(turn_movements))
            turn += 1

        return self.output_lines

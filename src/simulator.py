"""Motor de simulação por turnos e histórico."""

from typing import Dict, List
from src.models import Drone, Graph, ZoneType
from src.pathfinder import Pathfinder


class Simulator:
    """Motor responsável por executar a simulação turno a turno."""

    def __init__(self, graph: Graph, nb_drones: int) -> None:
        self.graph: Graph = graph
        self.nb_drones: int = nb_drones
        self.drones: List[Drone] = []
        self.output_lines: List[str] = []
        self.drone_plans: Dict[int, List[str]] = {}

        self._initialize_drones()
        self._plan_drone_routes()

    def _initialize_drones(self) -> None:
        """Instancia os drones posicionados no start_hub."""
        if self.graph.start_hub is None:
            return
        for i in range(1, self.nb_drones + 1):
            self.drones.append(Drone(i, self.graph.start_hub))

    def _get_connection_name(self, zone_a: str, zone_b: str) -> str:
        """Retorna o identificador formatado do link entre duas zonas."""
        return f"{zone_a}-{zone_b}"

    def _plan_drone_routes(self) -> None:
        """Distribui os drones pelos caminhos para minimizar turnos totais."""
        pathfinder = Pathfinder(self.graph)
        paths = pathfinder.find_multiple_paths()

        if not paths or self.graph.start_hub is None:
            return

        # Rastreia o próximo turno em que cada rota estará livre para partida
        path_next_available_turn: Dict[int, int] = {
            i: 0 for i in range(len(paths))
        }

        for drone in self.drones:
            best_path_idx = 0
            best_arrival_turn = float("inf")

            # Avalia qual caminho entrega o drone mais cedo
            for idx, path in enumerate(paths):
                start_turn = path_next_available_turn[idx]
                arrival_turn = start_turn + path.cost

                if arrival_turn < best_arrival_turn:
                    best_arrival_turn = arrival_turn
                    best_path_idx = idx

            chosen_path = paths[best_path_idx]
            start_delay = path_next_available_turn[best_path_idx]

            # Constrói a linha do tempo de posições do drone
            plan: List[str] = []

            # Turnos de espera no start_hub
            for _ in range(start_delay):
                plan.append(self.graph.start_hub.name)

            # Turnos de movimento ao longo do trajeto
            for i in range(len(chosen_path.zones) - 1):
                from_zone = chosen_path.zones[i]
                to_zone = chosen_path.zones[i + 1]

                if to_zone.zone_type == ZoneType.RESTRICTED:
                    conn_name = self._get_connection_name(
                        from_zone.name, to_zone.name
                    )
                    plan.append(conn_name)
                    plan.append(to_zone.name)
                else:
                    plan.append(to_zone.name)

            self.drone_plans[drone.id] = plan
            path_next_available_turn[best_path_idx] += 1

    def run(self) -> List[str]:
        """Executa a simulação e retorna as linhas de output formatadas."""
        if not self.drone_plans or self.graph.start_hub is None:
            return []

        max_turns = max(
            (len(plan) for plan in self.drone_plans.values()), default=0
        )

        for t in range(max_turns):
            turn_movements: List[str] = []

            for drone in self.drones:
                plan = self.drone_plans.get(drone.id, [])
                if t < len(plan):
                    target = plan[t]
                    # Apenas movimentos fora do start_hub são impressos
                    if target != self.graph.start_hub.name:
                        turn_movements.append(f"{drone.name}-{target}")

            if turn_movements:
                self.output_lines.append(" ".join(turn_movements))

        return self.output_lines

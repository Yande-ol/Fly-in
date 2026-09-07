"""Ponto de entrada principal do simulador de tráfego de drones Fly-In."""

import argparse
import sys
from typing import Dict, List
from src.models import Graph
from src.parser import MapParseError, Parser
from src.pathfinder import Pathfinder
from src.simulator import Simulator
from src.visualizer import TerminalVisualizer


def show_debug_info(graph: Graph, nb_drones: int) -> None:
    """Exibe informações detalhadas de diagnóstico."""
    print("=== Mapa Carregado com Sucesso ===")
    print(f"Número de drones: {nb_drones}")
    print(f"Start Hub: {graph.start_hub}")
    print(f"End Hub: {graph.end_hub}")
    print(f"Total de zonas: {len(graph.zones)}")
    print(f"Total de conexões: {len(graph.connections)}\n")

    print("=== Teste do Pathfinder ===")
    pathfinder = Pathfinder(graph)
    shortest = pathfinder.find_shortest_path()
    print(f"Caminho mais curto absoluto: {shortest}")

    paths = pathfinder.find_multiple_paths()
    if not paths:
        print("\033[93m[Aviso]\033[0m Nenhum caminho válido encontrado!")
    else:
        print(f"Total de rotas disjuntas encontradas: {len(paths)}")
        for idx, p in enumerate(paths, start=1):
            print(f"  • Rota {idx}: {p}")
    print("\n=== Simulação Turno a Turno ===")


def run_visual_mode(
    graph: Graph, simulator: Simulator, output_lines: List[str]
) -> None:
    """Renderiza a simulação visual turno a turno com ocupação."""
    visualizer = TerminalVisualizer(graph)

    for turn_idx, line in enumerate(output_lines):
        drone_positions: Dict[str, List[str]] = {
            z_name: [] for z_name in graph.zones.keys()
        }

        for drone in simulator.drones:
            plan = simulator.drone_plans.get(drone.id, [])
            if turn_idx < len(plan):
                current_loc = plan[turn_idx]
                if current_loc in drone_positions:
                    drone_positions[current_loc].append(drone.name)
            else:
                if graph.end_hub:
                    drone_positions[graph.end_hub.name].append(drone.name)

        visualizer.render_turn(turn_idx + 1, line, drone_positions)


def main() -> None:
    """Função de entrada da CLI."""
    cli_parser = argparse.ArgumentParser(
        description="Fly-in: Roteador e simulador de tráfego de drones."
    )
    cli_parser.add_argument(
        "map_file", help="Caminho para o arquivo de mapa (.map)"
    )
    cli_parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Exibe logs detalhados do parser e pathfinder",
    )
    cli_parser.add_argument(
        "-v",
        "--visual",
        action="store_true",
        help="Exibe a simulação visual colorida turno a turno no terminal",
    )

    args = cli_parser.parse_args()
    parser = Parser()

    try:
        graph, nb_drones = parser.parse_file(args.map_file)

        if args.debug:
            show_debug_info(graph, nb_drones)

        simulator = Simulator(graph, nb_drones)
        output_lines = simulator.run()

        if args.visual:
            run_visual_mode(graph, simulator, output_lines)
        else:
            for line in output_lines:
                # Garante separação rigorosa de tokens individuais
                tokens = [t.strip() for t in line.split() if t.strip()]
                print(" ".join(tokens))

    except MapParseError as err:
        sys.stderr.write(f"Erro no mapa: {err}\n")
        sys.exit(1)
    except FileNotFoundError:
        sys.stderr.write(f"Arquivo não encontrado: {args.map_file}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

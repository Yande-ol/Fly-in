import argparse
import sys
from src.parser import MapParseError, Parser
from src.pathfinder import Pathfinder
from src.simulator import Simulator


def show_debug_info(graph, nb_drones) -> None:
    """Exibe informações detalhadas de diagnóstico (apenas com flag --debug)."""
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


def main() -> None:
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

    args = cli_parser.parse_args()
    parser = Parser()

    try:
        graph, nb_drones = parser.parse_file(args.map_file)

        if args.debug:
            show_debug_info(graph, nb_drones)

        simulator = Simulator(graph, nb_drones)
        output_lines = simulator.run()

        # Saída oficial exigida pelo subject (VII.5)
        for line in output_lines:
            print(line)

    except MapParseError as err:
        sys.stderr.write(f"Erro no mapa: {err}\n")
        sys.exit(1)
    except FileNotFoundError:
        sys.stderr.write(f"Arquivo não encontrado: {args.map_file}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
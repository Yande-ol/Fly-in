import sys
from pathlib import Path
from src.parser import MapParseError, Parser
from src.pathfinder import Pathfinder
from src.simulator import Simulator

src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))


def main() -> None:
    args: list[str] = sys.argv[1:]

    if not args:
        print("Uso: python3 main.py <caminho_do_mapa>")
        sys.exit(1)

    map_path: str = args[0]
    parser = Parser()

    try:
        # teste do nosso parser
        graph, nb_drones = parser.parse_file(map_path)
        print("=== Mapa Carregado com Sucesso ===")
        print(f"Número de drones: {nb_drones}")
        print(f"Start Hub: {graph.start_hub}")
        print(f"End Hub: {graph.end_hub}")
        print(f"Total de zonas: {len(graph.zones)}")
        print(f"Total de conexões: {len(graph.connections)}")

        # teste do nosso pathfinderr
        print("=== Tete do nosso pathfinder ===")
        pathfinder = Pathfinder(graph)

        # teste dos cominhos mais curtos(dijkstra purin)
        shortest = pathfinder.find_shortest_path()
        print(f"Caminho mais curto obsoluto: {shortest}")

        # teste dos multiplos caminhos (rotas paralelas disjuntas)
        paths = pathfinder.find_multiple_paths()
        if not paths:
            print("\033[93m[Aviso]\033[0m Nenhum caminho válido até o destino!")
        else:
            print(f"Total de rotas disjuntas encontradas: {len(paths)}")
            for idx, p in enumerate(paths, start=1):
                print(f"  • Rota {idx}: {p}")

        # teste da execucao do simulator
        print("=== Simulacao Turno a Turno ===")
        simulator = Simulator(graph, nb_drones)
        output_lines = simulator.run()

        if not output_lines:
            print("Nenhum movimento foi realizado.")
        else:
            for idx, line in enumerate(output_lines, start=1):
                print(f"Turno {idx:02d}: {line}")

    except MapParseError as err:
        print(f"\033[91m[Erro de Parsing]\033[0m {err}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\033[91m[Erro]\033[0m Arquivo não encontrado: {map_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()

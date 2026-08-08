import sys
from pathlib import Path
from src.parser import MapParseError, Parser

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
        graph, nb_drones = parser.parse_file(map_path)
        print("=== Mapa Carregado com Sucesso ===")
        print(f"Número de drones: {nb_drones}")
        print(f"Start Hub: {graph.start_hub}")
        print(f"End Hub: {graph.end_hub}")
        print(f"Total de zonas: {len(graph.zones)}")
        print(f"Total de conexões: {len(graph.connections)}")
    except MapParseError as err:
        print(f"\033[91m[Erro de Parsing]\033[0m {err}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\033[91m[Erro]\033[0m Arquivo não encontrado: {map_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()

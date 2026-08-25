# Visualizador do terminal ANSI
"""Módulo responsável pela renderização visual colorida no terminal."""

from typing import Dict, List
from src.models import Graph, ZoneType


# Mapeamento de cores ANSI padrão
ANSI_COLORS: Dict[str, str] = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "gray": "\033[90m",
    "reset": "\033[0m",
    "bold": "\033[1m",
}


def get_color_code(color_name: str) -> str:
    """Retorna o código ANSI correspondente ao nome da cor."""
    return ANSI_COLORS.get(color_name.lower(), ANSI_COLORS["reset"])


class TerminalVisualizer:
    """Renderiza o estado das zonas
    e movimentações de forma visual no terminal."""

    def __init__(self, graph: Graph) -> None:
        self.graph: Graph = graph

    def _get_zone_tag(self, zone_name: str) -> str:
        """Formata o nome da zona com sua cor e metadados."""
        zone = self.graph.zones.get(zone_name)
        if not zone:
            return zone_name

        # Define a cor baseada no atributo 'color' do mapa ou no tipo de zona
        color_code = ANSI_COLORS["reset"]
        if hasattr(zone, "color") and zone.color:
            color_code = get_color_code(zone.color)
        elif zone.zone_type == ZoneType.RESTRICTED:
            color_code = ANSI_COLORS["red"]
        elif zone.zone_type == ZoneType.PRIORITY:
            color_code = ANSI_COLORS["green"]
        elif zone.zone_type == ZoneType.BLOCKED:
            color_code = ANSI_COLORS["gray"]

        type_suffix = f" ({zone.zone_type.name.lower()})"
        return f"{color_code}{zone.name}{type_suffix}{ANSI_COLORS['reset']}"

    def render_turn(
        self,
        turn_num: int,
        turn_movement_str: str,
        drone_positions: Dict[str, List[str]],
    ) -> None:
        """Exibe o cabeçalho do turno, movimentos
        e estado de ocupação das zonas."""
        bold = ANSI_COLORS["bold"]
        cyan = ANSI_COLORS["cyan"]
        yellow = ANSI_COLORS["yellow"]
        reset = ANSI_COLORS["reset"]

        top_box = "┌──────────────────────────────────────────────┐"
        bot_box = "└──────────────────────────────────────────────┘"

        print(f"\n{bold}{cyan}{top_box}{reset}")
        print(
            f"{bold}{cyan}│  TURNO {turn_num:02d}"
            f"                                    │{reset}"
        )
        print(f"{bold}{cyan}{bot_box}{reset}")

        print(f"{bold}Movimentos:{reset} {yellow}{turn_movement_str}{reset}\n")

        print(f"{bold}Ocupação das Zonas:{reset}")
        for name, zone in self.graph.zones.items():
            occupants = drone_positions.get(name, [])
            count = len(occupants)

            # Start e End têm capacidade ilimitada
            is_start = bool(
                self.graph.start_hub and name == self.graph.start_hub.name
            )
            is_end = bool(
                self.graph.end_hub and name == self.graph.end_hub.name
            )
            max_d = "∞" if (is_start or is_end) else str(zone.max_drones)

            drones_str = ", ".join(occupants) if occupants else "vazia"
            zone_label = self._get_zone_tag(name)

            print(f"  • [{count}/{max_d}] {zone_label:<30} -> {drones_str}")

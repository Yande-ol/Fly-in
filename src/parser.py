# Leitor e validador do arquivo de mapa
import re
from typing import Dict, Optional, Tuple
from src.models import Connection, Graph, Zone, ZoneType


class MapParseError(Exception):
    """Exceção customizada para erros de parsing com linha e causa."""

    def __init__(self, line_num: int, message: str) -> None:
        self.line_num: int = line_num
        self.message: str = message
        super().__init__(f"Erro na linha {line_num}: {message}")


class Parser:
    """Valida e converte o arquivo de mapa para a estrutura Graph."""

    def __init__(self) -> None:
        self.graph: Graph = Graph()
        self.nb_drones: int = 0
        self.start_found: bool = False
        self.end_found: bool = False
        self.connection_set: set[Tuple[str, str]] = set()

    def parse_file(self, file_path: str) -> Tuple[Graph, int]:
        """Lê o arquivo de mapa e retorna o Grafo e a quantidade de drones."""
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        if not lines:
            raise MapParseError(1, "O arquivo de mapa está vazio.")

        for idx, raw_line in enumerate(lines, start=1):
            line = raw_line.split("#")[0].strip()
            if not line:
                continue

            if self.nb_drones == 0 and idx == 1:
                self._parse_nb_drones(line, idx)
                continue

            if line.startswith("start_hub:") or line.startswith("end_hub:"):
                self._parse_special_hub(line, idx)
            elif line.startswith("hub:"):
                self._parse_regular_hub(line, idx)
            elif line.startswith("connection:"):
                self._parse_connection(line, idx)
            else:
                raise MapParseError(idx, f"Instrução desconhecida: '{line}'")

        self._validate_final_graph()
        return self.graph, self.nb_drones

    def _parse_nb_drones(self, line: str, line_num: int) -> None:
        if not line.startswith("nb_drones:"):
            raise MapParseError(
                line_num, "A primeira linha deve definir 'nb_drones: <num>'"
            )
        try:
            val = int(line.split(":")[1].strip())
            if val <= 0:
                raise ValueError()
            self.nb_drones = val
        except ValueError:
            raise MapParseError(
                line_num, "nb_drones deve ser um inteiro positivo maior que 0"
            )

    def _extract_metadata(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Extrai o texto base e o dicionário de metadados entre [...]"""
        match = re.search(r"\[(.*?)\]", text)
        metadata: Dict[str, str] = {}
        if match:
            meta_str = match.group(1)
            text_without_meta = text[: match.start()].strip()
            for pair in meta_str.split():
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    metadata[k.lower()] = v.lower()
            return text_without_meta, metadata
        return text.strip(), metadata

    def _parse_zone_data(
        self, line: str, line_num: int
    ) -> Tuple[str, int, int, ZoneType, Optional[str], int]:
        clean_line, meta = self._extract_metadata(line)
        parts = clean_line.split(":")[1].strip().split()

        if len(parts) < 3:
            raise MapParseError(
                line_num, "Sintaxe inválida para zona."
                "Esperado: <nome> <x> <y>"
            )

        name, x_str, y_str = parts[0], parts[1], parts[2]

        if "-" in name or " " in name:
            raise MapParseError(
                line_num,
                f"Nome da zona não pode conter hífens ou espaços: '{name}'"
            )

        if name in self.graph.zones:
            raise MapParseError(line_num, f"Zona duplicada: '{name}'")

        try:
            x, y = int(x_str), int(y_str)
        except ValueError:
            raise MapParseError(
                line_num,
                f"Coordenadas devem ser inteiros: {x_str}, {y_str}"
            )

        zone_type_str = meta.get("zone", "normal")
        try:
            zone_type = ZoneType.from_str(zone_type_str)
        except ValueError:
            raise MapParseError(
                line_num, f"Tipo de zona inválido: '{zone_type_str}'"
            )

        color = meta.get("color", None)
        max_drones = 1
        if "max_drones" in meta:
            try:
                max_drones = int(meta["max_drones"])
                if max_drones <= 0:
                    raise ValueError()
            except ValueError:
                raise MapParseError(
                    line_num, "max_drones deve ser um inteiro positivo"
                )

        return name, x, y, zone_type, color, max_drones

    def _parse_special_hub(self, line: str, line_num: int) -> None:
        is_start = line.startswith("start_hub:")
        if is_start and self.start_found:
            raise MapParseError(line_num, "Apenas um start_hub é permitido")
        if not is_start and self.end_found:
            raise MapParseError(line_num, "Apenas um end_hub é permitido")

        name, x, y, z_type, color, max_drones = self._parse_zone_data(
            line, line_num
        )
        zone = Zone(name, x, y, z_type, color, max_drones)

        self.graph.add_zone(zone)
        if is_start:
            self.graph.start_hub = zone
            self.start_found = True
        else:
            self.graph.end_hub = zone
            self.end_found = True

    def _parse_regular_hub(self, line: str, line_num: int) -> None:
        name, x, y, z_type, color, max_drones = self._parse_zone_data(
            line, line_num
        )
        self.graph.add_zone(Zone(name, x, y, z_type, color, max_drones))

    def _parse_connection(self, line: str, line_num: int) -> None:
        clean_line, meta = self._extract_metadata(line)
        conn_str = clean_line.split(":")[1].strip()

        if "-" not in conn_str:
            raise MapParseError(
                line_num, "Conexão deve ser no formato <zone1>-<zone2>"
            )

        z1_name, z2_name = conn_str.split("-", 1)

        if (
            z1_name not in self.graph.zones
            or z2_name not in self.graph.zones
        ):
            raise MapParseError(
                line_num,
                f"Conexão refere-se a zona inexistente:"
                f"'{z1_name}' ou '{z2_name}'",
            )

        # Checa duplicatas (a-b ou b-a)
        pair = (min(z1_name, z2_name), max(z1_name, z2_name))
        if pair in self.connection_set:
            raise MapParseError(
                line_num, f"Conexão duplicada entre '{z1_name}' e '{z2_name}'"
            )
        self.connection_set.add(pair)

        max_capacity = 1
        if "max_link_capacity" in meta:
            try:
                max_capacity = int(meta["max_link_capacity"])
                if max_capacity <= 0:
                    raise ValueError()
            except ValueError:
                raise MapParseError(
                    line_num, "max_link_capacity deve ser um inteiro positivo"
                )

        conn = Connection(
            self.graph.zones[z1_name],
            self.graph.zones[z2_name],
            max_capacity,
        )
        self.graph.add_connection(conn)

    def _validate_final_graph(self) -> None:
        if not self.start_found or self.graph.start_hub is None:
            raise MapParseError(0, "O mapa não possui um start_hub definido")
        if not self.end_found or self.graph.end_hub is None:
            raise MapParseError(0, "O mapa não possui um end_hub definido")

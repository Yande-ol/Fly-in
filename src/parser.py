"""Leitor e validador do arquivo de mapa."""

import re
from typing import Dict, Optional, Set, Tuple
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
        self.connection_set: Set[Tuple[str, str]] = set()

    def parse_file(self, file_path: str) -> Tuple[Graph, int]:
        """Lê o arquivo de mapa e retorna o Grafo e os drones."""
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        if not lines:
            raise MapParseError(1, "O arquivo de mapa está vazio.")

        for idx, raw_line in enumerate(lines, start=1):
            line = raw_line.split("#")[0].strip()
            if not line:
                continue

            if self.nb_drones == 0:
                self._parse_nb_drones(line, idx)
                continue

            if line.startswith("start_hub:") or line.startswith(
                "end_hub:"
            ):
                self._parse_special_hub(line, idx)
            elif line.startswith("hub:"):
                self._parse_regular_hub(line, idx)
            elif line.startswith("connection:"):
                self._parse_connection(line, idx)
            else:
                err_msg = f"Instrução desconhecida: '{line}'"
                raise MapParseError(idx, err_msg)

        self._validate_final_graph()
        return self.graph, self.nb_drones

    def _parse_nb_drones(self, line: str, line_num: int) -> None:
        if not line.startswith("nb_drones:"):
            msg_first = (
                "A primeira instrução deve definir 'nb_drones: <num>'"
            )
            raise MapParseError(line_num, msg_first)
        try:
            val = int(line.split(":")[1].strip())
            if val <= 0:
                raise ValueError()
            self.nb_drones = val
        except ValueError:
            msg_val = (
                "nb_drones deve ser um inteiro positivo maior que 0"
            )
            raise MapParseError(line_num, msg_val)

    def _extract_metadata(
        self, text: str, line_num: int, allowed_keys: Set[str]
    ) -> Tuple[str, Dict[str, str]]:
        """Extrai texto base e metadados entre colchetes."""
        if text.count("[") != text.count("]") or text.count("[") > 1:
            raise MapParseError(line_num, "Bloco de metadata inválido")

        match = re.search(r"\[(.*?)\]", text)
        metadata: Dict[str, str] = {}
        if match:
            if match.end() != len(text.strip()):
                raise MapParseError(
                    line_num, "Metadata deve aparecer no final da instrução"
                )
            meta_str = match.group(1)
            text_without_meta = text[: match.start()].strip()
            for pair in meta_str.split():
                if "=" not in pair:
                    raise MapParseError(
                        line_num, f"Metadata inválida: '{pair}'"
                    )
                k, v = pair.split("=", 1)
                key = k.lower()
                if key not in allowed_keys or not v:
                    raise MapParseError(
                        line_num, f"Metadata inválida: '{key}'"
                    )
                metadata[key] = v.lower()
            return text_without_meta, metadata
        return text.strip(), metadata

    def _parse_zone_data(
        self, line: str, line_num: int
    ) -> Tuple[str, int, int, ZoneType, Optional[str], int]:
        clean_line, meta = self._extract_metadata(
            line, line_num, {"zone", "color", "max_drones"}
        )
        parts = clean_line.split(":")[1].strip().split()

        if len(parts) != 3:
            msg_syntax = (
                "Sintaxe inválida para zona. Esperado: <nome> <x> <y>"
            )
            raise MapParseError(line_num, msg_syntax)

        name, x_str, y_str = parts[0], parts[1], parts[2]

        if "-" in name or " " in name:
            msg_name = (
                "Nome da zona não pode conter hífens ou espaços: "
                f"'{name}'"
            )
            raise MapParseError(line_num, msg_name)

        if name in self.graph.zones:
            raise MapParseError(
                line_num, f"Zona duplicada: '{name}'"
            )

        try:
            x, y = int(x_str), int(y_str)
        except ValueError:
            msg_coords = (
                f"Coordenadas devem ser inteiros: {x_str}, {y_str}"
            )
            raise MapParseError(line_num, msg_coords)

        zone_type_str = meta.get("zone", "normal")
        try:
            zone_type = ZoneType.from_str(zone_type_str)
        except ValueError:
            msg_type = f"Tipo de zona inválido: '{zone_type_str}'"
            raise MapParseError(line_num, msg_type)

        color = meta.get("color", None)
        max_drones = 1
        if "max_drones" in meta:
            try:
                max_drones = int(meta["max_drones"])
                if max_drones <= 0:
                    raise ValueError()
            except ValueError:
                msg_max = (
                    "max_drones deve ser um inteiro positivo"
                )
                raise MapParseError(line_num, msg_max)

        return name, x, y, zone_type, color, max_drones

    def _parse_special_hub(self, line: str, line_num: int) -> None:
        is_start = line.startswith("start_hub:")
        if is_start and self.start_found:
            msg_start = "Apenas um start_hub é permitido"
            raise MapParseError(line_num, msg_start)
        if not is_start and self.end_found:
            msg_end = "Apenas um end_hub é permitido"
            raise MapParseError(line_num, msg_end)

        name, x, y, z_type, color, _ = self._parse_zone_data(
            line, line_num
        )
        zone = Zone(name, x, y, z_type, color, max_drones=999999)

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
        self.graph.add_zone(
            Zone(name, x, y, z_type, color, max_drones)
        )

    def _parse_connection(self, line: str, line_num: int) -> None:
        clean_line, meta = self._extract_metadata(
            line, line_num, {"max_link_capacity"}
        )
        conn_str = clean_line.split(":")[1].strip()

        if "-" not in conn_str:
            msg_conn = (
                "Conexão deve ser no formato <zone1>-<zone2>"
            )
            raise MapParseError(line_num, msg_conn)

        names = conn_str.split("-")
        if len(names) != 2 or not all(names):
            raise MapParseError(
                line_num, "Conexão deve conter exatamente duas zonas"
            )
        z1_name, z2_name = names

        if (
            z1_name not in self.graph.zones
            or z2_name not in self.graph.zones
        ):
            msg_missing = (
                "Conexão refere-se a zona inexistente: "
                f"'{z1_name}' ou '{z2_name}'"
            )
            raise MapParseError(line_num, msg_missing)

        pair = (min(z1_name, z2_name), max(z1_name, z2_name))
        if pair in self.connection_set:
            msg_dup = (
                f"Conexão duplicada entre '{z1_name}' e '{z2_name}'"
            )
            raise MapParseError(line_num, msg_dup)
        self.connection_set.add(pair)

        max_capacity = 1
        if "max_link_capacity" in meta:
            try:
                max_capacity = int(meta["max_link_capacity"])
                if max_capacity <= 0:
                    raise ValueError()
            except ValueError:
                msg_cap = (
                    "max_link_capacity deve ser um inteiro positivo"
                )
                raise MapParseError(line_num, msg_cap)

        conn = Connection(
            self.graph.zones[z1_name],
            self.graph.zones[z2_name],
            max_capacity,
        )
        self.graph.add_connection(conn)

    def _validate_final_graph(self) -> None:
        if not self.start_found or self.graph.start_hub is None:
            msg_no_start = "O mapa não possui um start_hub definido"
            raise MapParseError(0, msg_no_start)
        if not self.end_found or self.graph.end_hub is None:
            msg_no_end = "O mapa não possui um end_hub definido"
            raise MapParseError(0, msg_no_end)

        if not self._has_path_to_end():
            raise MapParseError(
                0, "Não existe caminho entre start_hub e end_hub"
            )

    def _has_path_to_end(self) -> bool:
        """Verifica se existe um caminho transitável até o end_hub."""
        if self.graph.start_hub is None or self.graph.end_hub is None:
            return False

        visited: Set[str] = {self.graph.start_hub.name}
        pending = [self.graph.start_hub]
        while pending:
            current = pending.pop()
            if current.name == self.graph.end_hub.name:
                return True
            for neighbor in self.graph.get_neighbors(current):
                if neighbor.zone_type == ZoneType.BLOCKED:
                    continue
                if neighbor.name not in visited:
                    visited.add(neighbor.name)
                    pending.append(neighbor)
        return False

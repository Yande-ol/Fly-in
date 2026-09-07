*This project has been created as part of the 42 curriculum by Yan Matos.*

# Fly-In

---
## Table of Contents

1. [Description](#description)
2. [Theoretical Background & Algorithmic Strategy](#theoretical-background--algorithmic-strategy)
   - [Graph Modeling](#1-graph-modeling)
   - [Route Discovery (Modified Dijkstra & Vertex Penalty)](#2-route-discovery-modified-dijkstra--vertex-penalty)
   - [Discrete-Time Space Reservation & Scheduling](#3-discrete-time-space-reservation--scheduling)
   - [Simultaneous Transitions & Deadlock Avoidance](#4-simultaneous-transitions--deadlock-avoidance)
3. [Architecture & Module Overview](#architecture--module-overview)
4. [Input Format Specifications](#input-format-specifications)
5. [Visual Features](#visual-features)
6. [Examples of Execution](#examples-of-execution)
   - [Standard Mode (Official Output)](#standard-mode-official-output)
   - [Visual Mode (-v)](#visual-mode--v)
   - [Debug Mode (-d)](#debug-mode--d)
7. [Instructions: Installation & How to Run](#Instructions: installation--how-to-run)
8. [Code Quality & Standards](#code-quality--standards)
9. [Resources & AI Usage](#resources--ai-usage)

---

## Description

**Fly-In** is a deterministic traffic management and pathfinding engine built with Python 3.10+. The system coordinates the transit of an arbitrary fleet of $N$ autonomous drones navigating a topological network from a designated entry node (`start_hub`) to an exit target node (`end_hub`). The primary goal is minimizing total makespan (number of operational turns) while strictly adhering to node capacities and edge transit rules.

Unlike single-agent pathfinding systems, **Fly-In** models discrete spatial and temporal dimensions:
* **Node Capacity Constraints:** Intermediate flight zones have fixed capacity thresholds ($\text{max\_drones} \ge 1$). Drones cannot land or remain in a zone if its threshold for that turn is saturated.
* **Infinite Hubs:** The initial takeoff zone (`start_hub`) and final destination (`end_hub`) hold capacity $\infty$, meaning any number of drones can exist there concurrently.
* **Synchronous Turns:** All operational events happen in discrete time steps $t \in \mathbb{N}$. Within each turn, every drone either transitions to an adjacent valid node or holds position at its current location.

---

## Theoretical Background & Algorithmic Strategy

### 1. Graph Modeling
The airspace is formalized as a directed multigraph $G = (V, E)$, where:
* Each vertex $v \in V$ represents an airspace zone with coordinates $(x, y)$, zone type attributes (`normal`, `priority`, `restricted`), and a maximum concurrent drone capacity $C(v) = \text{max\_drones}$.
* Each directed or undirected edge $e = (u, v) \in E$ defines a navigable airway allowing a 1-turn traversal.

### 2. Route Discovery (Modified Dijkstra & Vertex Penalty)
A naive approach would direct every drone along the single shortest topological path, creating severe queue bottlenecks at intermediate nodes. To maximize network throughput, the pathfinding engine employs an iterative variant of **Dijkstra's Algorithm** with dynamic cost augmentation:

1. **Base Pathfinding:** Dijkstra calculates the optimal path from `start_hub` to `end_hub` considering base edge traversal weights and zone classifications.
2. **Congestion Penalization:** For each extracted path, intermediate vertices receive an artificial cost penalty.
3. **Alternative Discovery:** The algorithm executes subsequent Dijkstra passes against the penalized graph to locate disjoint or semi-disjoint bypass corridors.
4. **Pruning:** Suboptimal paths that take significantly longer than queueing on the primary route are discarded to preserve computational efficiency.

### 3. Discrete-Time Space Reservation & Scheduling
Once the set of viable flight corridors $\mathcal{P} = \{P_1, P_2, \dots, P_k\}$ is established, the **Simulator** engine dispatches drones via a reservation table mapping $(v, t) \to \text{occupancy}$:

$$\text{occupancy}(v, t) = \sum_{d \in \text{Drones}} \mathbb{I}(\text{pos}(d, t) == v)$$

For every drone $d_i \in \{1, \dots, N\}$, the dispatcher determines:
* Optimal departure turn $t_{\text{start}}$ from `start_hub`.
* Best corridor $P \in \mathcal{P}$ minimizing arrival turn $t_{\text{arrival}}$.
* Necessary holding turns (delays) along the route to guarantee that at no point does $\text{occupancy}(v, t) > C(v)$.

### 4. Simultaneous Transitions & Deadlock Avoidance
A critical subject requirement is handling simultaneous handoffs:
* If drone $A$ occupies node $v_1$ at turn $t-1$ and moves to $v_2$ at turn $t$, node $v_1$ has a slot vacated at turn $t$.
* Drone $B$ at an adjacent node $v_0$ can legally move into $v_1$ at turn $t$.
* The simulation engine models departures before entries at each discrete transition step, enabling continuous pipelining through single-capacity bottlenecks.

---

## Architecture & Module Overview

The repository structure isolates responsibilities into modular units under `src/`:

```text
Fly-in/
├── maps/                     # Official map evaluation suites
│   ├── easy/                 # Baseline validation maps
│   ├── medium/               # Loops, dead-ends, and bifurcations
│   ├── hard/                 # Dense mazes and capacity chokepoints
│   └── challenger/           # High drone count stress scenarios
├── src/
│   ├── __init__.py           # Package marker
│   ├── models.py             # Strongly-typed data models (Zone, Edge, Path, Graph)
│   ├── parser.py             # Map file syntax lexer, validator, and tokenizer
│   ├── pathfinder.py         # Dijkstra routing and corridor discovery
│   ├── simulator.py          # Temporal event queue and space reservation engine
│   └── visualizer.py         # ANSI terminal renderer with turn state matrix
├── main.py                   # CLI entrypoint, argument handling, execution runner
├── Makefile                  # Lifecycle orchestration (lint, run, debug, clean)
├── README.md                 # Complete project technical documentation
└── requirements.txt          # Static analysis requirements (flake8, mypy)
```

### Module Responsibilities
- **`src/models.py`**: Declares immutable `Zone`, `Connection`, `Path`, and `Graph` classes using `@dataclass`. Enforces strong type safety across coordinate handling, zone tagging, and adjacency representations.
- **`src/parser.py`**: Handles map parsing, verifies coordinate consistency, detects orphaned zones, validates single start/end hubs, and discards inline comments/whitespace.
- **`src/pathfinder.py`**: Houses graph traversal algorithms, min-heap priority queues, cost calculation routines, and path conflict estimation.
- **`src/simulator.py`**: Coordinates drone lifecycles, computes per-turn movement vectors, tracks spatial occupancy, and serializes movements to standard 42 string notation.
- **`src/visualizer.py`**: Renders turn-by-turn simulation states, colored capacity fractions, and drone placements directly to the terminal.

---

## Input Format Specifications

Map files (supporting `.txt` or `.map` extensions) declare three distinct sections:

```plaintext
# 1. Total Fleet Count
nb_drones: 2

# 2. Zone Declarations: <name> <x> <y> [metadata]
start 0 0 [start]
waypoint1 1 0 [max_drones=1]
waypoint2 2 0 [max_drones=1]
goal 3 0 [end]

# 3. Directed/Undirected Edges: <origin> - <destination>
start - waypoint1
waypoint1 - waypoint2
waypoint2 - goal
```

- Coordinates `(x,y)` define spatial positions.
- Hub tags `[start]` and `[end]` set entry/exit points and apply capacity ∞.
- Zone capacities are declared via `[max_drones=N]` (defaulting to 1 if omitted).

---

## Visual Features

Executing the program with `--visual` or `-v` activates the formatted terminal visualizer:

- **Turn Status Frames:** Renders dedicated unicode-boxed headers identifying the active turn index.
- **Movement Log:** Lists all active vector dispatches in official `D<id>-<zone>` syntax.
- **Real-Time Capacity Gauges:** Displays instantaneous utilization metrics against maximum node limits (`[current/max]`).
- **Drone Location Matrix:** Shows exact drone IDs inhabiting each zone per discrete step.
- **ANSI Color Highlighting:** Clear visual differentiation between regular nodes, critical chokepoints, and terminal hubs.

---

## Examples of Execution

### Standard Mode (Official Output)

By default, the program outputs only the required move tokens per turn, making it fully compatible with automated verification suites:

```bash
python3 main.py maps/easy/01_linear_path.txt
```

Output:
```plaintext
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

### Visual Mode (-v)

Runs detailed step-by-step visualization in the terminal:

```bash
python3 main.py maps/easy/01_linear_path.txt -v
```

Output:
```plaintext
┌──────────────────────────────────────────────┐
│  TURNO 01                                    │
└──────────────────────────────────────────────┘
Movimentos: D1-waypoint1

Ocupação das Zonas:
  • [1/∞] start (normal)        -> D2
  • [1/1] waypoint1 (normal)    -> D1
  • [0/1] waypoint2 (normal)    -> vazia
  • [0/∞] goal (normal)         -> vazia

┌──────────────────────────────────────────────┐
│  TURNO 02                                    │
└──────────────────────────────────────────────┘
Movimentos: D1-waypoint2 D2-waypoint1

Ocupação das Zonas:
  • [0/∞] start (normal)        -> vazia
  • [1/1] waypoint1 (normal)    -> D2
  • [1/1] waypoint2 (normal)    -> D1
  • [0/∞] goal (normal)         -> vazia
```

### Debug Mode (-d)

Provides topology statistics, node capacity distributions, and path traversal costs:

```bash
python3 main.py maps/easy/01_linear_path.txt --debug
```

Output:
```plaintext
=== Mapa Carregado com Sucesso ===
Número de drones: 2
Start Hub: Zone(start, type=normal, max_drones=inf)
End Hub: Zone(goal, type=normal, max_drones=inf)
Total de zonas: 4
Total de conexões: 3

=== Teste do Pathfinder ===
Caminho mais curto absoluto: Path(start -> waypoint1 -> waypoint2 -> goal, cost=3)
Total de rotas disjuntas encontradas: 1
  • Rota 1: Path(start -> waypoint1 -> waypoint2 -> goal, cost=3)
```

---

## Instructions: Installation & How to Run

### Installation

Clone the repository and install development dependencies:

```bash
make install
```

### Execution Commands

Run Standard Simulation:
```bash
make run MAP=maps/easy/01_linear_path.txt
```

Run Terminal Visualizer:
```bash
make visual MAP=maps/easy/01_linear_path.txt
```

Run Interactive Debugger (pdb):
```bash
make debug MAP=maps/easy/01_linear_path.txt
```

Run Static Linters:
```bash
make lint
```

Clean Cache & Temporary Directories:
```bash
make clean
```

---

## Code Quality & Standards

- **PEP 8 Compliance:** All Python files strictly comply with PEP 8 standards, including the 79-column line limit enforced by flake8.
- **Strict Type Annotations:** Fully typed with Python 3.10+ type hints (`typing` module). Validated using mypy with `--disallow-untyped-defs` and `--check-untyped-defs`.
- **Automated Cleanup:** The `make clean` rule removes all bytecode caches (`__pycache__`), typing caches (`.mypy_cache`), and temporary testing artifacts.

---

## Resources & AI Usage

### References & Documentation
- Python 3.10 Documentation — Dataclasses, typing, and argparse implementations.
- Dijkstra's Algorithm Overview — Shortest path discovery in weighted graphs.
- PEP 8 - Style Guide for Python Code — Formatting, naming conventions, and line limits.

### AI Assistance Statement
**Assistance Scope:** Generative AI was consulted as a pair-programming resource during development. It aided in formulating edge-case unit test layouts, generating sample map permutations for complex graph topologies, and refining the structural documentation format.


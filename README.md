
# Fly-in 

## Description
**Fly-in** is an algorithmic simulation project designed to route a fleet of autonomous drones from a starting hub to an end hub in the minimum number of simulation turns. 

The simulation navigates a network of interconnected zones while respecting various constraints:
- Node capacities (`max_drones`) and link capacities (`max_link_capacity`).
- Varying movement costs depending on zone types (`normal`, `restricted`, `priority`, `blocked`).
- Conflict-free simultaneous drone movements and turn scheduling.

## Technical Choices & Algorithm Strategy
*(To be updated upon completion)*

- **Graph Representation:** Custom Object-Oriented Graph structure built from scratch (no external graph libraries permitted).
- **Pathfinding Approach:** *(e.g., Multi-path BFS / Flow optimization / Custom Dijkstra modified for capacity tracking)*.
- **Type Safety & Standards:** Fully typed Python codebase validated with `mypy --strict` and `flake8`.

---

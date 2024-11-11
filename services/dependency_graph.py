from typing import Dict, List, Any

class DependencyGraph:
    
    def __init__(self):
        self.dependencies: Dict[str, List[str]] = {}

    def add_dependency(self, agent: str, depends_on: str):
        """Add a dependency relationship."""
        if agent not in self.dependencies:
            self.dependencies[agent] = []
        self.dependencies[agent].append(depends_on)

    def check_dependencies_met(self, agent: str, agent_status: Dict[str, Any]) -> bool:
        """Check if all dependencies for an agent are completed."""
        deps = self.dependencies.get(agent, [])
        return all(agent_status.get(dep) and agent_status[dep].state == "completed" for dep in deps)

    def has_circular_dependency(self) -> bool:
        """Detect circular dependencies using a depth-first search."""
        visited = {}
        
        def visit(agent):
            if visited.get(agent) == -1:  # Cycle found
                return True
            if visited.get(agent) == 1:
                return False  # Already processed
            
            visited[agent] = -1  # Mark as visiting
            for dep in self.dependencies.get(agent, []):
                if visit(dep):
                    return True
            visited[agent] = 1  # Mark as processed
            return False
        
        return any(visit(agent) for agent in self.dependencies)

    def get_dependents(self, agent: str) -> List[str]:
        """Return a list of agents that depend on the given agent."""
        dependents = []
        for ag, deps in self.dependencies.items():
            if agent in deps:
                dependents.append(ag)
        return dependents
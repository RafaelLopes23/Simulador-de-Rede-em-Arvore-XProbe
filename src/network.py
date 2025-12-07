from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import ipaddress
import random


@dataclass
class Interface:
    name: str
    ip: Optional[ipaddress.IPv4Address] = None
    network: Optional[ipaddress.IPv4Network] = None


@dataclass
class RoutingEntry:
    destination: ipaddress.IPv4Network
    next_hop: Optional[ipaddress.IPv4Address]  # None means directly connected
    out_interface: Optional[str] = None
    metric: int = 1


@dataclass
class Link:
    a: str
    b: str
    medium: str  # e.g., "fiber", "copper"
    capacity_gbps: float
    latency_ms: float


@dataclass
class Node:
    name: str
    kind: str  # 'router' | 'host' | 'switch'
    interfaces: Dict[str, Interface] = field(default_factory=dict)
    routing_table: List[RoutingEntry] = field(default_factory=list)  # routers only
    default_gateway: Optional[ipaddress.IPv4Address] = None  # hosts only
    active: bool = True  # hosts only

    def add_interface(self, ifname: str, ip: Optional[str], network: Optional[str]):
        ip_addr = ipaddress.IPv4Address(ip) if ip else None
        net = ipaddress.IPv4Network(network) if network else None
        self.interfaces[ifname] = Interface(name=ifname, ip=ip_addr, network=net)

    def add_route(self, destination: str, next_hop: Optional[str], out_interface: Optional[str] = None, metric: int = 1):
        self.routing_table.append(
            RoutingEntry(
                destination=ipaddress.IPv4Network(destination),
                next_hop=ipaddress.IPv4Address(next_hop) if next_hop else None,
                out_interface=out_interface,
                metric=metric,
            )
        )


class Graph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.links: List[Link] = []
        self.adj: Dict[str, List[Tuple[str, Link]]] = {}
        self.ip_to_node: Dict[str, str] = {}

    def add_node(self, node: Node):
        self.nodes[node.name] = node
        self.adj.setdefault(node.name, [])
        # index IPs
        for iface in node.interfaces.values():
            if iface.ip:
                self.ip_to_node[str(iface.ip)] = node.name

    def add_link(self, a: str, b: str, medium: str, capacity_gbps: float, latency_ms: float):
        link = Link(a=a, b=b, medium=medium, capacity_gbps=capacity_gbps, latency_ms=latency_ms)
        self.links.append(link)
        self.adj.setdefault(a, []).append((b, link))
        self.adj.setdefault(b, []).append((a, link))

    def find_node_by_ip(self, ip: str) -> Optional[Node]:
        name = self.ip_to_node.get(ip)
        return self.nodes.get(name) if name else None

    def get_path_latency(self, path: List[str]) -> float:
        total = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            # find link between u and v
            link = next((l for nbr, l in self.adj[u] if nbr == v), None)
            if link:
                total += link.latency_ms
        return total

    def route_step(self, current: Node, dest_ip: ipaddress.IPv4Address) -> Optional[str]:
        # hosts forward to default gateway
        if current.kind == 'host':
            return self.ip_to_node.get(str(current.default_gateway))

        if current.kind == 'switch':
            # L2 switch: forward to any neighbor toward routers/hosts; in a tree, pick the neighbor that moves closer.
            # Heuristic: prefer router neighbors if available.
            neighbors = [nbr for nbr, _ in self.adj[current.name]]
            # try to move toward the node containing dest_ip if directly adjacent
            dest_node_name = self.ip_to_node.get(str(dest_ip))
            if dest_node_name and dest_node_name in neighbors:
                return dest_node_name
            # prefer routers then hosts
            for nbr in neighbors:
                if self.nodes[nbr].kind == 'router':
                    return nbr
            return neighbors[0] if neighbors else None

        # router: choose most specific matching route
        if current.kind == 'router':
            matching = [r for r in current.routing_table if dest_ip in r.destination]
            if not matching:
                # try default route 0.0.0.0/0
                matching = [r for r in current.routing_table if r.destination.prefixlen == 0]
            if not matching:
                return None
            # longest prefix match
            matching.sort(key=lambda r: r.destination.prefixlen, reverse=True)
            chosen = matching[0]
            if chosen.next_hop:
                return self.ip_to_node.get(str(chosen.next_hop))
            # direct network: pick neighbor in that network
            # Strategy: choose the neighbor that leads to any node with IP in this network
            target_net = chosen.destination
            neighbors = [nbr for nbr, _ in self.adj[current.name]]

            def neighbor_reaches_net(start: str) -> bool:
                # Do not traverse back through the current router
                visited = {current.name}
                queue = [start]
                hops = {start: 0}
                # limit search depth to avoid wide traversals; tree is shallow
                MAX_DEPTH = 4
                while queue:
                    u = queue.pop(0)
                    if u in visited:
                        continue
                    visited.add(u)
                    node_u = self.nodes[u]
                    # does this node have any interface IP within target_net?
                    if node_u.name != current.name:
                        for iface in node_u.interfaces.values():
                            if iface.ip and iface.ip in target_net:
                                return True
                    # expand BFS
                    for v, _ in self.adj.get(u, []):
                        if v not in visited and hops[u] + 1 <= MAX_DEPTH:
                            hops[v] = hops[u] + 1
                            queue.append(v)
                return False

            # Prefer switches first (typical router->switch->hosts fanout), then any neighbor
            switch_neighbors = [n for n in neighbors if self.nodes[n].kind == 'switch']
            for nbr in switch_neighbors + neighbors:
                if neighbor_reaches_net(nbr):
                    return nbr
            # fallback: any neighbor (shouldn't happen in valid config)
            return neighbors[0] if neighbors else None
        return None

    def compute_path(self, src: Node, dest: Node) -> Optional[List[str]]:
        # follow routing hops; since it's a tree, this should converge
        path = [src.name]
        current = src
        guard = 0
        while current.name != dest.name and guard < 100:
            guard += 1
            next_name = self.route_step(current, list(dest.interfaces.values())[0].ip if dest.interfaces else ipaddress.IPv4Address(list(self.ip_to_node.keys())[0]))
            if not next_name:
                return None
            path.append(next_name)
            current = self.nodes[next_name]
        return path


def simulate_rtt_ms(one_way_ms: float) -> float:
    # RTT ≈ 2 * one-way + processing + jitter
    base = 2 * one_way_ms
    processing = random.uniform(0.05, 0.5)  # router/host stack
    jitter = random.uniform(0, 0.3)
    return base + processing + jitter

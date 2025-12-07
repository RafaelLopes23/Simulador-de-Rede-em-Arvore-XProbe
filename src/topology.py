from ipaddress import IPv4Address
from .network import Graph, Node


def build_topology() -> Graph:
    g = Graph()

    # Core router
    core = Node(name='core', kind='router')
    core.add_interface('core-a1', '172.16.0.34', '172.16.0.32/30')
    core.add_interface('core-a2', '172.16.1.66', '172.16.1.64/30')
    g.add_node(core)

    # Aggregation a1
    a1 = Node(name='a1', kind='router')
    a1.add_interface('a1-core', '172.16.0.33', '172.16.0.32/30')
    a1.add_interface('a1-e1', '172.16.0.1', '172.16.0.0/28')
    a1.add_interface('a1-e2', '172.16.0.17', '172.16.0.16/28')
    g.add_node(a1)

    # Aggregation a2
    a2 = Node(name='a2', kind='router')
    a2.add_interface('a2-core', '172.16.1.65', '172.16.1.64/30')
    a2.add_interface('a2-e3', '172.16.1.1', '172.16.1.0/27')
    a2.add_interface('a2-e4', '172.16.1.33', '172.16.1.32/27')
    g.add_node(a2)

    # Edge switches (L2)
    es_e1 = Node(name='edge_e1', kind='switch')
    es_e2 = Node(name='edge_e2', kind='switch')
    es_e3 = Node(name='edge_e3', kind='switch')
    es_e4 = Node(name='edge_e4', kind='switch')
    g.add_node(es_e1)
    g.add_node(es_e2)
    g.add_node(es_e3)
    g.add_node(es_e4)

    # Hosts (create a few per subnet; the report can list all)
    hosts = []
    for i in range(2, 12):  # e1: 10 hosts 172.16.0.2..11
        h = Node(name=f'h_e1_{i}', kind='host')
        ip = IPv4Address(f'172.16.0.{i}')
        h.add_interface('eth0', str(ip), '172.16.0.0/28')
        h.default_gateway = IPv4Address('172.16.0.1')
        hosts.append(h)
        g.add_node(h)

    for i in range(18, 28):  # e2: 10 hosts 172.16.0.18..27
        h = Node(name=f'h_e2_{i}', kind='host')
        ip = IPv4Address(f'172.16.0.{i}')
        h.add_interface('eth0', str(ip), '172.16.0.16/28')
        h.default_gateway = IPv4Address('172.16.0.17')
        hosts.append(h)
        g.add_node(h)

    for i in range(2, 22):  # e3: 20 hosts 172.16.1.2..21
        h = Node(name=f'h_e3_{i}', kind='host')
        ip = IPv4Address(f'172.16.1.{i}')
        h.add_interface('eth0', str(ip), '172.16.1.0/27')
        h.default_gateway = IPv4Address('172.16.1.1')
        hosts.append(h)
        g.add_node(h)

    for i in range(34, 54):  # e4: 20 hosts 172.16.1.34..53
        h = Node(name=f'h_e4_{i}', kind='host')
        ip = IPv4Address(f'172.16.1.{i}')
        h.add_interface('eth0', str(ip), '172.16.1.32/27')
        h.default_gateway = IPv4Address('172.16.1.33')
        hosts.append(h)
        g.add_node(h)

    # Links core<->agg (fiber 40Gbps ~1ms)
    g.add_link('core', 'a1', medium='fiber', capacity_gbps=40.0, latency_ms=1.0)
    g.add_link('core', 'a2', medium='fiber', capacity_gbps=40.0, latency_ms=1.0)

    # Links agg<->edge (10Gbps ~0.5ms)
    g.add_link('a1', 'edge_e1', medium='fiber/copper', capacity_gbps=10.0, latency_ms=0.5)
    g.add_link('a1', 'edge_e2', medium='fiber/copper', capacity_gbps=10.0, latency_ms=0.5)
    g.add_link('a2', 'edge_e3', medium='fiber/copper', capacity_gbps=10.0, latency_ms=0.5)
    g.add_link('a2', 'edge_e4', medium='fiber/copper', capacity_gbps=10.0, latency_ms=0.5)

    # Links edge<->hosts (1Gbps ~0.1ms)
    for h in hosts:
        if h.interfaces['eth0'].ip in h.interfaces['eth0'].network:
            ip = h.interfaces['eth0'].ip
            if str(ip).startswith('172.16.0.') and int(str(ip).split('.')[-1]) < 16:
                g.add_link('edge_e1', h.name, medium='copper', capacity_gbps=1.0, latency_ms=0.1)
            elif str(ip).startswith('172.16.0.'):
                g.add_link('edge_e2', h.name, medium='copper', capacity_gbps=1.0, latency_ms=0.1)
            elif str(ip).startswith('172.16.1.') and int(str(ip).split('.')[-1]) < 32:
                g.add_link('edge_e3', h.name, medium='copper', capacity_gbps=1.0, latency_ms=0.1)
            else:
                g.add_link('edge_e4', h.name, medium='copper', capacity_gbps=1.0, latency_ms=0.1)

    # Routing tables
    # Core routes summarizing to each aggregator block
    core.add_route('172.16.0.0/24', next_hop='172.16.0.33')
    core.add_route('172.16.1.0/24', next_hop='172.16.1.65')

    # a1 routes: local e1/e2 + default via core
    a1.add_route('172.16.0.0/28', next_hop=None, out_interface='a1-e1')
    a1.add_route('172.16.0.16/28', next_hop=None, out_interface='a1-e2')
    a1.add_route('0.0.0.0/0', next_hop='172.16.0.34')

    # a2 routes: local e3/e4 + default via core
    a2.add_route('172.16.1.0/27', next_hop=None, out_interface='a2-e3')
    a2.add_route('172.16.1.32/27', next_hop=None, out_interface='a2-e4')
    a2.add_route('0.0.0.0/0', next_hop='172.16.1.66')

    return g

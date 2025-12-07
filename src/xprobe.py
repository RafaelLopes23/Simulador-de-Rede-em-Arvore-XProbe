from typing import Dict, List, Tuple
import statistics
import ipaddress
from .network import Graph, simulate_rtt_ms


def xprobe(graph: Graph, src_ip: str, dst_ip: str, samples: int = 3) -> Dict:
    src = graph.find_node_by_ip(src_ip)
    dst = graph.find_node_by_ip(dst_ip)
    result = {
        'src_ip': src_ip,
        'dst_ip': dst_ip,
        'dst_active': False,
        'path': [],
        'rtts_ms': [],
        'avg_rtt_ms': None,
    }

    if not src or not dst:
        return result

    # destination active only for hosts with active flag
    if dst.kind == 'host' and dst.active:
        result['dst_active'] = True
    elif dst.kind == 'router' or dst.kind == 'switch':  # consider infra nodes always reachable
        result['dst_active'] = True

    path = graph.compute_path(src, dst)
    if not path:
        return result

    result['path'] = path
    one_way = graph.get_path_latency(path)

    for _ in range(max(3, samples)):
        rtt = simulate_rtt_ms(one_way)
        result['rtts_ms'].append(rtt)

    result['avg_rtt_ms'] = statistics.mean(result['rtts_ms']) if result['rtts_ms'] else None
    return result

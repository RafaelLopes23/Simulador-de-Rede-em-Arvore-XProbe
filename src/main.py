#!/usr/bin/env python3
import argparse
from typing import Optional
from .topology import build_topology
from .xprobe import xprobe


def list_hosts(graph):
    print("Hosts disponíveis:")
    for name, node in graph.nodes.items():
        if node.kind == 'host':
            ip = next((iface.ip for iface in node.interfaces.values() if iface.ip), None)
            print(f"- {name}: {ip}")


def run_cli():
    parser = argparse.ArgumentParser(description='Simulador de Rede (Árvore) + XProbe')
    parser.add_argument('--list', action='store_true', help='Listar hosts disponíveis')
    parser.add_argument('--src', type=str, help='IP de origem')
    parser.add_argument('--dst', type=str, help='IP de destino')
    parser.add_argument('--samples', type=int, default=3, help='Número de amostras para RTT (>=3)')
    args = parser.parse_args()

    graph = build_topology()

    if args.list or (not args.src and not args.dst):
        list_hosts(graph)
        print("\nExemplo de uso:")
        print("  python3 -m src.main --src 172.16.0.2 --dst 172.16.1.34 --samples 5")
        return

    res = xprobe(graph, args.src, args.dst, samples=args.samples)

    print("\nXProbe resultados:")
    print(f"  Origem: {res['src_ip']}")
    print(f"  Destino: {res['dst_ip']}")
    print(f"  Destino ativo: {'sim' if res['dst_active'] else 'não'}")
    print(f"  Caminho: {' -> '.join(res['path']) if res['path'] else 'indisponível'}")
    if res['rtts_ms']:
        rtts_fmt = ', '.join(f"{v:.3f} ms" for v in res['rtts_ms'])
        print(f"  RTTs: {rtts_fmt}")
        print(f"  RTT médio: {res['avg_rtt_ms']:.3f} ms")
    else:
        print("  Não foi possível medir RTT (sem caminho)")


if __name__ == '__main__':
    run_cli()

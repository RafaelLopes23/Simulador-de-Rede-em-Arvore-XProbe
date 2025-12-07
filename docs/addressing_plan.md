# Plano de Endereçamento (Fase 1)

Rede privada: 172.16.0.0/16 (domínio único, classe B privada)

Topologia simplificada (árvore):
- Núcleo: roteador central `core`
- Agregação: roteadores `a1` e `a2`
- Bordas: switches L2 (sem IP)
- Hosts: subredes `e1`, `e2`, `e3`, `e4`

Blocos por agregador (para suportar ≥4 subredes cada):
- a1: bloco `172.16.0.0/24` (pode ser subdividido em várias subredes)
- a2: bloco `172.16.1.0/24`

Subredes de borda:
- e1: `172.16.0.0/28` (14 hosts) — gateway `172.16.0.1`
- e2: `172.16.0.16/28` (14 hosts) — gateway `172.16.0.17`
- e3: `172.16.1.0/27` (30 hosts) — gateway `172.16.1.1`
- e4: `172.16.1.32/27` (30 hosts) — gateway `172.16.1.33`

Links ponto-a-ponto (uplinks):
- a1 ↔ core: `172.16.0.32/30`
  - a1: `172.16.0.33`
  - core: `172.16.0.34`
- a2 ↔ core: `172.16.1.64/30`
  - a2: `172.16.1.65`
  - core: `172.16.1.66`

Reservas no bloco de cada agregador (capacidade para ≥4 subredes):
- a1: livres dentro `172.16.0.0/24` → ex.: `172.16.0.36/30`, `172.16.0.40/30`, `172.16.0.44/30`...
- a2: livres dentro `172.16.1.0/24` → ex.: `172.16.1.68/30`, `172.16.1.72/30`, `172.16.1.76/30`...

Tipos de enlaces e capacidades (justificativa típica de data center):
- core ↔ agregação: fibra óptica, 40 Gbps, latência ~1 ms
- agregação ↔ borda: fibra/10GBase-SR ou par trançado Cat6A, 10 Gbps, latência ~0.5 ms
- borda ↔ hosts: par trançado Cat6, 1 Gbps, latência ~0.1 ms

Roteamento (estático, sumarização):
- core: rota `172.16.0.0/24` via `172.16.0.34` (interface para a1), rota `172.16.1.0/24` via `172.16.1.66` (interface para a2)
- a1: rotas locais para `e1` e `e2`; rota padrão (0.0.0.0/0) via `172.16.0.34` (core)
- a2: rotas locais para `e3` e `e4`; rota padrão via `172.16.1.66` (core)
- hosts: gateway padrão conforme subrede (ver acima)

Observações:
- Switches de borda são L2 e não possuem endereços IP neste design.
- O esquema pode ser expandido sem conflito dentro dos blocos /24 de cada agregador.

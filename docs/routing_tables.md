# Tabelas de Roteamento (Resumo)

Este arquivo resume as rotas configuradas estaticamente em cada roteador, conforme implementado em `src/topology.py`.

## core
- `172.16.0.0/24` via `172.16.0.33` (a1)
- `172.16.1.0/24` via `172.16.1.65` (a2)

## a1
- `172.16.0.0/28` diretamente conectada (saída `a1-e1`)
- `172.16.0.16/28` diretamente conectada (saída `a1-e2`)
- `0.0.0.0/0` via `172.16.0.34` (core)

## a2
- `172.16.1.0/27` diretamente conectada (saída `a2-e3`)
- `172.16.1.32/27` diretamente conectada (saída `a2-e4`)
- `0.0.0.0/0` via `172.16.1.66` (core)

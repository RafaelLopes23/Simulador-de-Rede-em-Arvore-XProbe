# Simulador de Rede em Árvore + XProbe (Fase 1 e 2)

Este projeto implementa a topologia de árvore (Figura 1) com roteadores `core`, `a1`, `a2`, switches de borda L2 e subredes `e1..e4`, além de um simulador simples com o comando `xprobe` para verificar atividade do destino e calcular o RTT médio (>=3 amostras).

## Estrutura
- `docs/addressing_plan.md`: plano de endereçamento, enlaces e justificativas.
- `docs/topology.dot`: diagrama GraphViz (topologia e enlaces).
- `src/`: código-fonte do simulador e CLI `xprobe`.

## Requisitos
- Linux com Python 3.8+
- (Opcional) Graphviz para renderizar o diagrama: `sudo apt-get install graphviz`

## Como executar

Listar hosts disponíveis e exemplo de uso:
```bash
python3 -m src.main --list
```

Executar um `xprobe` (exemplo: host em `e1` para host em `e4`):
```bash
python3 -m src.main --src 172.16.0.2 --dst 172.16.1.34 --samples 5
```

Saída esperada (caminho e RTT médio variam levemente):
```
XProbe resultados:
  Origem: 172.16.0.2
  Destino: 172.16.1.34
  Destino ativo: sim
  Caminho: h_e1_2 -> a1 -> core -> a2 -> edge_e4 -> h_e4_34
  RTTs: 5.703 ms, 5.782 ms, 5.739 ms, ...
  RTT médio: 5.6xx ms
```

## Renderizar o diagrama
Gerar PNG a partir do DOT:
```bash
dot -Tpng docs/topology.dot -o docs/topology.png
```

## Observações de projeto
- Roteamento estático com sumarização no `core` por agregador.
- Switches são L2 (sem IP); hosts usam gateway padrão do roteador de agregação.
- O simulador usa latências por enlace e jitter simples para compor RTT.

## Próximos passos (Fase 3)
- Gravar um vídeo curto (~5 min) demonstrando: topologia, IPs, tabelas de roteamento e execução de um `xprobe`, com breve análise dos resultados.

```bash
cd chaos-eval-system
python3 -m chaos_manager.manager --list
sudo python3 -m chaos_manager.manager --scenario delay_lo_100ms
sudo python3 -m chaos_manager.manager --scenario delay_lo_100ms --duration 10
sudo python3 -m chaos_manager.manager --scenario composite_lo_delay100_loss20 --duration 15
```

### Explicação
100 ms de atraso em cada pacote que sai pela interface lo
-N1 → envia PING para N2(pacote sai pela lo → leva +100 ms)
-N2 recebe, o echo_server responde com PONG (resposta também sai pela lo → leva +100 ms)

```bash
sudo python3 -m chaos_manager.manager --scenario composite_lo_delay100_loss20 --duration 15
```
Enquanto isso:

-   no collector, os rtt_ms devem subir bastante

-   alguns valores podem ser null (por causa da loss 20%)

-   Depois dos 15s, o reset_after: true limpa o tc e tudo volta ao normal.


```bash
python3 -m chaos_manager.manager --list-nodes --nodes-cfg config/chaos_nodes.yaml

cenário remoto 
sudo python3 -m chaos_manager.manager \
  --scenario delay_100ms \
  --target-node N3 \
  --duration 20 \
  --nodes-cfg config/chaos_nodes.yaml

cenário local
sudo python3 -m chaos_manager.manager \
  --scenario delay_100ms \
  --duration 20

```
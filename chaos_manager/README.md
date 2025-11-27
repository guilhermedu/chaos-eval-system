```bash
cd chaos-eval-system
python3 -m chaos_manager.manager --list
sudo python3 -m chaos_manager.manager --scenario delay_lo_100ms
sudo python3 -m chaos_manager.manager --scenario delay_lo_100ms --duration 10
```

### Explicação
100 ms de atraso em cada pacote que sai pela interface lo
-N1 → envia PING para N2(pacote sai pela lo → leva +100 ms)
-N2 recebe, o echo_server responde com PONG (resposta também sai pela lo → leva +100 ms)
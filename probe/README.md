```bash
cd chaos-eval-system
python3 -m probe.probe_node --node-id N1
python3 -m probe.throughput_probe   --node-id N1   --peer-id N2   --collector-ip 127.0.0.1 
python3 -m probe.app_echo_server --port 9000
python3 -m probe.app_latency_probe \
  --node-id N1 \
  --peer-id SERVICE1 \
  --service-host 127.0.0.1 \
  --service-port 9000 \
  --collector-ip 192.168.1.68
```

```bash
cd chaos-eval-system
python3 -m probe.probe_node --node-id N2 
```


```bash
python3 -m probe.throughput_probe \
  --node-id N1 \
  --peer-id N2 \
  --collector-ip 192.168.1.68 \
  --duration 3
```

```bash
pip install pyyaml
```
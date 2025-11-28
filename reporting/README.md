
```bash
python3 -m reporting.reporting
```


```bash
pip install flask
```



=== Stats para métrica: app_latency_ms (nodeId -> peerId) ===
From   To   Total  OK   Lost  Loss%   Min     Max     Avg     Std
------------------------------------------------------------------------------
N2    SERVICE1    134  134     0    0.00    0.28   82.61   12.01   26.77

=== Stats para métrica: rtt_ms (nodeId -> peerId) ===
From   To   Total  OK   Lost  Loss%   Min     Max     Avg     Std
------------------------------------------------------------------------------
N1    N2       281  281     0    0.00    0.02   62.97    5.14   12.70
N2    N1       282  280     2    0.71    0.04   48.75    5.33   12.91

=== Stats para métrica: throughput_kbps (nodeId -> peerId) ===
From   To   Total  OK   Lost  Loss%   Min     Max     Avg     Std
------------------------------------------------------------------------------
N1    N2        51   51     0    0.00  236.18 1025305.74 595238.57 473362.56

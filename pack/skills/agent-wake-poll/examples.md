# agent-wake-poll examples

## Arm wake

```bash
DELAY=1800  # ≤3600
sleep "$DELAY"
echo "AGENT_LOOP_WAKE_myjob"
```

`block_until_ms: 0`，`notify_on_output.pattern: ^AGENT_LOOP_WAKE_myjob`。

## Scratch 更新（每轮）

```python
# pseudocode
prev, now = job["metric_prev"], measure()
if now > prev:
    job["stall_count"] = 0
else:
    job["stall_count"] += 1
job["metric_prev"], job["metric_now"] = now, now
# then DELAY / next_wake / updated_at
```

## 最小 state

```json
{
  "updated_at": "2026-08-26 12:14:00",
  "started_at": "2026-08-26 09:40:00",
  "current": 4,
  "queue_complete": false,
  "autonomous": true,
  "deadline": null,
  "wake_tag": "cameo49",
  "next_wake": "12:44",
  "eta": "13:10",
  "eta_queue": "15:40",
  "queue": [{
    "id": 4,
    "status": "running",
    "pid_hint": 1338884,
    "log": "/abs/results/run_retry.log",
    "started_at": "2026-08-26 11:20:00",
    "metric_name": "video_latent",
    "metric_now": 12,
    "metric_target": 24,
    "metric_prev": 8,
    "stall_count": 0,
    "last_fail": "torchcodec AssertionError",
    "retry": "reuse_ref_audios_latent",
    "note": "dit 12/24 ~2.6s/step"
  }]
}
```

回用户：

```text
下次检查：12:44
本作业：12/24（50%），预计 13:10 完成
任务队列：第 4/8 项，预计 15:40 完成
已用/剩余：2h36m / 3h24m
```

## 检查（浅）

```bash
ps -p "$PID" >/dev/null && echo alive || echo dead
grep -E 'EXIT:|Traceback|AssertionError|illegal memory' "$LOG" | tail -5
ls "$EXP/dit/video_latent" 2>/dev/null | wc -l   # 勿对大盘 find -R
```

## 停 wake

```bash
kill "$WAKE_PID" 2>/dev/null || true
pkill -f 'AGENT_LOOP_WAKE_myjob' 2>/dev/null || true
```

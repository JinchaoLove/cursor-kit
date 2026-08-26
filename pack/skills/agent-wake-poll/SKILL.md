---
name: agent-wake-poll
description: >-
  Long-running job watchdog: externalized progress scratch + one-shot wake
  (≤1h). Keeps multi-hour jobs moving without high-frequency polling or fat
  in-context memory. Use for long wall-clock tasks, wake/poll loops, hang
  prevention, overnight queues (AGENT_LOOP_WAKE, notify_on_output, state.json).
metadata: {"version": "1.2", "skill-author": "lijinchao, cursor"}
---

# Agent Wake Poll

长耗时任务（墙钟长，未必复杂）：**等不花 token，想只在稀疏检查点**。  
记忆在磁盘短字段里，不在对话里。目标：不 hang、不隔夜进度为 0、不反复踩同一 bug。

## Principle

| 放哪 | 放什么 |
|------|--------|
| 磁盘 `state.json` | 进度、ETA、stall、失败签名（O(1) 字段） |
| Skill / note | 已验证的修复（程序性） |
| Context | 本轮只读 state + 必要的 `tail`/`grep`，不灌全 log |

禁止：固定高频循环轮询；把长 log / 全文历史当记忆。

## Hard rules

1. **One-shot wake only** — `sleep DELAY; echo AGENT_LOOP_WAKE_<tag>`；禁 `while true`。
2. **`DELAY ∈ [60, 3600]`** — 失联窗口上限 1h。
3. **未终态 → 本轮结束前必须已 arm 下一 wake**（先 arm 再长汇报）。
4. **终态 → kill 所有相关 wake**。
5. **进度证据** — 仅 `ps` 存活不够；要看约定度量是否增长（或 stage/日志 mtime 推进）。
6. **`stall_count`**：度量相对上次 **零增长** → +1；有增长 → 置 0。`stall_count ≥ 2` → hang，禁止再空睡。
7. **日志写入用绝对路径**（symlink 只读）。

## Progress scratch（state 必有）

路径任务自定。整文件保持小；**每轮 wake 只改这些字段**：

```json
{
  "updated_at": "...",
  "started_at": "...",
  "current": 1,
  "queue_complete": false,
  "autonomous": true,
  "deadline": null,
  "wake_tag": "myjob",
  "next_wake": "HH:MM",
  "eta": "HH:MM",
  "eta_queue": "HH:MM",
  "wake_pid": 0,
  "queue": [{
    "id": 1,
    "status": "running",
    "pid_hint": 0,
    "log": "/abs/run.log",
    "started_at": "...",
    "metric_name": "combined_video",
    "metric_now": 0,
    "metric_target": 24,
    "metric_prev": 0,
    "stall_count": 0,
    "last_fail": "",
    "retry": "",
    "note": "≤1 line"
  }]
}
```

- `deadline`：用户或任务给出的墙钟目标（ISO/`YYYY-mm-dd HH:MM`）；临近则缩短 `DELAY`，逾期未终态 → 停队汇报。无则 `null`。
- `started_at`：队列启动一次写入；当前 job 首次 running 时写入 `queue[].started_at`。用于均速与已耗时。
- `eta` / `eta_queue`：本 job / 整队预计完成墙钟（`HH:MM`）；无速率则 `null`。
- `last_fail` / `retry`：失败签名与已试修复，避免下一轮重复盲试。
- 度量名随任务变（`video_latent`、`step`、文件数…），但 **prev/now/target/stall_count 结构不变**。

## Loop

```
launch → 写 scratch → arm wake
on wake:
  读 scratch
  alive? / EXIT? / metric_now?
  metric_now > metric_prev → stall=0, 更新 prev/now/eta, 估 DELAY, arm, 回用户 4 行
  metric 达 target → success; 下一 job 或 queue_complete; kill wakes
  进程死未达标 → 记 last_fail; autonomous 则按 retry 最小修一次; 否则停
  stall_count≥2 → hang: 取证 → 最小修重试一次 → 仍挂则停（勿加长 sleep）
  wake 报错/被杀且 job 未终态 → 立刻补 arm
```

### DELAY / ETA

全程均速优先（抗单步抖动）；`metric_now==0` 或缺 `started_at` 时改用上轮间隔。

```text
rate = metric_now / (now - job.started_at)          # units / sec
remain_sec = (metric_target - metric_now) / rate
later = 未开始 jobs（同度量或可按当前 rate 估）
queue_remain = remain_sec + Σ (j.metric_target / rate)

有速率: DELAY = clamp(0.8 * remain_sec, 60, 3600)
        eta = now + remain_sec
        eta_queue = now + queue_remain
无速率: DELAY = 1800; eta = eta_queue = null
有 deadline: DELAY = min(DELAY, seconds_until_deadline)
```

进度（写入 `note` 可省略，回用户必带）：

```text
job_pct = metric_now / metric_target
elapsed = now - (queue.started_at or job.started_at)
```

回用户固定 4 行（先 arm 再汇报；标签与顺序不得改；缺值写 `—`；时钟 `HH:MM`；时长 `XhYm`）：

```text
下次检查：12:44
本作业：12/24（50%），预计 13:10 完成
任务队列：第 4/8 项，预计 15:40 完成
已用/剩余：2h36m / 3h24m
```

「本作业」= 当前 job 的度量（`metric_now/target`）。「任务队列」= 第几项 / 共几项，不要写成百分比。无速率：预计与剩余填 `—`。单 job 可省略「任务队列」行。终态只报「任务队列完成：HH:MM」和「总耗时：XhYm」，不报下次检查。

### Hang 取证（短）

`tail` 日志错误、`metric_now`、`ps`；写入 `note`/`last_fail`。同一 `last_fail` 自动重试 **最多 1 次**。

## Wake 原语

```bash
# Shell: block_until_ms=0
# notify_on_output.pattern=^AGENT_LOOP_WAKE_<tag>  reason≤5词
sleep "$DELAY"
echo "AGENT_LOOP_WAKE_<tag>"
```

`<tag>` 会话内唯一。多 job 串行：成功才启动下一个。

## Anti-patterns

- 高频 tick / `DELAY>3600` / 检查后忘 arm  
- 只看 pid、成功不杀 wake、经漂浮 symlink 写日志  
- 把对话摘要当唯一进度源（应用 scratch）

样例：[examples.md](examples.md)

---
name: agent-wake-poll
description: >-
  Long-running job watchdog driven by wake.py: externalized progress scratch +
  one-shot wake (≤1h). Keeps multi-hour jobs moving without high-frequency
  polling or fat in-context memory. Use for long wall-clock tasks, wake/poll
  loops, hang prevention, overnight queues (AGENT_LOOP_WAKE, notify_on_output,
  .cursor/wake-poll/<tag>.json).
metadata: {"version": "2.1.0", "skill-author": "lijinchao, cursor"}
---

# Agent Wake Poll

长耗时任务（墙钟长，未必复杂）：**等不花 token，只在稀疏检查点想**。进度在磁盘，不在对话里。

度量、stall 计数、DELAY/ETA、汇报文本、arm/kill wake 全由 `wake.py` 执行。
**不要手算、不要自拟汇报格式、不要自己写轮询循环。**

```bash
W="python3 .cursor/skills/agent-wake-poll/wake.py"   # 在 workspace 根跑，state 落 .cursor/wake-poll/
```

## 每轮

```bash
$W check --tag TAG
```

stdout **原样贴给用户**（头部、进度、ETA 已成型），然后按末行 `ACTION` 走：

| ACTION | 做什么 |
|---|---|
| `arm` | `$W arm --tag TAG`，**arm 成功后**再回复用户 |
| `launch` | `bash` 它打印的 `launch_cmd` → `$W started --tag TAG` → `$W arm --tag TAG` |
| `hang` | 读它打印的 log tail 判死因，先看 [pitfalls.md](pitfalls.md)。`autonomous` 且 `retry` 空可重跑一次（再 `started`+`arm`）；改代码 / 装依赖 / 换配置不属自主范围，交给用户。**禁止直接再 arm 空睡** |
| `terminal` | wake 已自动 kill；归还独占资源（GPU 占卡）并核验实例数，再收工 |
| `needs_human` | 逾期或度量读不出来：不 arm，报给用户 |

`WARN:` 行是启动脚本体检（`doctor`）的输出，照抄给用户；确认无害才继续。

### arm

```bash
$W arm --tag TAG
```

Shell 参数：`block_until_ms=0`，`notify_on_output.pattern=^AGENT_LOOP_WAKE_TAG`，reason ≤5 词。
delay 取自 state（首条产出前恒 120s，之后 `clamp(0.8×剩余, 60, 3600)`）。
它会先清旧 wake 再记 pid，重复 arm 不留两个，也不会自杀。

## 建队列

```bash
$W new --launch-cmd "bash /abs/launch_pe49.sh" \
       --metric-cmd "find /abs/out -path '*/combined_video/*.mp4' | wc -l" \
       --metric-target 49 --log /abs/run.log --output-dir /abs/out \
       --metric-name combined_video --done-grep "All done" \
       --global-gpus 16 --autonomous
$W add --tag pe49 ...   # 串行下一项，字段同上
$W started --tag pe49   # bash 起来之后必须调，记开始时间
$W list                 # 续跑时选 queue_complete=false 的 tag
$W doctor --tag pe49    # 单独体检启动脚本
$W stop --tag pe49
```

- `--launch-cmd` 必须是**参数写死的绝对路径 .sh**，可裸执行。换配置就复制脚本改死值——
  脚本文件是这次运行的唯一完整记录。违反项由 `doctor` 报 `WARN`。
- `--metric-cmd` 单行 shell，**stdout 末行只有一个非负整数**；大目录优先数 log（见 pitfalls）。
- tag 由 `new` 自动取（`launch_pe49.sh` → `pe49`，重名加 `_2`），**不让用户手填**；
  续跑多个未完成队列时用 AskQuestion 列 `note`/`launch_cmd` 让用户选。
- 可给 job 加 `liveness_cmd` 字段，`hang` 时自动跑并打印（模式须锚定，见 pitfalls）。

排错与经验：[pitfalls.md](pitfalls.md) ｜ 交互样例：[examples.md](examples.md)

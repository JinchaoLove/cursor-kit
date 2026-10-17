---
name: agent-wake-poll
description: >-
  Long-running job watchdog driven by wake.py: externalized progress scratch +
  one-shot wake (≤1h). Keeps multi-hour jobs moving without high-frequency
  polling or fat in-context memory. Use for long wall-clock tasks, wake/poll
  loops, hang prevention, overnight queues (AGENT_LOOP_WAKE, notify_on_output,
  .cursor/wake-poll/<tag>.json).
metadata: {"version": "2.4.0", "skill-author": "lijinchao, cursor"}
---

# Agent Wake Poll

长耗时任务（墙钟长，未必复杂）：**等不花 token，只在稀疏检查点想**。进度在磁盘，不在对话里。

度量、stall 计数、DELAY/ETA、汇报文本、arm/kill wake 全由 `wake.py` 执行。
**不要手算、不要自拟汇报格式、不要自己写轮询循环。**

职责边界：只管理 **agent 当前所在机器** 上由本会话启动的任务、wake 和 GPU 占卡。
不登录、不巡检、不杀别的机器上的进程；跨机器任务只汇报项目脚本产出的进度，异常交给用户或对应机器负责人。

## 最高优先级：尽快交付

尽快完成用户任务是第一要务。**Agent 是任务顺利交付的责任主体，必须为任务按时启动、持续运行并最终交付负责。**
这不是“尽量关注”，而是必须履行的职责；不能把“命令已提交”当成“任务已启动”，也不能启动后放任不管：

1. 启动前清除本机可控干扰（尤其是 GPU 占卡脚本），确认所需资源已释放；
   占卡还会被别的脚本的 `trap ... EXIT` 在运行中拉回来，**每轮 `check` 都要确认它仍为 0**，
   只在启动前放一次不够（见 [pitfalls.md](pitfalls.md)）；
2. 启动后立即核验目标进程、日志或首个阶段信号，确认任务真实运行后才能 `started` 和 `arm`；
3. 若未启动、秒退或被本机干扰，立即排障并重新启动，不得进入长时间等待；
4. **Agent 因漏停占卡、漏执行 ACTION、误判启动成功、空等、忘记检查等犯傻行为造成的任何任务 delay，
   由 Agent 负全部责任。** 这是严重的交付失职：必须立即发现、纠正、追回进度并如实汇报；不得甩锅给工具、
   占卡脚本或其他进程，不得以“已经 arm”“进程曾经存在”等理由继续等待。

```bash
W="python3 .cursor/skills/agent-wake-poll/wake.py"   # 在 workspace 根跑，state 落 .cursor/wake-poll/
```

## 每轮

```bash
$W check --tag TAG
```

stdout 就是最终汇报，不是供 agent 摘要的素材。先按末行 `ACTION` 完成动作，再在同一轮用户可见回复中：

1. 用代码块逐行原样贴出本次 `check` 的**完整 stdout**；
2. 代码块后至多补一句已执行的动作或需人工判断的结论。

禁止翻译、删行、重排、改写；禁止只回复 “healthy / re-armed / 无需操作” 等摘要。即使系统通知要求
“briefly inform”，也不能用摘要替代 `check` stdout。没有运行 `check` 的旧 wake 结束通知无需重复汇报。
然后按末行 `ACTION` 走：

### 收到 wake 通知

`AGENT_LOOP_WAKE_<tag>` 通知只表示“该检查了”，**不携带任务结果**。收到后固定执行：

1. `$W check --tag <tag>`，不得用临时 shell 命令自行拼进度或手算 ETA；
2. 严格执行 stdout 末行 `ACTION`，`ACTION=arm` 时必须先成功 arm；
3. 用户回复用代码块原样粘贴第 1 步的完整 stdout，代码块后至多一句第 2 步的执行结果。

Shell / tool call 的输出卡片不算用户回复；即使工具输出可见，第 3 步仍必须执行。
同一个 wake 随后出现的 finished 通知只是定时进程退出，不再 `check`，也不重复汇报。
禁止把 wake 通知本身解释成“任务成功”；成功只由 `check` 的 metric / done-grep 判定。

**同一 tag 换了跑的对象（下一个单元 / 下一个变体 / 重跑）必须 `$W started --tag TAG`**，
它会把 `started_at` 与 `metric_*` / `stall_count` 一起重置。只改 `metric_cmd` 不调 `started`，
速率与 ETA 会拿新产物去除上一个对象的起点：实测把「约 1 小时后完成」算成了 16 小时后。

| ACTION | 做什么 |
|---|---|
| `arm` | `$W arm --tag TAG`，**arm 成功后**再回复用户 |
| `launch` | `bash` 它打印的 `launch_cmd` → `$W started --tag TAG` → `$W arm --tag TAG` |
| `hang` | 读它打印的 log tail 判死因，先看 [pitfalls.md](pitfalls.md)。`autonomous` 且 `retry` 空可重跑一次（再 `started`+`arm`）；改代码 / 装依赖 / 换配置不属自主范围，交给用户。**禁止直接再 arm 空睡** |
| `terminal` | wake 已自动 kill；在本机归还独占资源（GPU 占卡）并核验本机实例数，再收工 |
| `needs_human` | 逾期或度量读不出来：不 arm，报给用户 |

`WARN:` 行是启动脚本体检（`doctor`）的输出，照抄给用户；确认无害才继续。

### arm

```bash
$W arm --tag TAG
```

Shell 参数：`block_until_ms=0`，`notify_on_output.pattern=^AGENT_LOOP_WAKE_TAG`，reason ≤5 词。
delay 取自 state（首条产出前恒 120s，之后 `clamp(0.8×剩余, 60, 3600)`）。
它会先清旧 wake 再记 pid，重复 arm 不留两个，也不会自杀。
睡眠期间每分钟采一次本机显卡利用率（`nvidia-smi` util 的各卡均值）存进 state，
`check` 汇报的「显卡利用率」就是这批采样在近 1h 窗口内的均值——所以**漏了 arm 就没有采样**。
它只反映本机、且占卡进程也会把 util 顶高，不能当活性证据（见 [pitfalls.md](pitfalls.md)）。

## 建队列

```bash
$W new --launch-cmd "bash /project/launch_pe49.sh" \
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

- `--launch-cmd` 只能是 `bash /项目目录/launch_xxx.sh`，`.sh` 后禁止跟参数，命令前禁止挂环境变量。
  所有路径、模型、数据、并行度等运行配置都写死在该项目脚本里；换配置就复制脚本改死值。
  这里的“禁止传参”只约束被监控的运行脚本，`wake.py check --tag ...` 等控制命令仍按本文使用。
- 每个运行脚本开头和退出处理参考
  `/mmu-audio-ssd/lijinchao/m2v_zjc_dev_4_8_audio_3_batch/setup_env.sh`：开头定位脚本目录并加载项目
  `setup_env.sh`（或等价地释放本机 GPU 占卡），退出时用 `trap ... EXIT` 恢复占卡，并用
  `trap 'exit 130' INT TERM` 保证报错和 Ctrl-C 都走恢复；末尾禁止 `exec`。违反项由 `doctor` 报 `WARN`。
- **运行期间不要改这个 .sh**：bash 按字节偏移边读边执行，改完会从错位置接着读，
  报语法错或 `exit=127`。要改先 `cp` 一份快照去跑（见 pitfalls）。
- `--metric-cmd` 单行 shell，**stdout 末行只有一个非负整数**；大目录优先数 log（见 pitfalls）。
  只数**已经写完**的产物：存在的文件可能还在写，半成品既虚报进度，也会被下游读崩（见 pitfalls）。
- `--metric-name` 是「一条产物」的名字（`combined_video` / `sample`），汇报的「速率」按它计
  单位墙钟和卡时；`--global-gpus` 只填**本机参与运行的卡数**，不代管或巡检其他机器。
- `--report-cmd`：**项目自带汇报口径时必须填**（多阶段产物、任务在一批单元/变体间轮转，
  例如 RUNBOOK 规定要报「哪个单元、哪个变体、本单元已完成几个、latent x/N 与 mp4 x/N」）。
  它的 stdout 原样置顶在汇报头部，单行多行都行。`metric_*` 是单标量，压不住这些字段：
  把两种产物加成一个 `78/200` 之后，读的人既不知道是哪个单元哪个变体，也没法和上一轮比对。
  **不要因为 `check` 少了项目字段就改回手写汇报**——那样 ETA、stall、速率全部回到手算。
- tag 由 `new` 自动取（`launch_pe49.sh` → `pe49`，重名加 `_2`），**不让用户手填**；
  续跑多个未完成队列时用 AskQuestion 列 `note`/`launch_cmd` 让用户选。
- 可给 job 加 `liveness_cmd` 字段，`hang` 时自动跑并打印（模式须锚定，见 pitfalls）。

排错与经验：[pitfalls.md](pitfalls.md) ｜ 交互样例：[examples.md](examples.md)

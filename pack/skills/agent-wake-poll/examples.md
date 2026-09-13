# agent-wake-poll examples

`W="python3 .cursor/skills/agent-wake-poll/wake.py"`，在 workspace 根执行。

## 一轮完整交互

```
$ $W check --tag pe49
本机地址：10.12.34.56
总卡数：16
完整脚本：/abs/launch_pe49.sh
日志目录：/abs/logs
输出目录：/abs/out
任务序号：第 1 项 / 共 2 项
下次检查：2026-08-28 10:15（delay=1140s）
本作业：12/49（24%），预计 2026-08-28 10:43 完成
任务队列：预计 2026-08-28 12:40 完成
已用/剩余：2h36m / 1h24m
ACTION=arm delay=1140
```

→ 立刻 arm（Shell: `block_until_ms=0`, `notify_on_output.pattern=^AGENT_LOOP_WAKE_pe49`）：

```
$ $W arm --tag pe49
armed pe49 delay=1140s next_wake=2026-08-28 10:15 killed=-
```

→ 然后把 `check` 的 stdout 贴给用户。

## ACTION=launch（队列推进）

```
$ $W check --tag pe49
...
本项完成：combined_video 49/49
下一项：queue[1] bash /abs/launch_te_build.sh
ACTION=launch

$ bash /abs/launch_te_build.sh > /abs/te.log 2>&1 &
$ $W started --tag pe49
queue[1] running since 2026-08-28 12:41:03  ACTION=arm
$ $W arm --tag pe49
```

## ACTION=hang

`check` 会连带打印 log tail、`liveness_cmd` 结果、`last_fail` / `retry` / `autonomous`：

```
停滞 2 轮（combined_video 停在 12）
--- log tail: /abs/run.log
RuntimeError: CUDA out of memory
last_fail=out of memory retry=— autonomous=True
ACTION=hang
```

`autonomous=True` 且 `retry` 为空 → 重跑一次，写回 retry 后继续：

```bash
bash /abs/launch_pe49.sh > /abs/run.log 2>&1 &
$W started --tag pe49          # 重置 metric/stall/started_at
$W arm --tag pe49
```

不可自动处理（需改代码 / 装依赖 / 换配置）→ 不 arm，把 tail 和判断报给用户。

## 度量写法

```bash
# 嵌套产出
--metric-cmd "find /abs/out -path '*/combined_video/*.mp4' 2>/dev/null | wc -l"
# KFS / 大目录：数 log 行，别 find
--metric-cmd "grep -c 'Combining:' /abs/run.log 2>/dev/null || echo 0"
# 单产物
--metric-cmd "test -f /abs/te.whl && echo 1 || echo 0"  --metric-target 1
```

## 启动脚本体检

`new` / `add` / `ACTION=launch` 时自动跑，也可单独：

```
$ $W doctor --launch-cmd "CKPT=/other bash /abs/launch_bad.sh"
WARN: launch_cmd 在命令行挂了 env：漏传会静默回落到脚本默认值（通常是上次实验的配置）
WARN: /abs/launch_bad.sh:7 以 exec 收尾：exec 替换本进程，trap 和结尾行都不会执行
WARN: /abs/launch_bad.sh:6 在 trap(restore) 之外又调了一次恢复：两条都触发会起双份实例互抢显存
WARN: /abs/launch_bad.sh:2 身份参数留了 ${VAR:-默认} 覆盖口，外部 env 可静默改配置
WARN: /abs/launch_bad.sh:5 日志重定向到相对路径 logs/train.log：cwd 一变就写飞，且 symlink 只读
warnings=5
```

活性探测怎么写（模式必须锚定）见 [pitfalls.md](pitfalls.md)；可写进 job 的 `liveness_cmd` 字段。

## state 位置

默认 `.cursor/wake-poll/<tag>.json`（相对 cwd）；换位置用 `WAKE_POLL_DIR=/abs/dir`。
schema 与 1.x 兼容，老队列可直接被 `check` 接管。

# agent-wake-poll examples

`W="python3 .cursor/skills/agent-wake-poll/wake.py"`，在 workspace 根执行。

## 一轮完整交互

```
$ $W check --tag pe49
单元 part_0004a  变体 rand2 (本单元已完成 1/4)  latent 37/50  mp4 0/50
campaign 12/908 变体  |  齐活单元 0/227
本机地址：10.12.34.56
本机参与卡数：8
显卡利用率：81%（本机 8 卡，近 0h57m / 57 个采样点均值）
完整脚本：/abs/launch_pe49.sh
日志目录：/abs/logs
输出目录：/abs/out
任务序号：第 1 项 / 共 2 项
下次检查：2026-08-28 10:15（delay=1140s）
本作业：12/49（24%），预计 2026-08-28 10:43 完成
速率：combined_video 每条 13m00s 墙钟、1.73 卡·h（按 8 卡）
任务队列：预计 2026-08-28 12:40 完成
已用/剩余：2h36m / 1h24m
ACTION=arm delay=1140
```

头两行来自 `--report-cmd`（项目口径，原样置顶），其余由 `wake.py` 生成。

→ 立刻 arm（Shell: `block_until_ms=0`, `notify_on_output.pattern=^AGENT_LOOP_WAKE_pe49`）：

```
$ $W arm --tag pe49
armed pe49 delay=1140s next_wake=2026-08-28 10:15 killed=-
```

→ 然后把 `check` 的 stdout 贴给用户。

用户可见回复必须保留上面代码块的全部内容和顺序，随后至多补一句：

```
已按 ACTION=arm 启动下一次检查。
```

不能只回复“任务正常、watchdog 已重新 arm”；该摘要缺少固定头部、进度、ETA 和 ACTION，不算汇报。

收到 `AGENT_LOOP_WAKE_pe49` 通知时，通知本身只表示“该检查了”，不代表任务成功。固定流程是：

```bash
$W check --tag pe49
# 严格执行上一条 stdout 末行 ACTION；若为 ACTION=arm：
$W arm --tag pe49
```

禁止另写 shell 命令拼进度或手算 ETA。用户回复是 `check` 的完整 stdout，而不是 agent 重写的进度表。
同一 task 随后的 finished 通知只表示 wake 定时进程退出，不再 `check`、不重复汇报。

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
$ $W doctor --launch-cmd "bash /abs/launch_bad.sh extra_arg"
WARN: launch_cmd 必须严格写成 `bash /项目目录/script.sh`：禁止环境变量和脚本参数
WARN: /abs/launch_bad.sh:7 以 exec 收尾：exec 替换本进程，trap 和结尾行都不会执行
WARN: /abs/launch_bad.sh: 开头未加载项目 setup_env.sh，也未释放本机 GPU 占卡
WARN: /abs/launch_bad.sh: 缺少 EXIT trap，退出时不会恢复本机 GPU 占卡
WARN: /abs/launch_bad.sh: 缺少 INT/TERM trap，Ctrl-C/终止时可能跳过恢复处理
WARN: /abs/launch_bad.sh:6 在 trap(restore) 之外又调了一次恢复：两条都触发会起双份实例互抢显存
WARN: /abs/launch_bad.sh:2 身份参数留了 ${VAR:-默认} 覆盖口，外部 env 可静默改配置
WARN: /abs/launch_bad.sh:5 日志重定向到相对路径 logs/train.log：cwd 一变就写飞，且 symlink 只读
warnings=8
```

活性探测怎么写（模式必须锚定）见 [pitfalls.md](pitfalls.md)；可写进 job 的 `liveness_cmd` 字段。

## state 位置

默认 `.cursor/wake-poll/<tag>.json`（相对 cwd）；换位置用 `WAKE_POLL_DIR=/abs/dir`。
schema 与 1.x 兼容，老队列可直接被 `check` 接管。

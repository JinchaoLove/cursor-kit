# agent-wake-poll pitfalls

只在 `ACTION=hang`、或怀疑「进度不动但不知道 job 死没死」时读。都是实际把 agent 空转过几小时的情形。

## 假存活：活性探测命中了自己

**症状**：`pgrep` 每轮都说进程在，但产物几小时不涨；`retry` 永不触发，队列静默空转到早上。

**原因**：你的检查命令是 agent 用 `/bin/bash -c '…pgrep -f "train.py"…'` 跑的，
这个包装 shell 的命令行**本身就含 `train.py`**，于是 `pgrep -f 'train.py'` 恒命中它自己。
死掉的 job 因此永远显示存活，hang 判据里「进程不在」这个条件不可能成立。

**做法**：模式加锚点或绝对路径前缀，让包装 shell（以 `/bin/bash` 开头）不可能匹配：

```bash
pgrep -cf '^python /abs/train\.py' || true
ps -eo args= | grep -E '^python .*/train\.py' | grep -v grep
```

同一个机制也会咬 `pkill -f '<含 tag 的串>'`：它会连包装 shell 一起杀，
表现是那个 Shell 立刻 `status: error`，之后再没有任何 wake。**停 wake 只用 `wake.py stop`。**

## GPU util 不是活性证据

**症状**：`nvidia-smi` 显示 util 100%，判定「在跑」，但其实是占卡脚本在跑，真 job 早挂了。

**做法**：看**显存量级**（推理满载 vs 纯占卡差一个数量级）、产物计数、log mtime；util 只能证明「有人在用卡」。

## 首条产出前的空睡

**症状**：`metric_now` 一直 0，每轮都按「还没开始产出」继续睡，几小时后才发现是缺依赖 / 权限 / NCCL 起不来。

**原因**：环境类失败（依赖缺失、MPI/NCCL、OOM、路径权限）几乎全都在第一条产出之前爆，
而这个阶段度量恒为 0，光看度量分不出「正常预热」和「已经死了」。

**做法**：`metric_now==0` 时 delay 固定 120s（脚本已保证），每轮另外确认三件事都在动：
进程存活（锚定模式）、log mtime 在推进、阶段/前置度量在涨。任一停滞就当 stall 取证，别继续睡。

## 度量命令本身把集群拖死

KFS 等共享存储上，`find` 无界递归会给元数据集群造成压力、进程进 D 状态。
优先数 log：`grep -c 'Combining:' /abs/run.log`。必须 find 时限定 `-maxdepth` 和子目录。

## 跨 session 失联

wake 绑当前 Cursor 会话。会话关掉后 `sleep` 可能还在，但没人消费那条 `AGENT_LOOP_WAKE_*`。
不是故障：用户回来说「wake poll」，直接从 `check` 继续，state 在磁盘上没丢。

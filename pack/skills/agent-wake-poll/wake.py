#!/usr/bin/env python3
"""agent-wake-poll state machine.

每轮固定两条命令：
    python wake.py check --tag TAG     # 更新 state、打印汇报、输出 ACTION=...
    python wake.py arm   --tag TAG     # 清旧 wake 后 sleep，到点打印 AGENT_LOOP_WAKE_<tag>

ACTION 由 agent 消费：
    arm          未终态，按 state.next_wake 的 delay 去 arm
    hang         stall_count>=2，需人/agent 看 log 决定重跑
    launch       当前 job success，下一 pending 项待启动（agent bash 之后调 started）
    terminal     队列完成或需停队，kill 本 tag wake、归还独占资源
    needs_human  逾期 / 读不到度量等，不 arm
"""

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta

TIME_FMT = "%Y-%m-%d %H:%M:%S"
MIN_FMT = "%Y-%m-%d %H:%M"
STATE_DIR = os.path.expanduser(os.environ.get("WAKE_POLL_DIR", ".cursor/wake-poll"))
FAIL_PAT = re.compile(
    r"Traceback \(most recent call last\)|CUDA error|out of memory|"
    r"NCCL error|Killed|Segmentation fault",
    re.I,
)


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    print("ACTION=needs_human")
    sys.exit(1)


def state_path(tag):
    return os.path.join(STATE_DIR, f"{tag}.json")


def load(tag):
    p = state_path(tag)
    if not os.path.exists(p):
        die(f"state 不存在: {p}")
    with open(p) as f:
        return json.load(f)


def save(st):
    os.makedirs(STATE_DIR, exist_ok=True)
    p = state_path(st["wake_tag"])
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, p)


def now_dt():
    return datetime.now()


def parse_dt(s):
    if not s:
        return None
    for fmt in (TIME_FMT, MIN_FMT):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def hm(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 3600}h{(seconds % 3600) // 60:02d}m"


def sh(cmd, timeout=180):
    return subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=timeout
    )


def run_metric(job):
    cmd = job.get("metric_cmd")
    if not cmd:
        die(f"queue[{job['id']}] 缺 metric_cmd")
    try:
        r = sh(cmd)
    except subprocess.TimeoutExpired:
        die(f"metric_cmd 超时: {cmd}")
    lines = [x.strip() for x in r.stdout.splitlines() if x.strip()]
    if not lines or not re.fullmatch(r"\d+", lines[-1]):
        die(f"metric_cmd stdout 不是非负整数: {r.stdout!r} / stderr={r.stderr[-300:]!r}")
    return int(lines[-1])


def log_tail(path, n=40):
    if not path or not os.path.exists(path):
        return ""
    r = sh(f"tail -n {n} {json.dumps(path)}")
    return r.stdout


def log_hit(path, pattern):
    if not path or not pattern or not os.path.exists(path):
        return False
    return sh(f"grep -q -- {json.dumps(pattern)} {json.dumps(path)}").returncode == 0


def ancestors():
    """本进程到 init 的整条链，绝不能被 kill_wake 命中（自匹配防护）。"""
    out, pid = set(), os.getpid()
    while pid > 1:
        out.add(pid)
        try:
            with open(f"/proc/{pid}/stat") as f:
                pid = int(f.read().rsplit(")", 1)[1].split()[1])
        except (OSError, IndexError, ValueError):
            break
    return out


def wake_pids(tag):
    """匹配 AGENT_LOOP_WAKE_<tag> 的进程，排除自身祖先链。"""
    pat = re.compile(r"AGENT_LOOP_WAKE_" + re.escape(tag) + r"\b")
    mine = ancestors()
    out = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or int(pid) in mine:
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                cmdline = f.read().replace(b"\0", b" ").decode("utf-8", "replace")
        except OSError:
            continue
        if pat.search(cmdline):
            out.append(int(pid))
    return out


def kill_wake(tag, st=None):
    """kill 本 tag 的 wake：state 里记的 arm pid + 命令行含 AGENT_LOOP_WAKE_<tag> 的遗留进程。"""
    mine = ancestors()
    pids = set(wake_pids(tag))
    if st and st.get("wake_pid"):
        pids.add(int(st["wake_pid"]))
    killed = []
    for pid in pids - mine:
        try:
            os.kill(pid, signal.SIGTERM)
            killed.append(pid)
        except OSError:
            pass
    if st:
        st["wake_pid"] = None
    return killed


def script_of(launch_cmd):
    for tok in (launch_cmd or "").split():
        if tok.endswith(".sh") and tok.startswith("/"):
            return tok
    return None


# ---------------------------------------------------------------- 汇报


def report(st, extra_lines):
    job = st["queue"][st["current"]]
    script = script_of(job.get("launch_cmd"))
    lines = [
        f"本机地址：{st.get('ip') or '—'}",
        f"总卡数：{st.get('global_gpus') or '—'}",
        f"完整脚本：{script or '—（launch_cmd 未写成参数写死的独立脚本，违反 hard rule 8）'}",
        f"日志目录：{job.get('log_dir') or '—'}",
        f"输出目录：{job.get('output_dir') or '—'}",
        f"任务序号：第 {st['current'] + 1} 项 / 共 {len(st['queue'])} 项",
    ]
    lines += extra_lines
    print("\n".join(lines))


def progress_lines(st, delay):
    job = st["queue"][st["current"]]
    target = job.get("metric_target") or 0
    cur = job.get("metric_now") or 0
    pct = f"{cur * 100 // target}%" if target else "—"
    started = parse_dt(st.get("started_at"))
    elapsed = hm((now_dt() - started).total_seconds()) if started else "—"
    eq = parse_dt(st.get("eta_queue"))
    remain = hm((eq - now_dt()).total_seconds()) if eq else "—"
    return [
        f"下次检查：{st.get('next_wake') or '—'}（delay={delay}s）" if delay else "下次检查：—",
        f"本作业：{cur}/{target or '—'}（{pct}），预计 {st.get('eta') or '—'} 完成",
        f"任务队列：预计 {st.get('eta_queue') or '—'} 完成",
        f"已用/剩余：{elapsed} / {remain}",
    ]


# ---------------------------------------------------------------- DELAY / ETA


def plan_timing(st):
    """返回 delay 秒；同时写 eta / eta_queue。无速率信息则 eta 置 null。"""
    job = st["queue"][st["current"]]
    t = now_dt()
    started = parse_dt(job.get("started_at"))
    cur = job.get("metric_now") or 0
    target = job.get("metric_target") or 0

    if cur == 0 or not started:
        st["eta"] = st["eta_queue"] = None
        return 120

    elapsed = max(1.0, (t - started).total_seconds())
    rate = cur / elapsed
    if rate <= 0:
        st["eta"] = st["eta_queue"] = None
        return 600

    remain_sec = max(0.0, (target - cur) / rate)
    queue_remain = remain_sec
    for j in st["queue"][st["current"] + 1 :]:
        if j.get("status") in ("pending", "running"):
            queue_remain += (j.get("metric_target") or 0) / rate
    st["eta"] = (t + timedelta(seconds=remain_sec)).strftime(MIN_FMT)
    st["eta_queue"] = (t + timedelta(seconds=queue_remain)).strftime(MIN_FMT)

    delay = int(min(3600, max(60, 0.8 * remain_sec)))
    dl = parse_dt(st.get("deadline"))
    if dl:
        left = (dl - t).total_seconds()
        if left <= 0:
            return -1
        delay = int(min(delay, max(60, left)))
    return delay


# ---------------------------------------------------------------- commands


def cmd_new(a):
    tag = a.tag or re.sub(r"^launch_", "", os.path.basename(script_of(a.launch_cmd) or a.launch_cmd).rsplit(".", 1)[0])
    tag = re.sub(r"[^0-9A-Za-z_]", "_", tag) or "job"
    base, n = tag, 1
    while os.path.exists(state_path(tag)):
        n += 1
        tag = f"{base}_{n}"
    ip = sh("hostname -I | awk '{print $1}'").stdout.strip() or None
    st = {
        "schema": 2,
        "updated_at": now_dt().strftime(TIME_FMT),
        "started_at": None,
        "current": 0,
        "queue_complete": False,
        "autonomous": bool(a.autonomous),
        "deadline": a.deadline,
        "wake_tag": tag,
        "ip": ip,
        "global_gpus": a.global_gpus,
        "next_wake": None,
        "wake_pid": None,
        "eta": None,
        "eta_queue": None,
        "queue": [new_job(0, a)],
        "note": "",
    }
    save(st)
    print(f"tag={tag} state={state_path(tag)}")
    print_audit(a.launch_cmd)
    print(f"launch: {st['queue'][0]['launch_cmd']}")
    print("ACTION=launch")


def new_job(jid, a):
    return {
        "id": jid,
        "status": "pending",
        "launch_cmd": a.launch_cmd,
        "log": a.log,
        "log_dir": a.log_dir or (os.path.dirname(a.log) if a.log else None),
        "output_dir": a.output_dir,
        "started_at": None,
        "metric_name": a.metric_name or "items",
        "metric_cmd": a.metric_cmd,
        "done_grep": a.done_grep or "",
        "metric_now": 0,
        "metric_target": a.metric_target,
        "metric_prev": 0,
        "stall_count": 0,
        "last_fail": "",
        "retry": "",
        "note": a.note or "",
    }


def audit_launch(launch_cmd):
    """扫启动脚本，返回告警列表。经验性检查集中在此，不写进 SKILL.md。"""
    w = []
    script = script_of(launch_cmd)
    if not script:
        return ["launch_cmd 不是绝对路径的独立 .sh 脚本：参数不入库，事后无法还原这批结果的配置"]
    if re.search(r"^\s*\w+=\S+\s+(bash|sh)\b", launch_cmd or ""):
        w.append("launch_cmd 在命令行挂了 env：漏传会静默回落到脚本默认值（通常是上次实验的配置）")
    if not os.path.exists(script):
        return w + [f"脚本不存在: {script}"]
    with open(script, errors="replace") as f:
        lines = f.read().splitlines()

    code = [(i + 1, l) for i, l in enumerate(lines) if l.strip() and not l.strip().startswith("#")]
    if code and re.match(r"^\s*exec\s+\S", code[-1][1]):
        w.append(f"{script}:{code[-1][0]} 以 exec 收尾：exec 替换本进程，trap 和结尾行都不会执行")

    trap_fn = None
    for ln, l in code:
        m = re.search(r"^\s*trap\s+['\"]?([A-Za-z_][\w]*)", l)
        if m:
            trap_fn, trap_ln = m.group(1), ln
    if trap_fn:
        dup = [ln for ln, l in code if ln > trap_ln and re.match(rf"^\s*{trap_fn}\s*$", l)]
        if dup:
            w.append(f"{script}:{dup[0]} 在 trap({trap_fn}) 之外又调了一次恢复：两条都触发会起双份实例互抢显存")

    for ln, l in code:
        if re.search(r"\$\{[A-Z_]+:-", l):
            w.append(f"{script}:{ln} 身份参数留了 ${{VAR:-默认}} 覆盖口，外部 env 可静默改配置")
            break
    for ln, l in code:
        m = re.search(r">>?\s*([^\s|&;>]+)", l)
        if m and not m.group(1).startswith(("/", "$", "&")):
            w.append(f"{script}:{ln} 日志重定向到相对路径 {m.group(1)}：cwd 一变就写飞，且 symlink 只读")
            break
    return w


def print_audit(launch_cmd):
    for msg in audit_launch(launch_cmd):
        print(f"WARN: {msg}")


def cmd_doctor(a):
    cmds = [a.launch_cmd] if a.launch_cmd else [j["launch_cmd"] for j in load(a.tag)["queue"]]
    bad = 0
    for c in cmds:
        w = audit_launch(c)
        bad += len(w)
        print(f"--- {c}")
        print("\n".join(f"WARN: {m}" for m in w) or "OK")
    print(f"warnings={bad}")


def cmd_add(a):
    st = load(a.tag)
    st["queue"].append(new_job(len(st["queue"]), a))
    st["updated_at"] = now_dt().strftime(TIME_FMT)
    save(st)
    print_audit(a.launch_cmd)
    print(f"added queue[{len(st['queue']) - 1}]  ACTION=arm")


def cmd_started(a):
    """agent 已 bash 起当前/下一 pending 项后调用。"""
    st = load(a.tag)
    q = st["queue"]
    if q[st["current"]].get("status") in ("success", "failed", "cancelled"):
        nxt = next((j["id"] for j in q if j.get("status") == "pending"), None)
        if nxt is None:
            die("没有 pending 项可启动")
        st["current"] = nxt
    job = q[st["current"]]
    t = now_dt().strftime(TIME_FMT)
    job.update(
        status="running", started_at=t, metric_prev=0, metric_now=0, stall_count=0
    )
    if a.pid:
        job["pid"] = a.pid
    st["started_at"] = st.get("started_at") or t
    st["updated_at"] = t
    save(st)
    print(f"queue[{job['id']}] running since {t}  ACTION=arm")


def cmd_check(a):
    st = load(a.tag)
    if st.get("queue_complete"):
        killed = kill_wake(a.tag, st)
        save(st)
        report(st, [f"任务队列完成：{st.get('updated_at') or '—'}", terminal_elapsed(st)])
        print(f"killed_wake={killed or '-'}")
        print("ACTION=terminal")
        return

    job = st["queue"][st["current"]]
    if job.get("status") == "pending":
        print_audit(job["launch_cmd"])
        print(f"queue[{job['id']}] 尚未启动: {job['launch_cmd']}")
        print("ACTION=launch")
        return

    cur = run_metric(job)
    prev = job.get("metric_now") or 0
    target = job.get("metric_target") or 0
    done = log_hit(job.get("log"), job.get("done_grep"))

    if done or (target and cur >= target):
        job["status"] = "success"
    elif cur > prev:
        job["stall_count"] = 0
    else:
        job["stall_count"] = (job.get("stall_count") or 0) + 1
    job["metric_prev"], job["metric_now"] = prev, cur

    tail = log_tail(job.get("log"))
    fail = FAIL_PAT.search(tail)
    if job["status"] != "success" and fail and cur == prev:
        job["last_fail"] = fail.group(0)

    st["updated_at"] = now_dt().strftime(TIME_FMT)

    if job["status"] == "success":
        nxt = next((j for j in st["queue"] if j.get("status") == "pending"), None)
        if nxt:
            st["next_wake"] = None
            save(st)
            report(st, [f"本项完成：{job['metric_name']} {cur}/{target}", f"下一项：queue[{nxt['id']}] {nxt['launch_cmd']}"])
            print_audit(nxt["launch_cmd"])
            print("ACTION=launch")
        else:
            st["queue_complete"] = True
            st["next_wake"] = st["eta"] = st["eta_queue"] = None
            killed = kill_wake(a.tag, st)
            save(st)
            report(st, [f"任务队列完成：{st['updated_at']}", terminal_elapsed(st)])
            print(f"killed_wake={killed or '-'}  记得归还独占资源（GPU 占卡）后再收工")
            print("ACTION=terminal")
        return

    delay = plan_timing(st)
    if delay < 0:
        st["next_wake"] = None
        save(st)
        report(st, [f"已超过 deadline {st['deadline']}，停队不再 arm"] + progress_lines(st, 0))
        print("ACTION=needs_human")
        return

    st["next_wake"] = (now_dt() + timedelta(seconds=delay)).strftime(MIN_FMT)
    save(st)

    if job["stall_count"] >= 2:
        report(st, [f"停滞 {job['stall_count']} 轮（{job['metric_name']} 停在 {cur}）"] + progress_lines(st, delay))
        print(f"--- log tail: {job.get('log')}")
        print(tail.rstrip())
        if job.get("liveness_cmd"):
            print(f"--- liveness: {sh(job['liveness_cmd']).stdout.strip()}")
        print(f"last_fail={job.get('last_fail') or '—'} retry={job.get('retry') or '—'} "
              f"autonomous={st.get('autonomous')}")
        print("ACTION=hang")
        return

    report(st, progress_lines(st, delay))
    print(f"ACTION=arm delay={delay}")


def terminal_elapsed(st):
    started = parse_dt(st.get("started_at"))
    end = parse_dt(st.get("updated_at")) or now_dt()
    return f"总耗时：{hm((end - started).total_seconds()) if started else '—'}"


def cmd_arm(a):
    st = load(a.tag)
    tag = st["wake_tag"]
    if st.get("queue_complete"):
        die("queue_complete=true，不该 arm（应 kill wake）")
    delay = a.delay
    if delay is None:
        nw = parse_dt(st.get("next_wake"))
        delay = int((nw - now_dt()).total_seconds()) if nw else 120
    delay = max(60, min(3600, delay))
    killed = kill_wake(tag, st)
    st["wake_pid"] = os.getpid()
    st["next_wake"] = (now_dt() + timedelta(seconds=delay)).strftime(MIN_FMT)
    st["updated_at"] = now_dt().strftime(TIME_FMT)
    save(st)
    print(f"armed {tag} delay={delay}s next_wake={st['next_wake']} killed={killed or '-'}",
          flush=True)
    time.sleep(delay)
    print(f"AGENT_LOOP_WAKE_{tag}", flush=True)


def cmd_stop(a):
    st = load(a.tag)
    killed = kill_wake(a.tag, st)
    save(st)
    print(f"killed={killed or '-'}")


def cmd_list(_a):
    if not os.path.isdir(STATE_DIR):
        print("(no state dir)")
        return
    for fn in sorted(os.listdir(STATE_DIR)):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(STATE_DIR, fn)) as f:
                st = json.load(f)
        except (OSError, ValueError):
            continue
        job = st["queue"][st.get("current", 0)]
        print(f"{st.get('wake_tag')}\tcomplete={st.get('queue_complete')}\t"
              f"{job.get('status')}\t{job.get('metric_now')}/{job.get('metric_target')}\t"
              f"{job.get('note') or job.get('launch_cmd')}")


def main():
    p = argparse.ArgumentParser(prog="wake.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    def job_args(sp):
        sp.add_argument("--launch-cmd", required=True)
        sp.add_argument("--metric-cmd", required=True)
        sp.add_argument("--metric-target", type=int, required=True)
        sp.add_argument("--log")
        sp.add_argument("--log-dir")
        sp.add_argument("--output-dir")
        sp.add_argument("--metric-name")
        sp.add_argument("--done-grep")
        sp.add_argument("--note")

    sp = sub.add_parser("new", help="建队列（不自动启动）")
    job_args(sp)
    sp.add_argument("--tag")
    sp.add_argument("--global-gpus", type=int)
    sp.add_argument("--deadline")
    sp.add_argument("--autonomous", action="store_true")
    sp.set_defaults(func=cmd_new)

    sp = sub.add_parser("add", help="追加 pending job")
    job_args(sp)
    sp.add_argument("--tag", required=True)
    sp.set_defaults(func=cmd_add)

    sp = sub.add_parser("started", help="已启动当前/下一 pending 项")
    sp.add_argument("--tag", required=True)
    sp.add_argument("--pid", type=int)
    sp.set_defaults(func=cmd_started)

    sp = sub.add_parser("check", help="度量、更新 state、汇报、输出 ACTION")
    sp.add_argument("--tag", required=True)
    sp.set_defaults(func=cmd_check)

    sp = sub.add_parser("arm", help="清旧 wake 后 sleep 并 echo AGENT_LOOP_WAKE_<tag>")
    sp.add_argument("--tag", required=True)
    sp.add_argument("--delay", type=int)
    sp.set_defaults(func=cmd_arm)

    sp = sub.add_parser("doctor", help="体检启动脚本（exec 收尾 / 双恢复 / env 覆盖 / 相对路径日志）")
    sp.add_argument("--tag")
    sp.add_argument("--launch-cmd")
    sp.set_defaults(func=cmd_doctor)

    sp = sub.add_parser("stop", help="仅 kill 本 tag wake")
    sp.add_argument("--tag", required=True)
    sp.set_defaults(func=cmd_stop)

    sp = sub.add_parser("list", help="列出各队列状态")
    sp.set_defaults(func=cmd_list)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()

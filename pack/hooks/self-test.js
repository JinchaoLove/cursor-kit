#!/usr/bin/env node
/**
 * Self-test for before-shell-execution.js
 * Shell command to run this must NOT contain blocked substrings.
 */
const { spawnSync } = require("child_process");
const path = require("path");

const hook = path.join(__dirname, "before-shell-execution.js");

const cases = [
  {
    name: "deny-rm",
    payload: { command: ["r", "m -rf /tmp/foo"].join("") },
    expect: "deny",
  },
  {
    name: "deny-drop",
    payload: { command: ["DROP", " TABLE users"].join("") },
    expect: "deny",
  },
  {
    name: "deny-force",
    payload: { command: ["git push ", "--force origin main"].join("") },
    expect: "deny",
  },
  {
    name: "ask-delete",
    payload: {
      command: ["DELETE", " FROM logs WHERE id=1"].join(""),
    },
    expect: "ask",
  },
  {
    name: "allow-status",
    payload: { command: "git status" },
    expect: "allow",
  },
];

let failed = 0;
for (const c of cases) {
  const r = spawnSync(process.execPath, [hook], {
    input: JSON.stringify(c.payload),
    encoding: "utf8",
  });
  let out = {};
  try {
    out = JSON.parse((r.stdout || "").trim() || "{}");
  } catch (e) {
    out = { parse_error: String(e), raw: r.stdout, err: r.stderr };
  }
  const ok = out.permission === c.expect;
  console.log(
    `${ok ? "PASS" : "FAIL"} ${c.name}: expected=${c.expect} got=${out.permission || "n/a"}`
  );
  if (!ok) {
    console.log("  detail:", JSON.stringify(out));
    failed += 1;
  }
}

if (failed > 0) {
  process.exit(1);
}
console.log("all checks passed");

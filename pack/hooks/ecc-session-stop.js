#!/usr/bin/env node
/**
 * Cursor stop — write a lightweight session stub for continuous learning.
 * Does not auto-create instincts (requires explicit user approval via ecc-instincts).
 */
const fs = require("fs");
const path = require("path");

function readStdin() {
  try {
    return fs.readFileSync(0, "utf8");
  } catch {
    return "{}";
  }
}

function main() {
  let input = {};
  try {
    input = JSON.parse(readStdin() || "{}");
  } catch {
    input = {};
  }

  let workspaceRoot = process.cwd();
  if (Array.isArray(input.workspace_roots) && input.workspace_roots[0]) {
    workspaceRoot = input.workspace_roots[0];
  }

  try {
    const sessionDir = path.join(workspaceRoot, ".cursor", "ecc", "sessions");
    fs.mkdirSync(sessionDir, { recursive: true });

    const ts = new Date();
    const stamp = ts.toISOString().replace(/[:.]/g, "-");
    const file = path.join(sessionDir, `${stamp}.md`);

    const status = input.status || input.reason || "unknown";
    const body = [
      "---",
      `kind: session-stub`,
      `status: ${JSON.stringify(String(status))}`,
      `created: ${ts.toISOString()}`,
      "trust: unreviewed",
      "---",
      "",
      "# Session stub",
      "",
      "Auto-saved by `ecc-session-stop` hook.",
      "Say「学习本会话」to extract instincts via `ecc-instincts` (confirm before write).",
      "",
      "## Hook payload (redacted keys only)",
      "",
      `- status: ${String(status)}`,
      `- conversation_id: ${input.conversation_id || "n/a"}`,
      "",
    ].join("\n");

    fs.writeFileSync(file, body, "utf8");
  } catch (err) {
    // Fail open: never block the agent loop on persistence errors.
    process.stderr.write(`[ecc-session-stop] ${err && err.message ? err.message : err}\n`);
  }

  process.stdout.write("{}\n");
}

main();

import { readFile } from "node:fs/promises";
import { access } from "node:fs/promises";
import { spawn } from "node:child_process";

const required = [
  "index.html",
  "api/latest-reels.js",
  "api/run-reels.js",
  "api/scout.js",
  "api/today.js",
  "api/trends.js",
  "api/health.js"
];

async function exists(path) {
  try { await access(path); return true; } catch { return false; }
}

async function checkSyntax(path) {
  await new Promise((resolve, reject) => {
    const child = spawn(process.execPath, ["--check", path], { stdio: "inherit" });
    child.on("error", reject);
    child.on("exit", code => code === 0 ? resolve() : reject(new Error(`Syntax check failed: ${path}`)));
  });
}

for (const path of required) {
  if (!(await exists(path))) throw new Error(`Missing required deployment file: ${path}`);
}

const html = await readFile("index.html", "utf8");
if (!/^<!doctype html>/i.test(html.trim())) throw new Error("index.html is missing a valid doctype.");
if (!/<html\b/i.test(html) || !/<\/html>/i.test(html)) throw new Error("index.html is incomplete.");
if (!/<meta[^>]+name=["']viewport["']/i.test(html)) throw new Error("index.html is missing the viewport meta tag.");

for (const path of required.filter(p => p.endsWith(".js"))) {
  await checkSyntax(path);
}

console.log("Festival of Bharat Vercel build validation passed.");
console.log(`Checked ${required.length} required files and ${required.filter(p => p.endsWith(".js")).length} API syntax targets.`);

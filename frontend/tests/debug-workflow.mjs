import { chromium } from "playwright";
import path from "node:path";
import os from "node:os";

const baseUrl = process.env.WEB_BASE_URL || "http://127.0.0.1:5174";
const browser = await chromium.launch({
  headless: true,
  executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
});
const page = await browser.newPage({ viewport: { width: 1440, height: 980 } });
const errors = [];
page.on("console", (m) => {
  if (m.type() === "error") errors.push(m.text());
});
page.on("pageerror", (e) => errors.push("pageerror: " + e.message));

await page.goto(baseUrl, { waitUntil: "networkidle" });
await page.getByRole("button", { name: "交互推演" }).click();
await page.waitForTimeout(1200);
await page.screenshot({ path: path.join(os.tmpdir(), "dbg-workflow.png"), fullPage: true });
const texts = await page.locator("button, h1, h2, h3, label").evaluateAll((nodes) =>
  nodes.map((n) => `${n.tagName}:${n.textContent.trim().slice(0, 30)}`).filter((t) => t.length > 4));
console.log("UI:", JSON.stringify(texts.slice(0, 80), null, 1));
console.log("ERRORS:", JSON.stringify(errors.slice(0, 6), null, 1));
await browser.close();

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
await page.getByRole("button", { name: /开始推演/ }).click();
await page.getByText(/^compare_[a-f0-9]+$/).waitFor({ timeout: 20000 });
await page.screenshot({ path: path.join(os.tmpdir(), "dbg-overview.png"), fullPage: true });

const buttons = await page.locator("button").evaluateAll((nodes) =>
  nodes.map((n) => ({ text: n.textContent.trim(), role: n.getAttribute("role") })).filter((b) => b.text));
const headings = await page.locator("h1,h2,h3,h4").evaluateAll((nodes) =>
  nodes.map((n) => ({ tag: n.tagName, text: n.textContent.trim() })));
console.log("BUTTONS:", JSON.stringify(buttons, null, 1));
console.log("HEADINGS:", JSON.stringify(headings, null, 1));

const zhouyi = page.getByRole("button", { name: "周易" });
console.log("zhouyi buttons count:", await zhouyi.count());
try {
  await zhouyi.last().click();
  await page.waitForTimeout(1500);
  const after = await page.locator("h1,h2,h3,h4").evaluateAll((nodes) =>
    nodes.map((n) => n.textContent.trim()));
  console.log("HEADINGS AFTER CLICK:", JSON.stringify(after, null, 1));
  await page.screenshot({ path: path.join(os.tmpdir(), "dbg-zhouyi.png"), fullPage: true });
} catch (err) {
  console.log("click failed:", err.message);
}
console.log("ERRORS:", JSON.stringify(errors.slice(0, 10), null, 1));
await browser.close();

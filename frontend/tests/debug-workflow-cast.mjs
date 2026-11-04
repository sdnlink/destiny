import { chromium } from "playwright";

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
await page.getByPlaceholder(/请描述你想求测的事项/).fill("工作机会与团队邀请是否值得接受");
await page.getByRole("button", { name: "创建推演会话" }).click();
await page.waitForTimeout(1200);
const dump = async (tag) => {
  const items = await page.locator("button, h1, h2, h3, h4").evaluateAll((nodes) =>
    nodes.map((n) => `${n.tagName}:${n.textContent.trim().slice(0, 26)}`).filter((t) => t.length > 4));
  console.log(tag, JSON.stringify(items.slice(0, 60), null, 1));
};
await dump("AFTER CREATE:");
const castButton = page.getByRole("button", { name: /提交并起盘|直接起盘|排盘/ }).first();
if (await castButton.count()) {
  await castButton.click();
  await page.waitForTimeout(2500);
  await dump("AFTER CAST:");
  await page.screenshot({ path: "C:\\Users\\yulintao\\AppData\\Local\\Doubao\\User Data\\Default\\.doubao\\agent_mode\\workspace\\.sessions\\38450182690764802\\agents\\m_0cw391uvM9x\\shots\\dbg-workflow-cast.png", fullPage: true });
  const structured = page.getByRole("button", { name: "结构化数据" });
  if (await structured.count()) {
    await structured.click();
    await page.waitForTimeout(800);
    const visibleText = await page.locator(".workflow-structured, .structured-display, body").first().innerText();
    console.log("STRUCTURED TEXT HEAD:", visibleText.slice(0, 600));
    await page.screenshot({ path: "C:\\Users\\yulintao\\AppData\\Local\\Doubao\\User Data\\Default\\.doubao\\agent_mode\\workspace\\.sessions\\38450182690764802\\agents\\m_0cw391uvM9x\\shots\\dbg-workflow-structured.png", fullPage: true });
  }
}
console.log("ERRORS:", JSON.stringify(errors.slice(0, 8), null, 1));
await browser.close();

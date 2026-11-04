import { chromium } from "playwright";

const baseUrl = process.env.WEB_BASE_URL || "http://127.0.0.1:5174";
const browser = await chromium.launch({
  headless: true,
  executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
});
const page = await browser.newPage({ viewport: { width: 1440, height: 980 } });
await page.goto(baseUrl, { waitUntil: "networkidle" });
await page.getByRole("button", { name: /开始推演/ }).click();
await page.getByText(/^compare_[a-f0-9]+$/).waitFor({ timeout: 20000 });

const tabs = [
  "总览",
  "输入与历法",
  "周易",
  "梅花易数",
  "六爻",
  "大六壬",
  "奇门遁甲",
  "八字命理",
  "紫微斗数",
  "阳宅风水",
  "对照分析",
  "结论建议",
];
const result = [];
for (const tab of tabs) {
  const button = page.locator("button", { hasText: new RegExp(`^${tab}$`) }).last();
  await button.click();
  await page.waitForTimeout(400);
  const headings = await page.locator("h1,h2,h3,h4").evaluateAll((nodes) =>
    nodes.map((n) => n.textContent.trim()).filter(Boolean));
  result.push({ tab, headings });
}
console.log(JSON.stringify(result, null, 1));
await browser.close();

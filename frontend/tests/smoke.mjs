import { chromium } from "playwright";

const baseUrl = process.env.WEB_BASE_URL || "http://127.0.0.1:5173";
const executablePath = process.env.CHROME_BIN || "/usr/bin/google-chrome";
const browser = await chromium.launch({ executablePath, headless: true });

async function assertNoOverflow(page, label) {
  const dimensions = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
  }));
  if (dimensions.scroll > dimensions.viewport + 1) {
    throw new Error(`${label} horizontal overflow: ${dimensions.scroll} > ${dimensions.viewport}`);
  }
}

const desktop = await browser.newPage({ viewport: { width: 1440, height: 980 }, deviceScaleFactor: 1 });
const consoleErrors = [];
desktop.on("console", (message) => {
  if (message.type() === "error") consoleErrors.push(message.text());
});

await desktop.goto(baseUrl, { waitUntil: "networkidle" });
await desktop.getByRole("heading", { name: "推演参数" }).waitFor();
await assertNoOverflow(desktop, "desktop input");
await desktop.screenshot({ path: "/tmp/tianji-input-desktop.png", fullPage: true });

await desktop.getByRole("button", { name: /开始推演/ }).click();
await desktop.getByText(/^compare_[a-f0-9]+$/).waitFor({ timeout: 15000 });
await desktop.getByRole("heading", { name: "近期事项推演" }).waitFor();
await desktop.getByRole("button", { name: "周易" }).last().click();
await desktop.getByRole("heading", { name: "周易卦盘" }).waitFor();
await desktop.getByRole("button", { name: "梅花易数" }).click();
await desktop.getByRole("heading", { name: "梅花易数" }).waitFor();
await desktop.getByRole("button", { name: "六爻" }).last().click();
await desktop.getByRole("heading", { name: "六爻纳甲盘" }).waitFor();
await desktop.getByText("辛酉", { exact: true }).first().waitFor();
await desktop.screenshot({ path: "/tmp/tianji-liuyao-desktop.png", fullPage: true });
await desktop.getByRole("button", { name: "大六壬" }).click();
await desktop.getByRole("heading", { name: "大六壬盘" }).waitFor();
await desktop.getByRole("heading", { name: "天地盘与十二天将" }).waitFor();
await desktop.getByRole("heading", { name: "三传" }).waitFor();
await desktop.screenshot({ path: "/tmp/tianji-liuren-desktop.png", fullPage: true });
await desktop.getByRole("button", { name: "结论建议" }).click();
await desktop.getByRole("heading", { name: "事项结论与详细建议" }).waitFor();
await desktop.getByRole("heading", { name: "建议行动" }).waitFor();
await desktop.getByRole("heading", { name: "书籍中的明确观点" }).waitFor();
await desktop.getByRole("link", { name: /查看来源/ }).first().waitFor();
await desktop.getByText("综合说明", { exact: true }).waitFor();
await assertNoOverflow(desktop, "desktop result");
await desktop.screenshot({ path: "/tmp/tianji-result-desktop.png", fullPage: true });

await desktop.getByTitle("规则目录").click();
const rulesDialog = desktop.getByRole("dialog", { name: "规则目录" });
await rulesDialog.waitFor();
await rulesDialog.getByText("CAL-NORMALIZE-001", { exact: true }).waitFor();
await rulesDialog.getByText("LR-TRANSMISSION-001", { exact: true }).waitFor();
await desktop.getByRole("button", { name: "关闭规则目录" }).click();

const mobile = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
await mobile.goto(baseUrl, { waitUntil: "networkidle" });
await assertNoOverflow(mobile, "mobile input");
await mobile.getByRole("button", { name: /开始推演/ }).click();
await mobile.getByText(/^compare_[a-f0-9]+$/).waitFor({ timeout: 15000 });
await mobile.getByRole("button", { name: "周易", exact: true }).click();
await mobile.getByRole("heading", { name: "周易卦盘" }).waitFor();
await mobile.getByRole("button", { name: "结论建议", exact: true }).click();
await mobile.getByRole("heading", { name: "事项结论与详细建议" }).waitFor();
await assertNoOverflow(mobile, "mobile result");
await mobile.screenshot({ path: "/tmp/tianji-result-mobile.png", fullPage: true });

if (consoleErrors.length) {
  throw new Error(`browser console errors:\n${consoleErrors.join("\n")}`);
}

await browser.close();
console.log("browser smoke passed: desktop input/result, rules drawer, and mobile result");

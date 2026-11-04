import os from "node:os";
import path from "node:path";
import { chromium } from "playwright";

const baseUrl = process.env.WEB_BASE_URL || "http://127.0.0.1:5173";
// 不再写死 /usr/bin/google-chrome：未显式指定时用 Playwright 自带浏览器，Windows 上也能跑
const executablePath = process.env.CHROME_BIN;
const launchOptions = { headless: true };
if (executablePath) launchOptions.executablePath = executablePath;
const browser = await chromium.launch(launchOptions);
// 截图落到系统临时目录，不再假设 /tmp 一定存在
const shotDir = process.env.SMOKE_SHOT_DIR || os.tmpdir();
const shot = (name) => path.join(shotDir, name);

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
await desktop.screenshot({ path: shot("tianji-input-desktop.png"), fullPage: true });

await desktop.getByRole("radio", { name: "风水", exact: true }).click();
await desktop.getByLabel("向首方位角").fill("7.4");
await desktop.getByRole("button", { name: "真北测量", exact: true }).click();
await desktop.getByLabel("测量误差 ±").fill("0.2");
await desktop.getByRole("button", { name: /开始推演/ }).click();
await desktop.getByText(/^compare_[a-f0-9]+$/).waitFor({ timeout: 15000 });
await desktop.getByRole("button", { name: "阳宅风水", exact: true }).click();
await desktop.getByRole("heading", { name: "阳宅真北坐向" }).waitFor();
await desktop.getByText("跨越分界", { exact: true }).waitFor();
await desktop.getByText("子、癸", { exact: true }).waitFor();
await assertNoOverflow(desktop, "desktop fengshui result");
await desktop.screenshot({ path: shot("tianji-fengshui-desktop.png"), fullPage: true });

await desktop.goto(baseUrl, { waitUntil: "networkidle" });
await desktop.getByRole("radio", { name: "风水", exact: true }).click();
await desktop.getByRole("button", { name: "多次共识", exact: true }).click();
await desktop.getByLabel("第1次向首读数").fill("359");
await desktop.getByLabel("第2次向首读数").fill("0");
await desktop.getByLabel("第3次向首读数").fill("1");
await desktop.getByRole("button", { name: "真北测量", exact: true }).click();
await desktop.getByLabel("测量误差 ±").fill("0.5");
await desktop.getByRole("button", { name: /开始推演/ }).click();
await desktop.getByText(/^compare_[a-f0-9]+$/).waitFor({ timeout: 15000 });
await desktop.getByRole("button", { name: "阳宅风水", exact: true }).click();
await desktop.getByRole("heading", { name: "阳宅多次测量共识" }).waitFor();
await desktop.getByText("一致", { exact: true }).waitFor();
await desktop.getByText("1.5°", { exact: true }).waitFor();
await desktop.getByRole("heading", { name: "逐次真北读数" }).waitFor();
await assertNoOverflow(desktop, "desktop fengshui consensus");
await desktop.screenshot({ path: shot("tianji-fengshui-consensus-desktop.png"), fullPage: true });

await desktop.goto(baseUrl, { waitUntil: "networkidle" });

await desktop.getByRole("button", { name: /开始推演/ }).click();
await desktop.getByText(/^compare_[a-f0-9]+$/).waitFor({ timeout: 15000 });
await desktop.getByRole("heading", { name: "近期事项推演" }).waitFor();
await desktop.getByRole("button", { name: "周易" }).last().click();
await desktop.getByRole("heading", { name: "周易本变卦象" }).waitFor();
await desktop.getByRole("button", { name: "梅花易数" }).click();
await desktop.getByRole("heading", { name: "梅花易数" }).waitFor();
await desktop.getByRole("button", { name: "六爻" }).last().click();
await desktop.getByRole("heading", { name: "六爻纳甲盘与伏神飞神" }).waitFor();
await desktop.getByRole("columnheader", { name: "纳甲" }).waitFor();
await desktop.screenshot({ path: shot("tianji-liuyao-desktop.png"), fullPage: true });
await desktop.getByRole("button", { name: "大六壬" }).click();
await desktop.getByRole("heading", { name: "大六壬盘" }).waitFor();
await desktop.getByRole("heading", { name: "天地盘与十二天将乘神" }).waitFor();
await desktop.getByRole("heading", { name: "三传" }).waitFor();
await desktop.screenshot({ path: shot("tianji-liuren-desktop.png"), fullPage: true });
await desktop.getByRole("button", { name: "结论建议" }).click();
await desktop.getByRole("heading", { name: "综合推演研判与古籍引证" }).waitFor();
// 解释卡上的三段固定前缀（盘面事实 / 现实指导），用片段匹配避免标点变动即失败
await desktop.getByText("盘面事实：").first().waitFor();
await desktop.getByText("现实指导：").first().waitFor();
await desktop.getByRole("heading", { name: "元会运世" }).waitFor();
await desktop.getByRole("heading", { name: "类象关联" }).waitFor();
await desktop.getByRole("heading", { name: "分阶段落地行动策略" }).waitFor();
await desktop.getByRole("heading", { name: "典籍引证与高价值古籍断语" }).waitFor();
// 文献检索受后端 ENABLE_LITERATURE 控制：有片段则出现来源链接，无片段则出现提示条。
// 这里只校验「区块状态标签」渲染出来，不把某个环境开关固化成断言。
await desktop.locator(".literature-status").first().waitFor();
await assertNoOverflow(desktop, "desktop result");
await desktop.screenshot({ path: shot("tianji-result-desktop.png"), fullPage: true });

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
await mobile.getByRole("heading", { name: "周易本变卦象" }).waitFor();
await mobile.getByRole("button", { name: "结论建议", exact: true }).click();
await mobile.getByRole("heading", { name: "综合推演研判与古籍引证" }).waitFor();
await assertNoOverflow(mobile, "mobile result");
await mobile.screenshot({ path: shot("tianji-result-mobile.png"), fullPage: true });

if (consoleErrors.length) {
  throw new Error(`browser console errors:\n${consoleErrors.join("\n")}`);
}

await browser.close();
console.log("browser smoke passed: fengshui single/consensus, desktop result, rules drawer, and mobile result");

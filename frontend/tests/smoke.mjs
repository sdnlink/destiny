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
await desktop.screenshot({ path: "/tmp/tianji-fengshui-desktop.png", fullPage: true });

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
await desktop.screenshot({ path: "/tmp/tianji-fengshui-consensus-desktop.png", fullPage: true });

await desktop.goto(baseUrl, { waitUntil: "networkidle" });

await desktop.getByRole("button", { name: /开始推演/ }).click();
await desktop.getByText(/^compare_[a-f0-9]+$/).waitFor({ timeout: 15000 });
await desktop.getByRole("heading", { name: "近期事项推演" }).waitFor();
await desktop.getByRole("button", { name: "周易" }).last().click();
await desktop.getByRole("heading", { name: "周易卦盘" }).waitFor();
await desktop.getByRole("button", { name: "梅花易数" }).click();
await desktop.getByRole("heading", { name: "梅花易数" }).waitFor();
await desktop.getByRole("button", { name: "六爻" }).last().click();
await desktop.getByRole("heading", { name: "六爻纳甲盘" }).waitFor();
await desktop.getByRole("columnheader", { name: "纳甲" }).waitFor();
await desktop.screenshot({ path: "/tmp/tianji-liuyao-desktop.png", fullPage: true });
await desktop.getByRole("button", { name: "大六壬" }).click();
await desktop.getByRole("heading", { name: "大六壬盘" }).waitFor();
await desktop.getByRole("heading", { name: "天地盘与十二天将" }).waitFor();
await desktop.getByRole("heading", { name: "三传" }).waitFor();
await desktop.screenshot({ path: "/tmp/tianji-liuren-desktop.png", fullPage: true });
await desktop.getByRole("button", { name: "结论建议" }).click();
await desktop.getByRole("heading", { name: "事项结论与详细建议" }).waitFor();
await desktop.getByRole("heading", { name: "推演对应解释" }).waitFor();
await desktop.getByText("盘面事实", { exact: true }).first().waitFor();
await desktop.getByText("对应解释", { exact: true }).first().waitFor();
await desktop.getByText("现实核实", { exact: true }).first().waitFor();
await desktop.getByRole("heading", { name: "元会运世" }).waitFor();
await desktop.getByRole("heading", { name: "类象关联" }).waitFor();
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
console.log("browser smoke passed: fengshui single/consensus, desktop result, rules drawer, and mobile result");

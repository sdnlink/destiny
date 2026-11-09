import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { chromium } from "playwright";

const baseUrl = process.env.WEB_BASE_URL || "http://127.0.0.1:5173";
// 未显式指定时用 Playwright 自带浏览器，Windows 上也能跑
const executablePath = process.env.CHROME_BIN;
const launchOptions = { headless: true };
if (executablePath) launchOptions.executablePath = executablePath;
const browser = await chromium.launch(launchOptions);
const shotDir = process.env.SMOKE_SHOT_DIR || os.tmpdir();
const shot = (name) => path.join(shotDir, name);

// 导航到某个功能模块页（左侧 NavLink 是可分享 URL 的独立页面）
async function gotoModule(page, label) {
  await page.locator(".app-navigation").getByRole("link", { name: label, exact: true }).click();
}

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

// 首页引导页：每个术数都有独立入口（不再是混在一起的综合推演）
await desktop.goto(baseUrl, { waitUntil: "networkidle" });
await desktop.getByRole("heading", { name: "天机演象" }).waitFor();
await desktop.getByRole("link", { name: "周易" }).first().waitFor();
await assertNoOverflow(desktop, "desktop home");
await desktop.screenshot({ path: shot("tianji-home-desktop.png"), fullPage: true });

// 周易：独立模块页，三数排盘 → 结果 → 结论建议（含古籍引证）
await gotoModule(desktop, "周易");
await desktop.getByRole("heading", { name: "周易" }).waitFor();
await desktop.getByText("三数排盘").click();
await desktop.getByRole("button", { name: "开始起卦" }).click();
await desktop.getByRole("heading", { name: "周易本变卦象" }).waitFor({ timeout: 20000 });
await desktop.getByRole("tab", { name: "结论建议" }).click();
await desktop.getByRole("heading", { name: "综合研判与古籍引证" }).waitFor({ timeout: 20000 });
await desktop.getByText("盘面事实：").first().waitFor();
await desktop.getByText("现实指导：").first().waitFor();
await desktop.getByRole("heading", { name: "元会运世" }).waitFor();
await desktop.getByRole("heading", { name: "类象关联" }).waitFor();
await desktop.getByRole("heading", { name: "分阶段落地行动策略" }).waitFor();
await desktop.getByRole("heading", { name: "典籍引证与高价值古籍断语" }).waitFor();
await desktop.locator(".literature-status").first().waitFor();
await assertNoOverflow(desktop, "desktop zhouyi result");
await desktop.screenshot({ path: shot("tianji-zhouyi-desktop.png"), fullPage: true });

// 六爻：独立模块页，手工排盘 → 铜钱排盘 → 指定用神
await gotoModule(desktop, "六爻");
await desktop.getByRole("heading", { name: "六爻" }).waitFor();
await desktop.getByText("手工排盘").click();
await desktop.getByRole("button", { name: "开始起卦" }).click();
await desktop.getByRole("heading", { name: "六爻纳甲盘与伏神飞神" }).waitFor({ timeout: 20000 });
await desktop.getByText("铜钱排盘").click();
await desktop.getByRole("button", { name: "开始起卦" }).click();
await desktop.getByRole("heading", { name: "六爻纳甲盘与伏神飞神" }).waitFor({ timeout: 20000 });
await desktop.getByLabel(/用神焦点/).selectOption("求财买卖");
await desktop.getByRole("button", { name: "开始起卦" }).click();
await desktop.getByRole("heading", { name: /用神焦点 · 求财买卖/ }).waitFor({ timeout: 20000 });
await assertNoOverflow(desktop, "desktop liuyao workspace");
await desktop.screenshot({ path: shot("tianji-liuyao-desktop.png"), fullPage: true });

// 八字命理：独立模块页，本命盘 → 流年 → 生平时间轴
await gotoModule(desktop, "八字命理");
await desktop.getByRole("heading", { name: "八字命理" }).waitFor();
await desktop.getByLabel("公历出生日期时间").fill("1984-02-10T10:00");
await desktop.getByLabel("出生地时区").fill("Asia/Shanghai");
await desktop.getByRole("button", { name: "排本命盘" }).click();
await desktop.getByRole("heading", { name: "八字四柱与大运排盘" }).waitFor({ timeout: 20000 });
await desktop.getByRole("tab", { name: /流年/ }).click();
await desktop.getByLabel("起始年份").fill("2026");
await desktop.getByLabel("年数").fill("5");
await desktop.getByRole("button", { name: "生成流年" }).click();
await desktop.getByRole("heading", { name: "流年逐年事实（子平岁运）" }).waitFor({ timeout: 20000 });
await desktop.getByText("BZ-LIUNIAN-001", { exact: true }).waitFor();
await desktop.getByText("2026", { exact: true }).first().waitFor();
await desktop.getByRole("tab", { name: /生平时间轴/ }).click();
await desktop.getByRole("button", { name: "生成时间轴" }).click();
await desktop.getByText(/月令提纲：/).waitFor({ timeout: 20000 });
const [lifelineDownload] = await Promise.all([
  desktop.waitForEvent("download"),
  desktop.getByRole("button", { name: "导出报告" }).click(),
]);
const lifelinePath = await lifelineDownload.path();
if (!lifelinePath) throw new Error("lifeline report download missing file");
const lifelineReport = fs.readFileSync(lifelinePath, "utf8");
if (!lifelineReport.includes("# 八字 · 生平时间轴") || !lifelineReport.includes("## 逐年事实")) {
  throw new Error("lifeline report content is not the current timeline report");
}
await assertNoOverflow(desktop, "desktop bazi");
await desktop.screenshot({ path: shot("tianji-bazi-desktop.png"), fullPage: true });

// 紫微斗数：独立模块页
await gotoModule(desktop, "紫微斗数");
await desktop.getByRole("heading", { name: "紫微斗数" }).waitFor();
await desktop.getByRole("button", { name: "排紫微盘" }).click();
await desktop.getByRole("heading", { name: "紫微斗数全景天盘" }).waitFor({ timeout: 20000 });
await desktop.getByRole("heading", { name: "大限区间" }).waitFor();
await desktop.getByText(/当前约 \d+ 岁，落在/).waitFor();
await desktop.screenshot({ path: shot("tianji-ziwei-desktop.png"), fullPage: true });

// 奇门遁甲 / 大六壬：独立模块页
await gotoModule(desktop, "奇门遁甲");
await desktop.getByRole("heading", { name: "奇门遁甲" }).waitFor();
await desktop.getByRole("button", { name: "开始排盘" }).click();
await desktop.getByRole("heading", { name: "时家转盘奇门遁甲" }).waitFor({ timeout: 20000 });
await gotoModule(desktop, "大六壬");
await desktop.getByRole("heading", { name: "大六壬" }).waitFor();
await desktop.getByRole("button", { name: "开始排盘" }).click();
await desktop.getByRole("heading", { name: "大六壬盘" }).waitFor({ timeout: 20000 });
await assertNoOverflow(desktop, "desktop spacetime");
await desktop.screenshot({ path: shot("tianji-spacetime-desktop.png"), fullPage: true });

// 阳宅风水：独立模块页，单次坐向 / 多次共识 / 八宅 / 玄空 / 房屋档案
await gotoModule(desktop, "阳宅风水");
await desktop.getByRole("heading", { name: "阳宅风水" }).waitFor();
await desktop.getByLabel("向首方位角").fill("7.4");
await desktop.getByRole("button", { name: "真北测量", exact: true }).click();
await desktop.getByLabel("测量误差 ±").fill("0.2");
await desktop.getByRole("button", { name: "生成阳宅坐向" }).click();
await desktop.getByRole("heading", { name: "阳宅真北坐向与二十四山" }).waitFor({ timeout: 20000 });
await desktop.getByText("跨越分界", { exact: true }).waitFor();
await desktop.getByText("子、癸", { exact: true }).waitFor();
await assertNoOverflow(desktop, "desktop fengshui workspace");
await desktop.screenshot({ path: shot("tianji-fengshui-desktop.png"), fullPage: true });

await desktop.getByRole("tab", { name: "多次共识" }).click();
await desktop.getByLabel("第1次向首读数").fill("359");
await desktop.getByLabel("第2次向首读数").fill("0");
await desktop.getByLabel("第3次向首读数").fill("1");
await desktop.getByRole("button", { name: "真北测量", exact: true }).click();
await desktop.getByLabel("测量误差 ±").fill("0.5");
await desktop.getByRole("button", { name: "生成阳宅坐向" }).click();
await desktop.getByRole("heading", { name: "阳宅多次测量共识" }).waitFor({ timeout: 20000 });
await desktop.getByText("一致", { exact: true }).waitFor();
await desktop.getByText("1.5°", { exact: true }).waitFor();
await desktop.getByRole("heading", { name: "逐次真北读数" }).waitFor();
await assertNoOverflow(desktop, "desktop fengshui consensus");
await desktop.screenshot({ path: shot("tianji-fengshui-consensus-desktop.png"), fullPage: true });

await desktop.getByRole("tab", { name: "八宅" }).click();
await desktop.getByRole("button", { name: "排八宅盘" }).click();
await desktop.getByRole("heading", { name: "八宅大游年盘" }).waitFor({ timeout: 20000 });
await assertNoOverflow(desktop, "desktop bazhai workspace");
await desktop.screenshot({ path: shot("tianji-fengshui-bazhai-desktop.png"), fullPage: true });

const [bazhaiDownload] = await Promise.all([
  desktop.waitForEvent("download"),
  desktop.getByRole("button", { name: "导出报告" }).click(),
]);
const bazhaiPath = await bazhaiDownload.path();
if (!bazhaiDownload.suggestedFilename().endsWith(".md") || !bazhaiPath) {
  throw new Error("bazhai report download missing markdown file");
}
const bazhaiReport = fs.readFileSync(bazhaiPath, "utf8");
if (!bazhaiReport.includes("# 阳宅风水 · 八宅") || !bazhaiReport.includes("## 大游年歌")) {
  throw new Error("bazhai report content is not the current module report");
}

await desktop.getByRole("tab", { name: "玄空" }).click();
await desktop.getByRole("button", { name: "排玄空盘" }).click();
await desktop.getByRole("heading", { name: "玄空挨星盘" }).waitFor({ timeout: 20000 });
await desktop.getByLabel("附替卦起星盘").check();
await desktop.getByRole("button", { name: "排玄空盘" }).click();
await desktop.getByText("替卦起星盘（工程基线）").waitFor({ timeout: 20000 });
await assertNoOverflow(desktop, "desktop xuankong workspace");
await desktop.screenshot({ path: shot("tianji-fengshui-xuankong-desktop.png"), fullPage: true });

await desktop.getByRole("tab", { name: "房屋档案" }).click();
await desktop.getByText("已存档案", { exact: true }).waitFor();
await desktop.getByRole("button", { name: "刷新" }).waitFor();
await assertNoOverflow(desktop, "desktop fengshui archive");
await desktop.screenshot({ path: shot("tianji-fengshui-archive-desktop.png"), fullPage: true });

// 交互推演（7 步工作流）
await gotoModule(desktop, "交互推演");
const questionBox = desktop.getByPlaceholder(/请描述你想求测的事项/);
await questionBox.waitFor();
await questionBox.fill("工作机会与团队邀请是否值得接受");
await desktop.getByRole("button", { name: "创建推演会话" }).click();
await desktop.getByRole("heading", { name: "起盘前信息补全" }).waitFor();
await desktop.getByRole("button", { name: /提交并起盘|直接起盘/ }).first().click();
await desktop.getByRole("heading", { name: "推演结果" }).waitFor({ timeout: 60000 });
await desktop.locator(".fortune-banner").first().waitFor();
await desktop.getByRole("button", { name: "结构化数据" }).click();
const stepBlocks = desktop.locator(".structured-friendly");
await stepBlocks.first().waitFor();
await desktop.getByText(/历法基线/).first().waitFor();
const calendarLine = await desktop.locator(".structured-friendly").nth(1).innerText();
if (calendarLine.includes("[object Object]")) {
  throw new Error(`历法基线把对象插值成了 [object Object]：${calendarLine.replace(/\n/g, " | ")}`);
}
if (!/年/.test(calendarLine)) {
  throw new Error(`历法基线缺少干支：${calendarLine.replace(/\n/g, " | ")}`);
}
if (!/使用体系/.test(calendarLine)) {
  throw new Error(`步骤2 缺少「使用体系」：${calendarLine.replace(/\n/g, " | ")}`);
}
await desktop.getByRole("button", { name: "交互深化" }).click();
await desktop.getByRole("heading", { name: /交互深化（原始盘面不变/ }).waitFor();
await desktop.locator(".collapsible-header", { hasText: "盘面现状核对" }).click();
await desktop.locator(".collapsible-header", { hasText: "盘面现状核对" }).click();
const interactView = desktop.locator(".interact-view");
await interactView.locator("select").first().selectOption("符合");
await interactView.getByRole("button", { name: "提交" }).first().click();
const historyTab = desktop.getByRole("button", { name: /交互记录\(/ });
await historyTab.waitFor({ timeout: 30000 });
const historyTabLabel = await historyTab.innerText();
if (!/\d/.test(historyTabLabel)) throw new Error(`交互记录页签没有计数：${historyTabLabel}`);
await desktop.screenshot({ path: shot("tianji-workflow-interact.png"), fullPage: false });

await assertNoOverflow(desktop, "desktop workflow result");
await desktop.screenshot({ path: shot("tianji-workflow-desktop.png"), fullPage: true });

// 规则目录抽屉
await desktop.getByTitle("规则目录").click();
const rulesDialog = desktop.getByRole("dialog", { name: "规则目录" });
await rulesDialog.waitFor();
await rulesDialog.getByText("CAL-NORMALIZE-001", { exact: true }).waitFor();
await rulesDialog.getByText("LR-TRANSMISSION-001", { exact: true }).waitFor();
await desktop.getByRole("button", { name: "关闭规则目录" }).click();

// 典籍原文检索
await desktop.getByTitle("在本地典籍库检索原文段落与出处").click();
const classicsDialog = desktop.getByRole("dialog", { name: "典籍原文检索" });
await classicsDialog.waitFor();
await classicsDialog.getByText(/已收录 \d+ 部/).waitFor({ timeout: 20000 });
await classicsDialog.getByLabel("典籍原文关键词").fill("月令");
await classicsDialog.getByRole("button", { name: "检索", exact: true }).click();
await classicsDialog.locator(".classics-hit").first().waitFor({ timeout: 20000 });
await desktop.screenshot({ path: shot("tianji-classics-search-desktop.png"), fullPage: true });
await classicsDialog.getByRole("button", { name: "关闭典籍检索" }).click();

// 历史抽屉与后端会话联动
await desktop.getByRole("button", { name: "历史与案例" }).click();
const serverSessions = desktop.getByRole("region", { name: "后端推演会话" });
await serverSessions.waitFor({ timeout: 15000 });
const serverCards = serverSessions.locator(".history-item-card");
await serverCards.first().waitFor({ timeout: 15000 });
if ((await serverCards.count()) < 1) {
  throw new Error("历史抽屉没有列出任何后端会话");
}
await desktop.screenshot({ path: shot("tianji-history-drawer.png"), fullPage: false });
await serverCards.filter({ hasText: "工作机会与团队邀请是否值得接受" }).first().click();
await desktop.getByRole("heading", { name: "推演结果" }).waitFor({ timeout: 30000 });
await desktop.locator(".fortune-banner").first().waitFor({ timeout: 30000 });
if (await desktop.locator(".history-drawer").count()) {
  throw new Error("从历史抽屉打开会话后抽屉没有关闭");
}
await desktop.screenshot({ path: shot("tianji-history-bridge.png"), fullPage: false });

// 本地存档 → 后端会话（反向通道）
await desktop.getByRole("button", { name: "历史与案例" }).click();
const localHistoryList = desktop.locator(".history-list-wrap").nth(1);
const localCard = localHistoryList.locator(".history-item-card").filter({ hasText: "近期事项推演" }).first();
await localCard.waitFor({ timeout: 15000 });
await localCard.getByRole("button", { name: "转到后端" }).click();
await desktop.locator(".history-drawer").waitFor({ state: "detached", timeout: 60000 });
await desktop.locator(".workflow-panel").first().waitFor({ timeout: 30000 });
await desktop.getByRole("heading", { name: "推演结果" }).waitFor({ timeout: 30000 });
await desktop.locator(".fortune-banner").first().waitFor({ timeout: 30000 });
const migratedSessions = await desktop.evaluate(async () => {
  const clientId = localStorage.getItem("tianji_client_id_v1");
  const response = await fetch("/api/v1/sessions?limit=100", { headers: { "X-Client-Id": clientId } });
  const body = await response.json();
  return body?.data || [];
});
if (!migratedSessions.some((entry) => entry.question === "近期事项推演" && entry.status === "casted")) {
  throw new Error("本地存档重建后，后端没有对应的 casted 会话");
}
await desktop.screenshot({ path: shot("tianji-history-migrate.png"), fullPage: false });

// 移动端：顶栏「切换功能模块」下拉必须把用户带到对应模块页
const mobile = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
await mobile.goto(baseUrl, { waitUntil: "networkidle" });
await assertNoOverflow(mobile, "mobile home");
await mobile.getByLabel("切换功能模块").selectOption("/zhouyi");
await mobile.getByRole("heading", { name: "周易" }).waitFor();
await mobile.getByRole("button", { name: "开始起卦" }).click();
await mobile.getByRole("heading", { name: "周易本变卦象" }).waitFor({ timeout: 20000 });
await mobile.getByRole("tab", { name: "结论建议", exact: true }).click();
await mobile.getByRole("heading", { name: "综合研判与古籍引证" }).waitFor();
await assertNoOverflow(mobile, "mobile zhouyi result");
await mobile.screenshot({ path: shot("tianji-result-mobile.png"), fullPage: true });

await mobile.getByLabel("切换功能模块").selectOption("/bazi");
await mobile.getByRole("heading", { name: "八字命理" }).waitFor();
await mobile.getByLabel("公历出生日期时间").fill("1984-02-10T10:00");
await mobile.getByLabel("出生地时区").fill("Asia/Shanghai");
await mobile.getByRole("button", { name: "排本命盘" }).click();
await mobile.getByRole("heading", { name: "八字四柱与大运排盘" }).waitFor({ timeout: 20000 });
await assertNoOverflow(mobile, "mobile bazi");
await mobile.screenshot({ path: shot("tianji-bazi-mobile.png"), fullPage: true });

await mobile.getByLabel("切换功能模块").selectOption("/fengshui");
await mobile.getByRole("heading", { name: "阳宅风水" }).waitFor();
await mobile.getByLabel("向首方位角").fill("7.4");
await mobile.getByRole("button", { name: "生成阳宅坐向" }).click();
await mobile.getByRole("heading", { name: "阳宅真北坐向与二十四山" }).waitFor({ timeout: 20000 });
await mobile.getByRole("tab", { name: "八宅" }).click();
await mobile.getByRole("button", { name: "排八宅盘" }).click();
await mobile.getByRole("heading", { name: "八宅大游年盘" }).waitFor({ timeout: 20000 });
await assertNoOverflow(mobile, "mobile fengshui");
await mobile.screenshot({ path: shot("tianji-fengshui-mobile.png"), fullPage: true });

if (consoleErrors.length) {
  throw new Error(`browser console errors:\n${consoleErrors.join("\n")}`);
}

await browser.close();
console.log("browser smoke passed: zhouyi/liuyao/bazi/ziwei/spacetime standalone module pages, fengshui single/consensus/bazhai/xuankong/archive, classics search, desktop/mobile result, rules drawer, workflow 7-step result, history drawer ↔ backend sessions (both directions), mobile module navigation select");

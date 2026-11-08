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
await desktop.locator(".result-tabs").getByRole("button", { name: "阳宅风水", exact: true }).click();
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
await desktop.locator(".result-tabs").getByRole("button", { name: "阳宅风水", exact: true }).click();
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

// 审计 13 把 ResultWorkspace 拆成 result/ 下的独立视图文件后，构建通过仍不代表每个页签都能渲染
// （拆出来的组件少一个 import，只有真的点进去才会抛 ReferenceError）。这里逐个页签真实渲染一遍。
for (const [tab, heading] of [
  ["输入与历法", "历法基准与干支四柱"],
  ["奇门遁甲", "时家转盘奇门遁甲"],
  ["八字命理", "八字四柱与大运排盘"],
  ["紫微斗数", "紫微斗数全景天盘"],
  ["对照分析", "多模块推演对照分析"],
]) {
  await desktop.getByRole("button", { name: tab }).last().click();
  await desktop.getByRole("heading", { name: heading }).waitFor({ timeout: 15000 });
}
// 时间轴必须能在真实结果上生成：之前组件测试 mock 了 API，掩盖了
// solar_datetime 带 offset 时后端 422 的端到端缺陷。
await desktop.getByRole("button", { name: "八字命理" }).last().click();
await desktop.getByRole("button", { name: "生成时间轴" }).click();
await desktop.getByText(/月令提纲：/).waitFor({ timeout: 20000 });
await desktop.screenshot({ path: shot("tianji-tabs-desktop.png"), fullPage: true });


await desktop.getByTitle("规则目录").click();
const rulesDialog = desktop.getByRole("dialog", { name: "规则目录" });
await rulesDialog.waitFor();
await rulesDialog.getByText("CAL-NORMALIZE-001", { exact: true }).waitFor();
await rulesDialog.getByText("LR-TRANSMISSION-001", { exact: true }).waitFor();
await desktop.getByRole("button", { name: "关闭规则目录" }).click();

// 交互推演（7 步工作流）：这条路径此前既没有单测也没有烟测覆盖，
// 组件里被删掉的常量（SYSTEMS / localDateTimeValue 等）构建阶段查不出来，
// 只有真的点进来才会抛 ReferenceError。
await desktop.goto(baseUrl, { waitUntil: "networkidle" });
await desktop.getByRole("button", { name: "交互推演" }).click();
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
// 步骤1 是信息校验，步骤2 是完整排盘（含卦象与历法基线）
await desktop.getByText(/历法基线/).first().waitFor();
const calendarLine = await desktop.locator(".structured-friendly").nth(1).innerText();
if (calendarLine.includes("[object Object]")) {
  throw new Error(`历法基线把对象插值成了 [object Object]：${calendarLine.replace(/\n/g, " | ")}`);
}
if (!/年/.test(calendarLine)) {
  throw new Error(`历法基线缺少干支：${calendarLine.replace(/\n/g, " | ")}`);
}
// 卦象图必须拿到真实上下卦名，否则会静默画成坤（六条断线）
const hexagramText = calendarLine;
if (!/使用体系/.test(hexagramText)) {
  throw new Error(`步骤2 缺少「使用体系」：${hexagramText.replace(/\n/g, " | ")}`);
}
// ResultPhase 拆分后，交互深化页签也要真的走一遍：折叠面板、现实校验提交、交互记录计数
await desktop.getByRole("button", { name: "交互深化" }).click();
await desktop.getByRole("heading", { name: /交互深化（原始盘面不变/ }).waitFor();
// 折叠面板默认展开：点一下收起、再点一下展开（verify 折叠状态由 WorkflowPanel 的 collapsed 透传控制）
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

// 命运专项：四个页签都走真实后端。这里覆盖「拆出来的独立入口」整条链路：
// 共用出生信息 → 本命盘（/v1/calculations/evaluate）→ 紫微斗数 → 流年（/v1/bazi/liunian）→ 时间轴（/v1/bazi/lifeline）。
await desktop.goto(baseUrl, { waitUntil: "networkidle" });
await desktop.getByRole("button", { name: "命运专项" }).click();
await desktop.getByRole("heading", { name: "命运专项" }).waitFor();
await desktop.getByLabel("公历出生日期时间").fill("1984-02-10T10:00");
await desktop.getByLabel("出生地时区").fill("Asia/Shanghai");
await desktop.getByRole("button", { name: "排本命盘" }).click();
await desktop.getByRole("heading", { name: "八字四柱与大运排盘" }).waitFor({ timeout: 20000 });
await desktop.getByRole("tab", { name: /紫微斗数/ }).click();
await desktop.getByRole("button", { name: "排紫微盘" }).click();
await desktop.getByRole("heading", { name: "紫微斗数全景天盘" }).waitFor({ timeout: 20000 });
await desktop.getByRole("heading", { name: "大限区间" }).waitFor();
await desktop.screenshot({ path: shot("tianji-ziwei-desktop.png"), fullPage: true });
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
await assertNoOverflow(desktop, "desktop destiny");
await desktop.screenshot({ path: shot("tianji-destiny-desktop.png"), fullPage: true });

// 卜筮专项：周易与六爻页签各走一次真实后端，确认切换页签后提交的是当前体系。
await desktop.locator(".app-navigation").getByRole("button", { name: "卜筮专项", exact: true }).click();
await desktop.getByRole("heading", { name: "卜筮专项" }).waitFor();
await desktop.getByRole("tab", { name: /周易/ }).click();
await desktop.getByText("三数排盘").click();
await desktop.getByRole("button", { name: "开始起卦" }).click();
await desktop.getByRole("heading", { name: "周易本变卦象" }).waitFor({ timeout: 20000 });
await desktop.getByRole("tab", { name: "结论建议" }).click();
await desktop.getByRole("heading", { name: "综合推演研判与古籍引证" }).waitFor({ timeout: 20000 });
await desktop.getByRole("tab", { name: /六爻/ }).click();
await desktop.getByText("手工排盘").click();
await desktop.getByRole("button", { name: "开始起卦" }).click();
await desktop.getByRole("heading", { name: "六爻纳甲盘与伏神飞神" }).waitFor({ timeout: 20000 });
await desktop.getByText("铜钱排盘").click();
await desktop.getByRole("button", { name: "开始起卦" }).click();
await desktop.getByRole("heading", { name: "六爻纳甲盘与伏神飞神" }).waitFor({ timeout: 20000 });
await desktop.getByLabel(/用神焦点/).selectOption("求财买卖");
await desktop.getByRole("button", { name: "开始起卦" }).click();
await desktop.getByRole("heading", { name: /用神焦点 · 求财买卖/ }).waitFor({ timeout: 20000 });
await assertNoOverflow(desktop, "desktop divination workspace");
await desktop.screenshot({ path: shot("tianji-divination-workspace-desktop.png"), fullPage: true });

// 时空盘专项：奇门与大六壬各走一次真实后端。
await desktop.locator(".app-navigation").getByRole("button", { name: "时空盘专项", exact: true }).click();
await desktop.getByRole("heading", { name: "时空盘专项" }).waitFor();
await desktop.getByRole("button", { name: "开始排盘" }).click();
await desktop.getByRole("heading", { name: "时家转盘奇门遁甲" }).waitFor({ timeout: 20000 });
await desktop.getByRole("tab", { name: /大六壬/ }).click();
await desktop.getByRole("button", { name: "开始排盘" }).click();
await desktop.getByRole("heading", { name: "大六壬盘" }).waitFor({ timeout: 20000 });
await assertNoOverflow(desktop, "desktop spacetime workspace");
await desktop.screenshot({ path: shot("tianji-spacetime-workspace-desktop.png"), fullPage: true });

// 阳宅风水独立入口：单次坐向与多次共识都走真实后端，验证「拆出来的菜单」不是空壳。
await desktop.locator(".app-navigation").getByRole("button", { name: "阳宅风水", exact: true }).click();
await desktop.getByRole("heading", { name: "阳宅风水" }).waitFor();
await desktop.getByRole("button", { name: "生成阳宅坐向" }).click();
await desktop.getByRole("heading", { name: "阳宅真北坐向与二十四山" }).waitFor({ timeout: 20000 });
await desktop.getByRole("button", { name: "多次共识" }).click();
await desktop.getByRole("button", { name: "生成阳宅坐向" }).click();
await desktop.getByRole("heading", { name: "阳宅多次测量共识" }).waitFor({ timeout: 20000 });
await assertNoOverflow(desktop, "desktop fengshui workspace");
await desktop.screenshot({ path: shot("tianji-fengshui-workspace-desktop.png"), fullPage: true });

await desktop.getByRole("tab", { name: "八宅" }).click();
await desktop.getByRole("button", { name: "排八宅盘" }).click();
await desktop.getByRole("heading", { name: "八宅大游年盘" }).waitFor({ timeout: 20000 });
await assertNoOverflow(desktop, "desktop bazhai workspace");
await desktop.screenshot({ path: shot("tianji-fengshui-bazhai-desktop.png"), fullPage: true });

await desktop.getByRole("tab", { name: "玄空" }).click();
await desktop.getByRole("button", { name: "排玄空盘" }).click();
await desktop.getByRole("heading", { name: "玄空挨星盘" }).waitFor({ timeout: 20000 });
await desktop.getByLabel("附替卦起星盘").check();
await desktop.getByRole("button", { name: "排玄空盘" }).click();
await desktop.getByText("替卦起星盘（工程基线）").waitFor({ timeout: 20000 });
await assertNoOverflow(desktop, "desktop xuankong workspace");
await desktop.screenshot({ path: shot("tianji-fengshui-xuankong-desktop.png"), fullPage: true });

// 历史抽屉与后端会话（/v1/sessions）的联动：抽屉里必须能列出刚创建的会话，
// 点一下就能在交互推演里恢复结果。两套存档不通的问题是审计 14 的核心。
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

// 审计 14 的反向通道：本地存档 → 后端会话。上面的桌面推演已自动存了一条本地存档，
// 这里用抽屉里本地存档卡片的「转到后端」按存档事由与起盘时刻重建会话，并直接打开结果。
await desktop.getByRole("button", { name: "历史与案例" }).click();
const localHistoryList = desktop.locator(".history-list-wrap").nth(1);
const localCard = localHistoryList.locator(".history-item-card").filter({ hasText: "近期事项推演" }).first();
await localCard.waitFor({ timeout: 15000 });
await localCard.getByRole("button", { name: "转到后端" }).click();
// 抽屉关闭 = 重建成功（失败会留在抽屉里显示错误条）。旧的结果页仍在 DOM 里，
// 所以必须先等抽屉 detached，否则「推演结果」标题会被上一次的会话直接满足。
await desktop.locator(".history-drawer").waitFor({ state: "detached", timeout: 60000 });
await desktop.locator(".workflow-panel").first().waitFor({ timeout: 30000 });
await desktop.getByRole("heading", { name: "推演结果" }).waitFor({ timeout: 30000 });
await desktop.locator(".fortune-banner").first().waitFor({ timeout: 30000 });
// 光看结果页不够：旧会话也长一样。直接问后端有没有这张新会话，且状态已 casted。
// 会话接口要求 X-Client-Id（审计 22 的归属校验），所以这里取浏览器里那份 id 带上。
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

// 移动端导航栏是隐藏的，顶栏模式选择必须能把用户带到命运专项，否则新入口在手机上不可达。
await mobile.getByLabel("切换工作模式").selectOption("destiny");
await mobile.getByRole("heading", { name: "命运专项" }).waitFor();
await assertNoOverflow(mobile, "mobile destiny");
await mobile.screenshot({ path: shot("tianji-destiny-mobile.png"), fullPage: true });

await mobile.getByLabel("切换工作模式").selectOption("divination");
await mobile.getByRole("heading", { name: "卜筮专项" }).waitFor();
await mobile.getByRole("button", { name: "开始起卦" }).click();
await mobile.getByRole("heading", { name: "周易本变卦象" }).waitFor({ timeout: 20000 });
await assertNoOverflow(mobile, "mobile divination");
await mobile.screenshot({ path: shot("tianji-divination-mobile.png"), fullPage: true });

await mobile.getByLabel("切换工作模式").selectOption("spacetime");
await mobile.getByRole("heading", { name: "时空盘专项" }).waitFor();
await mobile.getByRole("button", { name: "开始排盘" }).click();
await mobile.getByRole("heading", { name: "时家转盘奇门遁甲" }).waitFor({ timeout: 20000 });
await assertNoOverflow(mobile, "mobile spacetime");
await mobile.screenshot({ path: shot("tianji-spacetime-mobile.png"), fullPage: true });

await mobile.getByLabel("切换工作模式").selectOption("fengshui");
await mobile.getByRole("heading", { name: "阳宅风水" }).waitFor();
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
console.log("browser smoke passed: fengshui single/consensus/bazhai/xuankong, desktop/mobile result, rules drawer, workflow 7-step result, history drawer ↔ backend sessions (both directions), mobile destiny entry, standalone fengshui workspace, and divination/spacetime workspaces (desktop/mobile, three-number + manual lines + coins + result tabs)");

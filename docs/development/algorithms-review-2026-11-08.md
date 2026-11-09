# 算法审查记录（2026-11-08）

审查对象：`backend/app` 下周易、梅花、六爻、大六壬、奇门、八字、紫微、阳宅风水各计算内核，以及历法、公共干支/卦象层。
审查方式：逐模块读源码 + 项目内 ADR/开发文档反查口径 + 外部典籍或标准案例核对；不做风格审查。
本轮已实际修改 5 个算法文件与 3 个测试文件；未改动前端。代码与本文已提交为 `5563858`。
2026-11-09 已按第三节处置口径问题：能确定的改代码，流派差异改为显式标注；见第三节。

## 一、结论速览

| 级别 | 问题 | 状态 |
| --- | --- | --- |
| P0 | 紫微天府落宫按「六冲对宫」计算，除寅申外 10/12 宫错位 | 已修 |
| P0 | 奇门拆补法按当日地支定三元，未按符头；乙卯日等大量日期局数错误 | 已修 |
| P1 | 奇门旬首寄中五时，值使门回落默认「休门」而非「死门」 | 已修 |
| P1 | 八字起运年只加整年，忽略起运月份跨年进位（1984-12 例差 1 年） | 已修 |
| P1 | 奇门天禽只在坤二写死，值符为天禽时落宫与九星语义断层 | 已修 |
| P2 | 六爻刑害「动爻N」用动爻序号而非真实爻位 | 已修 |
| P2 | 八字性别只认「男」，`M/male` 会按女性算顺逆与起运 | 已修 |
| P1/P2 | 奇门吉方数值评分与吉凶断语、工作流 `fortune_score` 与「不生成自动吉凶总分」边界冲突 | 已修：去评分/断语，删 `fortune_score` |
| P2 | 八字旺衰注释 1.5 与实现 1.6 不一致；阈值无出处；得地只看五行 | 已标注：注释对齐、`de_di_hits`、`analysis.method` |
| P2 | 八字阴刃、天乙/文昌日干年干并查属流派混用未标注 | 已修：分源标注、阴刃显式命名 |
| P2 | 紫微闰月 `abs` 不拆分、年界用立春而非春节；梅花年支同源问题 | 已标注：`calendar_policy` + 动态 warning |
| P2 | 大六壬涉害只走顺时针一条路径；手动占时的昼夜贵人仍用实际钟点 | 昼夜已修；涉害复核等价；变体覆盖不全 |
| P3 | `xun_info` 旬空两支顺序不统一（`亥戌`、`申酉`） | 勘误：实测顺序一致，无需改 |

## 二、已确认并修复的确定性错误

### 1. 紫微天府落宫（P0）

- 位置：`backend/app/ziwei/engine.py` 原第 206–214 行。
- 原实现：寅/申同宫，其余 `(ziwei + 6) % 12`（六冲对宫）。
- 正确口径：《紫微斗數全書·卷二·安天府图》「唯有寅申同一位，其余丑卯互安星」；以子=0 索引，`天府 = (4 - 紫微) % 12`。寅申同宫是公式自然结果，不是特例。
- 错误影响：紫微在子→天府应在辰，原实现给午；丑→卯原给未；卯→丑原给酉……除寅、申两宫外，10 个宫位全部错 2 宫。天府系八星随之整体错位。
- 修复：改为 `tianfu_branch_idx = (4 - ziwei_branch_idx) % 12`。
- 测试：`backend/tests/test_ziwei.py::test_ziwei_tianfu_formula` 改为断言 `(tf + zi) % 12 == 4`。原测试被并行提交锁成「非寅申一律六冲」，必须同步改，否则修复后测试反而失败。
- 文档：`docs/development/engine-algorithms-and-framework.md` 第 272 行原本已写 `(4 - Ziwei) mod 12`，与旧代码矛盾；本次以文档公式为准。

### 2. 奇门拆补法定元（P0）

- 位置：`backend/app/qimen/engine.py::_determine_yuan`。
- 原实现：只按当日地支——子午卯酉上元、寅申巳亥中元、辰戌丑未下元。
- 正确口径：拆补法先由日干支回退到符头（最近一个甲/己日），再按符头地支定元：甲子/甲午/己卯/己酉上元，甲寅/甲申/己巳/己亥中元，甲辰/甲戌/己丑/己未下元。
- 复现：`2001-08-20 16:00`，乙卯日甲申时，立秋。
  - 修复前：按日支卯判上元 → 阴遁2局、天英、景门、值符/值使落9宫。
  - 修复后：符头甲寅判中元 → 阴遁5局、天冲、伤门、值符/值使落3宫。与《开悟之门》标准例一致。
- 新增 `_fu_tou_pillar()`，输出 `facts.fu_tou` 便于回溯；`test_qimen_yuan_uses_fu_tou_not_day_branch` 锁定该例。
- 仍需决定：符头落在上一个节气、当前日已入下一节气时的「超神接气」处理。本修复仍以当前节气局数为准，未实现超神接气重排。

### 3. 奇门值使门中五寄宫（P1）

- 位置：`backend/app/qimen/rules.py::EIGHT_GATES_ORIGIN` 与 `engine.py` 第 118 行。
- 原实现：映射表没有 5 宫，`EIGHT_GATES_ORIGIN.get(5, "休门")` 直接回落「休门」。
- 正确口径：中五无门，旬首寄坤二，值使门按坤二死门起例。
- 修复：映射表补 `5: "死门"`；`test_qimen_zhi_shi_gate_for_center_xun_head` 用 `2026-01-01 12:00`（甲戌旬、值符天禽）锁定。

### 4. 奇门天禽寄宫（P1）

- 原实现：`tian_pan_stars[5] = "天禽"` 固定在中五；`is_tian_qin = (p_num == 2 and tian_pan_stars[2] == "天芮")` 只在坤二成立。
- 结果：值符为天禽时（如 2026-01-01 甲戌旬），输出「值符天禽落8宫」，但8宫九星写「天芮」，`is_tian_qin_present` 为 False，天禽仍挂在中五。
- 修复：转盘后按「天芮落宫」计算 `tian_qin_palace`，天禽与天芮同宫标记 `is_tian_qin_present=True`，并给出中五所携 `qin_stem`。
- 说明：九宫数据模型仍是一宫一主星，所以该宫 `nine_star` 保持「天芮」，另以 `is_tian_qin_present`/`qin_stem` 表达同宫；若要一宫双星展示，需要前端模型扩展。

### 5. 八字起运年月份进位（P1）

- 位置：`backend/app/bazi/engine.py` 第 422 行。
- 原实现：`start_actual_year = birth_year + start_year_offset`，忽略 `start_month_offset`。
- 复现：`1984-12-20 10:00` 男命，`getYun` 返回 5 岁 5 个月；按「出生后 5 年 5 个月」交运应在 1990-05，原实现记 1989，整条大运提前一年；`liunian`/`lifeline` 的大运区间也随错。
- 修复：把出生月与起运月相加，超过 12 个月进位到年；`luck_start_info` 增加 `start_actual_month`，`luck_pillars` 使用修正后的 `start_year`。
- 测试：`test_luck_start_year_carries_start_month` 断言 1990 / 1990-05 / 首运 1990–1999 / 次运 2000 起。

### 6. 八字性别别名（P2）

- 原实现：`is_forward` 用 `gender == "男"`，`getYun` 用 `1 if gender == "男" else 0`。接口允许任意字符串，传 `M`/`male` 时顺逆按女性、起运也按女性，两处同时错。
- 修复：入口统一归一化为「男/女」，与紫微已有的 `M/male` 兼容口径一致；`test_bazi_accepts_male_alias` 锁定。

### 7. 六爻刑害动爻标号（P2）

- 位置：`backend/app/liuyao/advanced.py::punishments_harms`。
- 原实现：`enumerate(动爻子集, 1)`，得到的是「第几个动爻」，不是真实爻位；例如初爻、四爻动，会写成「动爻1、动爻2」。
- 修复：遍历原爻表，用 `line["position"]` 生成「动爻N」，与 `assess_sanhe_conditions` 的来源字符串一致。

## 三、口径问题与处置（2026-11-09 更新）

原则：能从典籍或项目既有 ADR 确定的，直接改代码；确属流派差异的，保留一种口径并在响应里显式标注 `warnings` / `analysis`，不沉默混算。

1. **奇门吉方评分与断语 — 已修（去评分）**
   - `qimen/engine.py` 删除 `score`（原吉门80 + 三奇15 + 吉神10）与「吉神护佑，宜主动布局开拓」类断语。
   - `favorable_directions` 每项改为 `conditions`（三吉门 / 天盘三奇 / 吉神），`summary` 只陈述盘面结构，例如「东（震三宫），临【伤门】、【天冲】、【六合】；条件：三吉门、天盘三奇、吉神」。
   - 排序改为结构序：`gate_order(开0/休1/生2)` + 宫数，不再按分数排序。
   - `advisory` 改为「局象结构 / 候选方位 / 读盘说明」，并明确「只是盘面结构条件，未计算吉凶总分」。
   - 前端 `frontend/src/components/result/QimenView.jsx` 改为「三吉门落宫候选」「结构候选」；`Overview.jsx` 改「三吉门落宫：」；`lib/export.js` 去掉「吉方研判 / 八神护佑」。

2. **工作流 `fortune_score` 五档 — 已修（删数值）**
   - `workflow/steps.py` 两处删除 `fortune_score`，保留 `fortune_level` 与 `fortune_basis`；`basis` 改为逐条收集，等级依据仍可复核。
   - 对外只输出「大吉/小吉/平/小凶/大凶」规则等级，不再带任何数值总分。
   - `workflow/steps.py` 内部仍用 `TIYONG_SCORE` 做等级映射，该数值不进入响应。

3. **八字旺衰工程基线 — 已标注（不改公式）**
   - 注释与实现对齐为月令乘 `1.6` 倍。
   - `de_di` 改为逐条输出 `de_di_hits`，含 `pillar_index/branch/stem/type/weight/in_month_branch`，不再只返回布尔值。
   - `analysis.method` 显式记录 `branch_score_per_branch=12.0`、`month_branch_factor=1.6`、阈值 `0.65/0.52/0.45/0.30`，并注明「工程加权口径，不等同于任一传统旺衰流派；不区分本气/中气/余气权重」。
   - 若要改用《渊海子平》月令本气加权，属于新增流派口径，不在本次修复内。

4. **八字阴刃与天乙/文昌并查 — 已修（分源标注）**
   - 天乙、文昌按来源分别输出「天乙贵人（日干）/（年干）」「文昌贵人（日干）/（年干）」，不再合并成一个集合。
   - 阴干羊刃保留但显式标为「羊刃（阴刃）」，与阳干羊刃区分。

5. **紫微闰月与年界 — 已标注**
   - 保留「年柱按立春换年」的现状，新增 `calendar_policy`（`year_boundary="立春"`、`lunar_year_branch`、`leap_month_handling="按月序取数，不拆分前半月/后半月"`）。
   - 立春与春节之间年干支不一致、或生月为闰月时，动态写入 `calendar_warnings` 并提示「按当前口径出盘、不混算」。
   - 已删除未使用的 `_get_lunar_info` 死代码。
   - 是否改为「紫微以春节换年」需产品口径决定；当前不混算。

6. **梅花年支 — 已标注**
   - `time_cast` 保留年柱（立春换年）取数，新增年支口径 warning：当农历年对应年支编号与年柱年支不一致时，提示「梅花年支存在立春/春节两种口径，本盘按立春口径取数，未混算」。

7. **大六壬昼夜贵人 — 已修；涉害与「知一」边界说明**
   - `_cast` 在用户指定占时（`occupation_branch`，含报数起课）时，昼夜改按占时支判定（卯辰巳午未申为昼），不再按实际钟点；未指定占时仍按 `6<=hour<18`。
   - 涉害顺行单路径已用《六壬大全》原例复核（「午加庚」历酉辛为2、「戌加子」历癸为1），原疑点撤销。
   - 「知一」等三传变体仍未实现，属覆盖不全；当前按比用→涉害主路径，响应中不宣称支持全部变体。

8. **六爻月令旺衰 — 已标注（不改权重）**
   - 保留「月建地支本气单五行」判定旺相休囚死。
   - `facts.month_strength_policy` 与顶层 `warnings` 显式声明「未按月令藏干本气/中气/余气加权；藏干加权属另一流派口径，本盘不混算」。
   - `_line_strength_rank` 中囚/死同权仅用于候选排序，不据此推断吉凶。

9. **奇门九遁覆盖 — 已修（补六遁）**
   - `evaluate_qimen_patterns` 增加 `palace_number` 落宫条件，在三遁之外补齐：
     - 神遁：天盘丙 + 生门 + 九天；
     - 鬼遁：天盘丁 + 杜门 + 九地；
     - 风遁：天盘乙 + 开/休/生门 + 巽四宫；
     - 云遁：天盘乙 + 开/休/生门 + 地盘辛；
     - 龙遁：天盘乙 + 开/休/生门 + 坎一宫或地盘癸；
     - 虎遁：地盘辛 + 艮八宫，且（天盘乙+休门）或（天盘丙+生门）。
   - 条件按《奇门法窍》《奇门旨归》等通行本取交集写法；异文变体不混算，并在 `warnings` 说明。

10. **旬空展示顺序 — 勘误：原报告判断有误，代码本身一致**
    - 实测 `xun_info`：甲子 `['戌','亥']`、甲戌 `['申','酉']`、甲申 `['午','未']`、甲午 `['辰','巳']`、甲辰 `['寅','卯']`、甲寅 `['子','丑']`，顺序均为「先阳支后阴支」，无需改代码。
    - 原报告「甲子返回 `[亥, 戌]`」系误读，特此勘误。

## 四、已核对为正确的部分（避免重复推导）

- 卦象层：`KING_WEN_MATRIX` 8×8 全表、`TRIGRAM_CATALOG` 先天数与三爻自下而上 bit 序；`derive_hexagram_facts` 的互卦 (2,3,4)/(3,4,5)、错卦全反、综卦逆序。
- 八字：十神、十二长生、纳音60、藏干权重、天乙/文昌/禄/天德/月德/天医/驿马/桃花/华盖/将星/劫煞/灾煞/岁煞/亡神表值；大运阳男阴女顺、从月柱起顺逆推8步；`start_year_offset` 为0不被 `or` 兜底。
- 紫微：命宫/身宫、五虎遁、纳音定五行局、紫微定位 `_locate_ziwei_star`、大限起限与顺逆、左辅右弼/文昌文曲/魁钺/禄存/天马/擎羊陀罗/火铃/空劫/红鸾天喜/天刑天姚/咸池、天府系八星偏移。
- 六爻：纳甲八表、八宫世应、六神起例、六亲、旺相休囚死四关系、进神八组、伏神取本宫首卦同位、旬空「当日只可能冲空/旬空，填实须出旬值日」、`void_fill_prospects`。
- 梅花：时间起卦、两数/三数起卦、闰月绝对值与 warning；与 ADR-002/ADR-004 一致。
- 大六壬：月将按中气、天地盘「月将加时」、四课、贼克/比用/涉害/遥克/昴星/别责/八专/伏吟/返吟取传主路径；贵人顺逆与昼夜表。
- 奇门：`SOLAR_TERM_JU_TABLE` 24节气×三元局数、阴阳遁翻转；`SAN_QI_LIU_YI` 布阵；九星/八门本位、八神序、驿马表、空亡按宫辖支（中五不标空亡）。
- 风水：角度归一、磁北→真北、坐山=向首+180°、二十四山左闭右开、误差传播、圆周平均/最小覆盖弧/抵消判定；八宅大游年与命卦公式；玄空三元九运 2044 复归上元、`FLY_ORDER`、五入中不替、阴阳山顺逆、替卦表与 3.0° 起替。

## 五、回归与工作树

本轮涉及模块：

```text
backend/app/qimen/{engine,rules}.py
backend/app/bazi/engine.py
backend/app/daliuren/engine.py
backend/app/meihua/engine.py
backend/app/ziwei/engine.py
backend/app/liuyao/{engine,advanced}.py
backend/app/workflow/steps.py
backend/tests/{test_qimen,test_bazi,test_daliuren_domain,test_workflow_steps,test_ziwei,test_meihua,test_liuyao_policy}.py
frontend/src/components/result/{QimenView,Overview}.jsx
frontend/src/lib/export.js
data/rules/mvp-engineering-baseline.json
```

定向测试：`152 passed / 33 subtests passed`（奇门、八字、大六壬、工作流）。
口径标注新增测试：`12 passed`（紫微、梅花、六爻月令）。
后端全量：

```text
2 failed, 890 passed, 10 skipped, 70 subtests passed
```

两个失败仍为 `tests/test_iching.py` 的卦序断言（屯应为3、解为40）。失败来源是工作树里**并行会话的未提交改动** `backend/app/common/hexagrams.py`（同批还有 `backend/tests/test_liuyao.py`、`?? backend/tests/test_hexagrams.py`、`?? backend/verify_liuyao.py`），不是本轮算法文件。这些并行文件不在本提交内，提交前必须核对归属。

静态检查：`ruff check app tests` 通过。
前端：`test:unit` 15 文件 / 97 用例通过；`test:node` 47 用例通过；`npm run build` 通过；`test:browser` 端到端烟测通过（桌面/移动端、工作流、奇门/六壬、风水、典籍检索）。

## 六、覆盖边界

- 完整阅读并核对：`common` 干支/卦象、`calendar` 历法与节气、`bazi`（含 `liunian`/`lifeline`）、`ziwei`、`liuyao`（含 `advanced`）、`meihua`、`daliuren`、`qimen`、`fengshui` 四模块。
- 口径抽查、未逐行做算法结论：`workflow/steps.py`（吉凶汇总与步骤编排）、`core/explanation.py`、`core/advisory.py`、`core/interpretation.py`、`core/targeted_deduction.py`、`zhouyi/*`、`calendar/timezone.py`。这些层主要做解释、编排与展示，不改变排盘数值；其中与「自动吉凶」边界相关的问题已在第三节列出。
- 未审前端计算/展示逻辑；本轮前端只同步奇门文案（「三吉门落宫候选」「结构候选」）；`ZiweiView.jsx` 用浏览器当前时间算年龄等展示近似问题不在本次算法结论内。


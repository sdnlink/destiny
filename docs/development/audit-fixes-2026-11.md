# 2026-11 审计问题修复记录

本文记录上一轮 28 条审计问题的落地情况，供复核与后续排期使用。
验收标准：后端回归全绿（依赖数据库的用例在无库环境下条件跳过并打印原因）、前端构建通过。

## 验证方式与结果

| 验证项 | 命令 | 结果 |
| --- | --- | --- |
| 后端全量回归 | `cd backend && python -m pytest tests -q` | 391 passed / 10 skipped / 24 subtests passed |
| 后端静态检查 | `cd backend && python -m ruff check app tests` | 0 error（规则集 `E4,E7,E9,F`） |
| 前端构建 | `cd frontend && npm run build` | 通过，产出按需分包（首包 60.44KB JS + 182.10KB react 分片） |
| 前端单测 | `cd frontend && npm run test:unit` | 15 passed |

说明：10 个 skip 全部是 `tests/test_calendar_corpus_db.py` 里依赖 ClickHouse 的集成用例，
无库时由 `HAS_CLICKHOUSE` 判定后 skip，不再伪装成「通过」，也不再因为没有数据库而报红。

## 逐条状态

| # | 问题 | 状态 | 落地位置 |
| --- | --- | --- | --- |
| 4 | 事项分类键名三处漂移 | 已修 | `backend/app/common/categories.py`；`core/interpretation.py`、`core/advisory.py`、`core/literature.py`、`workflow/steps.py` 全部改为引用；前端 `src/lib/labels.js` 与后端逐项比对（`tests/test_frontend_labels.py`） |
| 1 | 冻结快照丢真实起盘参数 | 已修 | `workflow/casting.py` handler 内部 `dict(payload)`，不再 pop 入参 |
| 2 | 冻结快照缺卦名/动爻，交互层读不到 | 已修 | 新增 `workflow/plate_facts.py`（`build_plate_facts` / `build_plate_view`），`raw_plate` 增加 `plate_facts` |
| 3 | 交互层字段名 `auxiliary_yongshen` 读错 | 已修 | `interaction/deep_question.py` 改为 `secondary_yongshen` |
| 5 | 用神五行写死固定对照表 | 已修 | `workflow/steps.py` 改为 `_resolve_yongshen_element`，按纳甲/世应/体用推导并输出 `element_source` |
| 7 | 体用关系只有两类 | 已修 | 五类齐全，判定统一走 `common/five_elements.element_relation` |
| 9 | 地支/五行常量各写一份 | 已修 | `common/ganzhi.py`、`common/five_elements.py` 收为唯一真源，`meihua/engine.py`、`bazi/rules.py` 改为转出 |
| 6 | 吉凶与应期不可追溯 | 已修 | 登记 `WF-YONGSHEN-001`/`WF-WANGSHUAI-001`/`WF-FORTUNE-001`/`WF-TIMING-001`，step4/step6 输出 `rule_ids`、`fortune_score`；口径见 ADR-015 |
| 8 | 四套 module/method 分发 | 大部分已修 | 新增 `common/calculation_dispatch.py`（27 组）；`core/validation.py`、`workflow/casting.py` 已切；`main.py` 的 if 链改为 `CALCULATION_ENTRIES` 表 |
| 23 | `requirements-dev` 缺 httpx | 已修 | `requirements-dev.txt` 改为 `-r requirements.txt` + `pytest` + `httpx<0.28`，并加 `tests/test_dependency_contract.py` |
| 26 | 无 CI/无 lint 配置 | 已修 | `.github/workflows/ci.yml`（lint + pytest + 前端构建与单测）、`pyproject.toml` 增加 `[tool.ruff]` |
| 27 | 三平台脚本缺口 | 已修 | 新增 `scripts/start_dev.sh`、`scripts/deploy.ps1`、`scripts/deploy.bat` |
| 28 | 死代码 | 已修 | 清 `steps.py` 局部常量与空分支、`inquiry_parser` 9 个 `has_*`、`session/models.py` 未实现交互类型、`bazi/engine.py` 半成品神煞变量（改为真正计算天德/月德）、`advisory` 单字母变量；`core/db.py get_branch_imagery` 经核实有调用者，非死代码 |
| 16 | 数据库异常被吞、来源标注撒谎 | 已修 | `core/db.py` 分类记录日志；`main.py` 新增 `constant_payload`，数据库不可达时返回 `source: unavailable` 而不是 `clickhouse_database` |
| 17 | 常量端点每次探测 + 空缓存永久化 | 已修 | `is_available` 加 30 秒缓存；`hexagram_service` 缓存加 TTL 且空结果不缓存 |
| 18 | 线程池用于纯 CPU 计算 | 已修 | `workflow/casting.py` 与 `main.py comparison_envelope` 均改顺序执行 |
| 19 | 会话写入非原子、ID 可穿越 | 已修 | `session/store.py` 原子写（临时文件 + `os.replace`）、会话 ID 严格校验、损坏文件记录日志 |
| 20 | 会话 JSON 体积放大 | 部分修 | 去掉 `indent=2` 改紧凑序列化；「同一结果存三遍」（快照 `module_results`、`raw_plate`、`workflow_result.step2`）需与前端读取契约同步改，留待单独一轮 |
| 21 | localStorage 超配额静默失败 | 已修 | `src/lib/storage.js` 改为字节预算 + 超限降级 + 失败返回 false，App 提示用户 |
| 22 | 口令双写、鉴权空转、异常外泄 | 部分修 | 代码侧口令只从环境读取（`requirements`/`.env.example` 说明）；500 响应不再回 `str(exc)`，改记日志；`APP_API_TOKEN` 未设时启动打印警告。会话归属校验需要身份体系，未见实现 |
| 24 | pydantic v1→v2 破坏性迁移 | 已界定 | `requirements.txt` 锁 `pydantic>=1.10.26,<2`，迁移步骤写入 ADR-016，并由测试锁定主版本 |
| 25 | README 数字过期 | 已修 | 14 条规则/7 个案例 → 73/31，并补工作流规则与吉凶边界说明 |
| 10 | 转发壳模块 | 保留 | `core/{casting,liuyao,meihua,liuren}.py` 是带 `__all__` 的兼容转出层，非重复实现；删除会破坏既有导入路径 |
| 11 | 三份 HTTP 客户端与三份 canonical_hash | 部分修 | 摘要统一到 `common/hashing.py`；ClickHouse 客户端仍只有 `core/db.py` 一处，语料检索客户端未合并（依赖不同服务） |
| 12 | 前端与后端双份体系映射 | 部分修 | 前端抽到 `src/lib/calculationPlan.js` 并单测（8 例）；与后端 `workflow/scheduler.py` 的跨栈单源需要新增计划接口，留待单独一轮 |
| 13 | 超大组件与 `!important` | 未修 | `ResultWorkspace.jsx`(101KB)、`WorkflowPanel.jsx`、`styles.css`(134KB/27 处 `!important`) 拆分属视觉回归风险高的重构，需视觉基线后再做 |
| 14 | 两套持久化不通、两个入口同抽屉 | 部分修 | 去掉重复的「历史任务」入口，合并为「历史与案例」；localStorage 与后端会话存储的打通属功能设计，未做 |
| 15 | 前端测试自证、Chrome 路径写死 | 已修 | 测试改为直接 import 生产模块；`smoke.mjs` 不再硬编码 `/usr/bin/google-chrome`，截图落系统临时目录 |

## 行为变化（可能影响既有调用方）

1. `/v1/constants/*` 在数据库不可达时返回 `source: "unavailable"`，不再谎报 `clickhouse_database`；`data` 为空数组并带 `warning`。
2. 非法 `session_id`（不符合 `sess_[A-Za-z0-9_-]{1,64}`）一律按查无此会话处理，返回 404。
3. 会话 JSON 改为紧凑序列化，已有文件仍可读取（格式兼容）。
4. 交互异常返回统一文案「交互处理失败，请查看服务端日志」，不再透出内部异常。
5. 前端首屏只加载外壳 + 输入面板，结果区与工作流面板改为按需分包。
6. 动爻爻题改为传统写法（`九三`、`初九`、`上六`），原输出「三九」是极性/位次颠倒；
   `bian_yao` 改为变爻描述「第3爻由阳变阴」，此前错填变卦名（变卦名仍在 `bian_gua`）。
   两者由 `backend/tests/test_plate_facts.py` 钉住，避免再次静默退化。
7. 八字神煞补齐天德/月德：此前只算了月令对应的天德/月德值却从未参与判定，
   现在逐柱比对天干与地支（天德可能是天干或地支，月德固定为天干）。

## 仍待决策

1. 审计第 13 条的大文件拆分与 `!important` 清理，需要先有视觉回归基线。
2. 第 20 条「同一结果存三遍」的字段裁剪会改前端读取契约，建议与第 14 条持久化打通一起排期。
3. 第 24 条 pydantic v2 迁移按 ADR-016 的清单单独执行。

## 第二轮修复（2026-11-04）

本轮目标是补齐上一轮遗留的测试缺口，并修复补测过程中暴露的真实缺陷。

### 验证结果

| 验证项 | 命令 | 结果 |
| --- | --- | --- |
| 后端全量回归 | `python -m pytest backend/tests -q` | 620 passed / 10 skipped（ClickHouse）/ 0 failed |
| 新增工作流单测 | `backend/tests/test_workflow_steps.py` | 105 用例 |
| 新增交互模块单测 | `backend/tests/test_interaction_modules.py` | 102 用例 |
| 新增鉴权边界单测 | `backend/tests/test_token_middleware.py` | 5 用例 |
| 前端渲染级测试 | `npm --prefix frontend run test:unit`（vitest + jsdom） | 7 文件 / 45 用例通过 |
| 前端既有纯 JS 单测 | `npm --prefix frontend run test:node` | 26 用例通过（命令原样保留） |
| 前端生产构建 | `npm --prefix frontend run build` | 通过，分块与首包体积不变 |

### 修复项

| 问题 | 状态 | 落地位置 |
| --- | --- | --- |
| 健康检查模块清单漏 ziwei/bazi/qimen | 已修 | `backend/app/main.py` `/health`，由 `test_token_middleware.py` 钉住 |
| `APP_API_TOKEN` 与 `SERVE_WEB=1` 冲突（整站 401） | 已修 | `backend/app/main.py` 中间件只保护 `/v1/*`、`/docs`、`/openapi.json`、`/redoc`；静态资源与 `/health` 公开 |
| 规则数量文档口径漂移（14/63/73） | 已修 | `docs/readme.md`、`docs/refactoring-plan.md`、`docs/development/calculation-service.md` 统一为 73 条规则、31 个案例、16 条 ADR |
| 旺衰休/囚/死三档判反 | 已修 | `backend/app/workflow/steps.py` 按 ADR-015 / WF-WANGSHUAI-001 口径：用神生月令→休、月令克用→囚、用神克月令→死 |
| 现实校验把「不太符合」判成「符合」 | 已修 | `backend/app/interaction/reality_check.py`：长关键词优先 + 关键词前缀否定判断 |
| 复盘把「未通过」判成偏有利 | 已修 | `backend/app/interaction/review.py` `_classify_outcome` 先判不利关键词 |
| 复盘有利/阻碍因素归因分支不可达 | 已修 | `backend/app/interaction/review.py` 新增 `_matches_any` 双向包含并忽略空串 |
| 空角度命中第一个预设 | 已修 | `backend/app/interaction/angle_shift.py` `_match_preset` 对空白输入短路 |
| 「其他」被误判为「对方」 | 已修 | `backend/app/interaction/multi_party.py` 匹配前剔除「其他/其它」 |
| 非法月支输出空括号「（）」 | 已修 | `backend/app/workflow/steps.py` 无节气时只输出 `月令「X」` |
| 历史抽屉使用未导入的 `FileClock` 图标（打开即白屏） | 已修 | `frontend/src/App.jsx` 补 lucide 导入；`frontend/tests/components/App.test.jsx` 新增抽屉渲染用例钉住 |
| React 组件零渲染测试 | 已修 | 新增 `frontend/tests/components/` 7 个测试文件（HexagramView/InteractionResultDisplay/StructuredDisplay/InputPanel/WorkflowPanel/ResultWorkspace/App），均真实挂载，无 snapshot |
| 测试把会话 JSON 写进仓库 `data/sessions/` | 已修 | 新增 `backend/tests/conftest.py` 将 `SESSION_STORAGE_DIR` 指向临时目录并退出时清理；`test_session_isolation.py` 钉住；已清理本轮测试产生的 20 个残留文件（保留 8 月的 2 个原有记录） |

### 行为变化（可能影响既有调用方）

1. 旺衰判定按规范口径校正后，step6 吉凶分档随之变化：休（泄气）由 -2 改记 0、囚（受克）由 0 改记 -2；`_calculate_trend`、obstacles、应期远近的「休 vs 囚死」分支同步回到正确档位。
2. `reality_check` 的模糊匹配语义收紧：`不太符合/并不完全符合/没有符合` 归一为「不符合」；`部分符合吧` 仍为「部分符合」；`未来符合预期` 不再被误判为否定；`不知道` 仍返回 `unknown/retry`。
3. `review` 的「未通过」类否定结果归为偏阻滞，与 step6 凶判一致；有利/阻碍因素现在能按双向包含命中。
4. `detect_parties("其他事情怎么办")` 返回 `['求测人']`，真代词（他/她/他们）仍能识别出「对方」。
5. `_match_preset("")` 与 `_match_preset("   ")` 返回 `None`，不再谎称命中「对方立场」。

### 仍待决策（本轮新增）

1. 六爻伏神飞神、大六壬遥克多候选已改为确定性推导（见第三轮补强），剩余断语仍需规则签署。
2. 风水 FS-001/FS-004~008、房屋档案 PostgreSQL 持久化属架构投入，本轮未动。

## 第三轮补强（2026-11-04）：补齐可确定性计算的结论

原则：只实现"输入已完备、结果唯一、可复算"的推导，不引入断语取舍；涉及流派分歧的仍留待签署。

| 结论 | 输入 | 推导口径 | 落地位置 |
| --- | --- | --- | --- |
| 六爻伏神/飞神 | 本卦、八宫归属、纳甲 | 本宫首卦（八纯卦）同位爻补缺；飞神取本卦同位爻；飞伏按五行生克 | `liuyao/engine.py` `_hidden_flying_spirits`，规则 `LY-HIDDEN-FLYING-001` |
| 六爻月令旺衰、月破 | 月建、爻支 | 同气旺、月生相、爻生月休、月克囚、爻克月死；月建冲爻为月破 | `liuyao/engine.py` `_month_strength`、`_decorate` |
| 六爻日辰关系、日破、暗动 | 日辰、爻支、动静、月令旺衰 | 临/冲/合/受生/泄气/受克；静爻受日冲，旺相为暗动、休囚为日破 | 同上，规则 `LY-DAYMONTH-001` |
| 六爻旬空状态 | 旬空支、日辰 | 空亡逢日辰同支填实，逢日冲冲空 | `liuyao/engine.py` `_void_state` |
| 六爻变卦纳甲、进退神 | 变卦上下卦、动爻 | 变卦按各自上下卦装纳甲；亥→子等八组为进神，反向为退神 | `liuyao/engine.py` `_decorate_changed`、`_advance_retreat` |
| 大六壬遥克多候选 | 四课、日干阴阳 | 比用后仍不定则转涉害取深，结果标注 `remote_control` | `daliuren/engine.py` `_remote_transmissions` |
| 奇门时旬空落宫 | 时柱旬空、九宫地支 | 宫辖地支命中空亡即标空；中五宫不标 | `qimen/engine.py`、`qimen/rules.py` `PALACE_BRANCHES` |
| 奇门驿马落宫 | 时支三合 | 申子辰马在寅、寅午戌马在申、巳酉丑马在亥、亥卯未马在巳 | `qimen/rules.py` `HORSE_STAR` |
| 紫微三方四正 | 宫位地支序 | 本宫 + 三合两宫（+4/+8）+ 对宫（+6） | `ziwei/engine.py` |
| 八字财星喜忌 | 日主五行、喜忌五行 | 财为日主所克，按喜用/忌神/不显三态出结论 | `bazi/engine.py` `_generate_bazi_advisory` |
| 六爻三合局/六合 | 动爻、月建、日辰爻支池 | 三合局三支齐备、六合成对，来源逐支标注 | `liuyao/engine.py` `_branch_structures`，规则 `LY-BRANCHSTRUCT-001` |
| 紫微杂曜五颗 | 生年支、生月 | 红鸾卯起子年逆数、天喜对宫、天刑酉起正月顺数、天姚丑起正月顺数、咸池按三合局 | `ziwei/engine.py`，规则 `ZW-MINOR-001` |
| 伏神展示取值修复 | 后端伏神结果 | 前端伏神卡片变量缺失会导致运行时崩溃（`palaceName`/`missingRelatives`），已补回并改为后端驱动 | `ResultWorkspace.jsx` `LiuyaoView` |

前端同步：六爻表显示月破/日破/暗动/旬空/进退神，世应徽章改为兼容后端 `roles: ["世"]/["应"]`（原先只认"世爻/应爻"，徽章永远不显示）；伏神优先取后端结果，旧会话回退本地计算。

验证：后端 **631 passed / 10 skipped / 0 failed**；前端 **45 passed**；`npm run build` 通过。

本轮明确不做（不可仅靠计算解决）：六爻用神旺衰断语、伏神空破、三合局与刑害合成、紫微四化飞星、八宅与玄空飞星（流派口径未签）、风水房屋档案（需持久化与合规设计）。

## 第四轮补强（2026-11-04）：多底本计算 + 典籍依据 + 风水档案

针对"不同流派取法全部计算、以历史典籍为依据、缺典籍从公开渠道补"的要求：

| 结论 | 多底本/依据 | 落地位置 | 规则 |
| --- | --- | --- | --- |
| 本地典籍库 | 多来源存档 91 部（维基文库 53 + 殆知阁 34 + 公开古籍网站 4：增删卜易、卜筮正宗、黄金策、宅经、地理辨正、沈氏玄空学、紫微斗数全书、三命通会、滴天髓阐微等）；引擎 evidence 字段按关键词检索原文段落（classic_id/摘录/来源链接/许可）；检索支持简繁双向变体（zhconv，查询词自动展开繁/简两种形式，摘录仍显示语料原文可回溯） | `app/common/classics.py`，端点 `/v1/classics/search`、`/v1/classics/status` | CLS-CORPUS-001 |
| 六爻用神候选与元忌仇 | 用神定义引《增删卜易·用神元神忌神仇神章》原文；候选（本卦/伏神/变爻）按动>静、旺>衰、不空破>空破排序，不断吉凶 | `app/liuyao/advanced.py`，请求参数 `focus` | LY-YONGSHEN-001 |
| 六爻伏神空破出伏 | 伏神空、破、受日月克伤不得出；冲空、暗动、填实反主引出（增删卜易·伏神章口径） | 同上，hidden_spirits 增加 emerge_blockers/can_emerge | 并入 LY-HIDDEN-FLYING-001 输出 |
| 六爻三合成局条件 | 全动成局、待补凑（虚待用）、空破待填、入墓待冲开（增删卜易·三合局章原文在库） | `app/liuyao/advanced.py` | LY-SANHE-COND-001 |
| 六爻刑害 | 三刑/自刑/六害通行地支表，动爻与日月齐备组合 | 同上 | LY-XINGHAI-001 |
| 紫微四化多底本 | 庚壬两干化科分歧：全书通行本 vs 通行别本（化科天府），两套变体同时输出并标注 | `app/ziwei/rules.py` SIHUA_VARIANTS | ZW-SIHUA-002 |
| 八宅大游年 | 大游年歌通行传本（各派一致），命卦通行公式，宅命东西四配法；理论依据引语料《宅经》 | `app/fengshui/bazhai.py`，端点 `/v1/fengshui/bazhai` | FS-BAZHAI-001 |
| 玄空飞星 | 三元九运 + 二十四山下卦挨星（蒋氏《地理辨正》传承，语料在库）；旺山旺向/上山下水/双星条件判定；替卦区间按实测角度判定但替卦盘未提供 | `app/fengshui/xuankong.py`，端点 `/v1/fengshui/xuankong` | FS-XUANKONG-001 |
| 风水房屋档案 | 文件后端（默认，租户子目录隔离）+ PostgreSQL 后端（FENGSHUI_STORAGE=postgres，DDL 见 scripts/sql/fengshui_building_profiles.sql）；owner_consent 强制、不含身份信息 | `app/fengshui/storage.py`，端点 `/v1/fengshui/buildings` | 并入 FS-BAZHAI-001 存档 |

### 典籍来源与待补清单

## 第五轮（2026-11-04）：全网公开渠道补齐缺失典籍

维基文库对内容批量接口持续限流（HTTP 429），改为多来源补齐，语料从 53 部扩至 **91 部 / 4777 段 / 约 586 万字符**：

| 来源 | 覆盖 | 数量 | 许可记录 |
| --- | --- | --- | --- |
| 维基文库（`cache/wikisource`） | 增删卜易、地理辨正、宅经、古今图书集成艺术典等 | 53 部 | CC BY-SA / 公有领域，逐书来源链接 |
| 殆知阁古代文献 GitHub 存档（`cache/open-sources`） | 卜筮正宗、黄金策、易隐、易冒、易林补遗、断易天机、火珠林、六壬大全、六壬指南、壬归、六壬粹言、御定六壬直指、奇门遁甲统宗、奇门法窍、遁甲演义、御定奇门宝鉴、渊海子平、子平真诠评注、穷通宝鉴、神峰通考、李虚中命书、梅花易数、阳宅指南、宅法举隅、灵城精义、入地眼全书、天玉经、天元五歌、地理古镜歌、青囊奥语、青囊序、撼龙经、潜虚 | 34 部 / 232 万字 | 公有领域（古籍原文），逐书记 GitHub blob 链接 |
| 公开古籍网站原文转录（`cache/web-classics`） | 八宅明鏡（诗词汇）、陽宅十書（王元吉易学网）、沈氏玄空學（中华典藏）、紫微斗數全書（中华典藏，序文+卷一至卷三） | 4 部 / 43 万字 | 公有领域（古籍原文网页转录），逐页来源链接 |

- 新增脚本：`scripts/cache_open_sources.py`（GitHub raw 下载）、`scripts/cache_web_classics.py`
  （网页正文提取，剔除导航噪音）、`scripts/build_classics_corpus.py`（多来源合并构建，
  schema 与旧构建器完全兼容）、`scripts/fix_cache_line_endings.py`（Windows 换行修复）；
- 抓取清单：`data/sources/open-source-books.json`、`data/sources/web-classics-books.json`；
- 诚实边界：《紫微斗數全書》卷四为图说（站方仅提供 PDF 扫描）未入库；网站转录版含少量
  站点导航噪音，已在提取器中尽量剔除；5000yan 等站为现代白话改写版（有现代编译版权），
  明确排除不用；
- 待补清单清账：`SOURCING_BACKLOG` 全部条目已逐项核对——八宅明鏡/陽宅十書/沈氏玄空學/
  紫微斗數全書/卜筮正宗均由上述来源补齐入库；《太極圖說》经逐句核对正文完整
  （原文仅约 250 字），此前"不完整"为 <2000 字符启发式误报；
- `scripts/cache_wikisource_texts.py` 新增 `--only` 单书参数（catalog 自动合并历史结果），
  限流恢复后可按书增量重抓；
- 维基文库限流期间不再重试其内容接口，`manifest_not_stored` 字段继续如实展示维基文库侧缺口。

### 早期来源记录（第四轮）

- 已入库（公开许可）：`data/generated/wikisource-corpus/`；
- 所有引用均带来源链接与许可信息，便于逐条校对。

### 诚实边界（仍然不做）

1. 六爻吉凶断语仍不生成——用神候选给出的是"候选+排序+典籍原文"，最终判断留给人；
2. 玄空替卦盘未提供——《沈氏玄空學》原文已由第五轮补入，但起星表工程化与替卦盘实现仍待专家口径签署，宁可标注缺失不杜撰；
3. 四化别本仅收录可查证的庚壬化科分歧，其余诸干诸本一致，不虚构更多"派别"。

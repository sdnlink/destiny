# 2026-11 审计问题修复记录

本文记录上一轮 28 条审计问题的落地情况，供复核与后续排期使用。
验收标准：后端回归全绿（依赖数据库的用例在无库环境下条件跳过并打印原因）、前端构建通过。

> 注：本文件为历史修复记录，表中规则/案例数字按当时口径保留；当前规则注册表已增至 84 条规则（工程回归案例 31 个）。

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
| 8 | 四套 module/method 分发 | 已修（第九轮） | 唯一分发表 `common/calculation_dispatch.py`（28 组）；`workflow/scheduler.py` 改 `REQUEST_BUILDERS` 查表；`main.py` 只留 `CALCULATION_MODELS`（27 条入参模型）、27 个计算端点统一走 `execute_calculation`；`test_scheduler_dispatch.py` / `test_main_dispatch.py` 钉住三张表键集一致 |
| 23 | `requirements-dev` 缺 httpx | 已修 | `requirements-dev.txt` 改为 `-r requirements.txt` + `pytest` + `httpx<0.28`，并加 `tests/test_dependency_contract.py` |
| 26 | 无 CI/无 lint 配置 | 已修（第九轮补钩子） | `.github/workflows/ci.yml`（lint + pytest + 前端构建与单测）、`pyproject.toml` 增加 `[tool.ruff]`、`.pre-commit-config.yaml`（ruff-pre-commit v0.17.3，已 install 并实跑 Passed） |
| 27 | 三平台脚本缺口 | 已修 | 新增 `scripts/start_dev.sh`、`scripts/deploy.ps1`、`scripts/deploy.bat` |
| 28 | 死代码 | 已修 | 清 `steps.py` 局部常量与空分支、`inquiry_parser` 9 个 `has_*`、`session/models.py` 未实现交互类型、`bazi/engine.py` 半成品神煞变量（改为真正计算天德/月德）、`advisory` 单字母变量；`core/db.py get_branch_imagery` 经核实有调用者，非死代码 |
| 16 | 数据库异常被吞、来源标注撒谎 | 已修 | `core/db.py` 分类记录日志；`main.py` 新增 `constant_payload`，数据库不可达时返回 `source: unavailable` 而不是 `clickhouse_database` |
| 17 | 常量端点每次探测 + 空缓存永久化 | 已修 | `is_available` 加 30 秒缓存；`hexagram_service` 缓存加 TTL 且空结果不缓存 |
| 18 | 线程池用于纯 CPU 计算 | 已修 | `workflow/casting.py` 与 `main.py comparison_envelope` 均改顺序执行 |
| 19 | 会话写入非原子、ID 可穿越 | 已修 | `session/store.py` 原子写（临时文件 + `os.replace`）、会话 ID 严格校验、损坏文件记录日志 |
| 20 | 会话 JSON 体积放大 | 已修（第八轮） | 去掉 `indent=2`；新增 `compact_plate_output`（每盘只留展示所需 facts），实测单会话 274457 → 89629 bytes、step2 36627 → 2519 bytes |
| 21 | localStorage 超配额静默失败 | 已修 | `src/lib/storage.js` 改为字节预算 + 超限降级 + 失败返回 false，App 提示用户 |
| 22 | 口令双写、鉴权空转、异常外泄 | 已修（第十四轮补归属校验） | 代码侧口令只从环境读取（`requirements`/`.env.example` 说明）；500 响应不再回 `str(exc)`，改记日志；`APP_API_TOKEN` 未设时启动打印警告。归属校验：会话接口强制 `X-Client-Id`，服务端只存其 sha256 作 `owner_hash`，列表按归属过滤，跨归属读写 403；迁移前的老会话由首个访问者认领（详见第十四轮小节） |
| 24 | pydantic v1→v2 破坏性迁移 | 已修（第十二轮） | 4 类 v1 写法共 46 处全部改写（`pattern=`/`min_length=`/`@field_validator`/`.model_dump()`，另 19 处 `example=` 改显式 `json_schema_extra`），依赖升到 `pydantic>=2.9,<3`；迁移前采契约基线逐项比对，14 个 422 用例的 `loc` 与状态码、3 个成功响应、55 条路由、31 个 schema 全部不变，只有错误文案与 OpenAPI 的 `Optional` 表达按 v2 换了写法（详见 ADR-016「迁移结果」） |
| 25 | README 数字过期 | 已修（历史时点） | 当时 14 条规则/7 个案例 → 73/31；现为 84 条规则/31 个案例 |
| 10 | 转发壳模块 | 保留 | `core/{casting,liuyao,meihua,liuren}.py` 是带 `__all__` 的兼容转出层，非重复实现；删除会破坏既有导入路径 |
| 11 | 三份 HTTP 客户端与三份 canonical_hash | 部分修 | 摘要统一到 `common/hashing.py`；ClickHouse 客户端仍只有 `core/db.py` 一处，语料检索客户端未合并（依赖不同服务） |
| 12 | 前端与后端双份体系映射 | 部分修 | 前端抽到 `src/lib/calculationPlan.js` 并单测（8 例）；与后端 `workflow/scheduler.py` 的跨栈单源需要新增计划接口，留待单独一轮 |
| 13 | 超大组件与 `!important` | 已修（第十、十一轮） | `ResultWorkspace.jsx` 2332 行 → 151 行，视图拆到 `components/result/` 13 个文件（最大 376 行）；`styles.css` 7416 行 → 7 个文件；`WorkflowPanel.jsx` 1114 → 628 行，三阶段 JSX 拆到 `components/workflow/`（最大 303 行）。`!important` 27 → 3（只剩无障碍 reduced-motion 三条，已备注理由），24 条逐条用运行时计算样式验证视觉等价 |
| 14 | 两套持久化不通、两个入口同抽屉 | 已修（第九轮正向 + 第十三轮反向） | 入口已合并为「历史与案例」；抽屉内「后端推演会话」栏点选即恢复；反向新增「转到后端」：用存档里的求测事由与起盘时刻（`local_datetime`/`timezone`）调 `POST /v1/sessions` + `/cast` 重建会话并直接打开结果，`cast_nonce` 重新生成、盘面可能与存档不同（抽屉提示与代码注释均已写明），存档原件保留 |
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
8. 会话接口（`/v1/sessions*`）强制要求 `X-Client-Id` 头：缺失或非法一律 400
   `CLIENT_ID_REQUIRED`；跨客户端访问返回 403 `SESSION_FORBIDDEN`；列表只回本客户端的会话
   （迁移前无归属的老会话仍可见，由首个访问者认领）。直接 `curl` 调试会话接口需自行带上该头。

## 仍待决策

1. 审计第 13 条已拆掉三个大文件（`ResultWorkspace` / `WorkflowPanel` / `styles.css`），`!important`
   27 → 3；剩下 3 条是无障碍 `prefers-reduced-motion` 降级，属于 `!important` 的正当用法，已就地注明理由。
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
| 规则数量文档口径漂移（14/63/73） | 已修（历史时点） | 当时统一为 73 条规则/31 个案例/16 条 ADR；现为 84 条规则（全部纳入 `rule_sets`）/31 个案例 |
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

本轮明确不做（当时口径，历史时点记录）：六爻用神旺衰断语、伏神空破、三合局与刑害合成、紫微四化飞星、八宅与玄空飞星（流派口径未签）、风水房屋档案（需持久化与合规设计）。其中八宅、玄空下卦挨星、房屋档案及六爻组合事实已在第四轮按"只列事实、不生成吉凶断语"落地；替卦盘仍待专家口径。

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
- 简繁双向检索：`app/common/classics.py` 与 ClickHouse 版语料服务 `app/corpus_api.py`
  均将查询词/标题过滤展开为原样+繁体+简体变体（后者在 SQL 中以参数化 OR 条件匹配），
  摘录一律保持语料原文；`zhconv==1.4.3` 已加入 `backend/requirements.txt`，缺库自动降级；
- 维基文库限流期间不再重试其内容接口，`manifest_not_stored` 字段继续如实展示维基文库侧缺口。

### 典籍来源与补齐记录（早期，第四轮）

- 已入库（公开许可）：`data/generated/wikisource-corpus/`；
- 所有引用均带来源链接与许可信息，便于逐条校对。

## 第六轮（2026-11-04）：八字流年岁运事实序列

| 结论 | 落地位置 | 规则 |
| --- | --- | --- |
| 逐年干支（4年甲子锚的60甲子循环）、流年十神/纳音/五行、周岁与虚岁并列、太岁与岁破地支 | `app/bazi/liunian.py`，端点 `/v1/bazi/liunian` | BZ-LIUNIAN-001 |
| 流年所属大运区间（起运前/八步之后为 null）、流年与四柱的六冲/六合/六害/三刑/自刑/三合局半合/天干五合组合事实 | 同上 | 并入 BZ-LIUNIAN-001 |
| 典籍依据：检索「流年/太歲/大運/行運」挂《三命通會》《神峰通考》《滴天髓闡微》等原文段落 | `app.common.classics`（简繁变体检索） | CLS-CORPUS-001 |

- 地支刑害/自刑与天干五合表统一收敛到 `app/common/ganzhi.py`，六爻 `app/liuyao/advanced.py` 改为引用同一张表，避免跨模块重复维护；
- 诚实边界：只列可查证的组合事实，不生成吉凶断语；干支按公历年通行纪年，立春交节精确边界需结合 calendar 模块；三合只列两支半合，不推断成局；
- 规则注册表同步更新 `CLS-CORPUS-001` 的多来源/简繁检索口径（84 条规则无重复）。

## 第七轮（2026-11-04）：全项目循环审查与加固

两路只读审查（文档口径一致性 / 代码质量与安全）逐项核实后，按"发现问题即修、每轮复验"处理：

**正确性**

- `app/main.py` 补导入 `HTTPException`：此前 4 个房屋档案端点的 422/404/503 分支会抛 `NameError` 变成 500；新增端点层测试覆盖这些分支；
- `CALCULATION_ENTRIES` 注册 `("bazi","liunian")`，统一计算入口与独立端点一致；
- `build_classics_corpus.py` 的 `attribution_url` 按 `source_id` 分支，非 MediaWiki 来源不再错误追加 `?action=history`；重建语料验证 38 处链接修正；
- 构建脚本输出默认改为相对仓库根（此前从 `scripts/` 调用会把语料误写入 `scripts/data/`，已清理副本）；
- 典籍库 `status()` 比对三个来源清单、`search()` 增加查询长度/limit 边界、损坏 jsonl 时显式降级；流年补齐 `start_year+count` 组合越界与出生年解析失败的显式报错。

**一致性与契约**

- 房屋档案双后端统一 `make_record` DTO、`PostgresBackend` 用 `closing` 关闭连接、文件后端 `mkstemp + os.replace` 原子写并加锁；删除与 SQL 文件重复的 DDL 常量；
- 兑现合规声明：`source`（测量方式）必填、`owner_consent` 必须布尔真、`facing_degree` 范围校验、payload 64KB 上限；
- 规则注册补齐 7 条紫微规则的 `rule_sets` 引用，`test_rule_registry.py` 增加双向一致性断言（84 条定义 ↔ 84 条引用）；
- 玄空/八宅模块及规则表的"原典未入语料/见待补清单"文案全部改为真实边界（替卦盘待专家口径、《阳宅三要》与卷四图说暂缺）；README、计算服务、前端、语料服务、设计文档与 ADR 的历史数字（73/7/17 部）与过时"未实现"条目统一或加历史时点注记。

**安全与健壮性**

- 两处 Bearer 令牌比较改为 `hmac.compare_digest`；`/v1/sessions` 的 `limit` 约束为 1–200；`/v1/classics/search` 的 `q/category/title/limit` 全部加上边界；
- 房屋档案新增可选 `FENGSHUI_TENANT_ID` 服务端绑定，多租户部署时忽略客户端声明；会话模块无归属字段、仅限单租户本地环境的边界已写入文档；
- ClickHouse 口令移除全部默认值（应用、`load_*.sh`、`verify_*.py` 等），校验脚本补 10 秒网络超时；`corpus_api.py` 500 分支记录堆栈；
- 抓取脚本加 URL 白名单（拒绝 `file://`/内网）、下载字节上限、仓库路径穿越防护与 `zhconv` 缺库告警；`app/core/imagery.py` 静默降级改为 debug/警告留痕；`requirements*.txt` 补齐 `starlette`、`psycopg2-binary`、`numpy` 声明。

**可复现性**（干净 clone）

- `cache/` 与 `data/generated/` 均不入库；此前多个测试硬依赖 91 部语料，全新环境会直接失败。现在 `build_all.sh` 在三个缓存 catalog 齐全时离线重建语料，无缓存时明确提示；
- 依赖真实语料的断言改为"缺失则 skip"，新增合成 jsonl 用例覆盖加载/检索/简繁变体与降级路径；模拟空语料目录验证 **44 passed / 7 skipped / 0 failed**，有语料环境 **51 passed / 0 failed**。

**验证**：后端全量回归、前端 45 项单测 + node 测试 + `npm run build`、新增 `test_review_hardening.py` 端点/边界/脚本契约用例全部通过。

### 诚实边界（仍然不做）

1. 六爻吉凶断语仍不生成——用神候选给出的是"候选+排序+典籍原文"，最终判断留给人；
2. 玄空替卦盘未提供——《沈氏玄空學》原文已由第五轮补入，但起星表工程化与替卦盘实现仍待专家口径签署，宁可标注缺失不杜撰；
3. 四化别本仅收录可查证的庚壬化科分歧，其余诸干诸本一致，不虚构更多"派别"。

## 第八轮（2026-11-05）：运行时验证 —— 构建通过不等于界面不炸

前几轮的验收一直是 `npm run build` + 单测 + 后端 pytest。本轮真的把浏览器拉起来点了一遍，
立刻抓到三个"构建阶段完全无法发现"的缺陷，也顺带定位了"经典推演偶发 15 秒超时"的真实原因。

### 运行时暴露的真缺陷

| 缺陷 | 现象 | 根因 | 落地位置 |
| --- | --- | --- | --- |
| 交互推演一打开就白屏 | `pageerror: SYSTEMS is not defined` | 早前把 `WorkflowPanel.jsx` 的本地 2025 字符实现删掉改 import 时，连带删掉了 `SYSTEMS` / `CASTING_METHODS` / `localDateTimeValue` / `newCastNonce` 四个标识符，只补了 `labels` 的 import。JS 未定义变量是运行期错误，构建期查不出来 | `frontend/src/lib/labels.js` 新增 `SYSTEMS`(7) / `CASTING_METHODS`(4)；新建 `frontend/src/lib/castingInput.js` 承载 `localDateTimeValue` / `newCastNonce`（App.jsx 改为引用同一实现）；`labels-contract.test.mjs` 钉住取值域与后端一致 |
| 历法行显示 `[object Object]` | 步骤2 渲染成「丙午年 戊戌月 壬午日 丁未时 · [object Object]」 | 后端 `solar_term` 是 `{previous,current,next,...}` 结构，前端直接插值对象 | 后端 `plate_facts._solar_term_display` 归约为 `{name, note}`；前端 `workflowDisplay.solarTermLabel` 兼容压缩前后两种来源 |
| 卦象图永远画成坤（六条断线） | 上下卦名查不到，`TRIGRAMS[upperTrigram]` 为 undefined | 引擎把上下卦存成 `upper_trigram`/`lower_trigram` **字典**，`_hexagram_brief` 只认字符串键 | `plate_facts._hexagram_brief` 同时读 `.name`；`test_plate_facts.py::test_trigram_dict_names_are_flattened_for_frontend` 钉住 |
| 烟测断言与真实界面脱节 | 6 处标题/文案断言早就改过名，`盘面事实` 少了冒号 | 断言写死历史文案，界面改名后没人同步 | `frontend/tests/smoke.mjs` 全部按真实界面改名，文献断言改为只校验 `.literature-status`（不把环境开关固化成断言） |

### 「经典推演 15 秒超时」的根因（不是网络抖动）

ClickHouse 不可达时，**一次失败建连在本机实测要 2–4 秒**（探活与查询各自超时，`localhost` 还要先试 IPv6 再试 IPv4）；
而一个 `/v1/calculations/compare` 会连打三条常量查询，于是单个请求空耗 **12.2 秒**，正好撞上前端 15 秒超时。
`is_available()` 的 30 秒缓存只挡住了探活，没挡住查询本身。

- 修复：`core/db.py` 增加 `QUERY_FAILURE_COOLDOWN_SECONDS = 20`，查询失败/探活失败后进入冷却，
  冷却期内 `query()` 直接返回 `None` 走降级路径；探活成功即解除冷却，数据库恢复后下一个请求就回到真实数据。
  这保留了"失败结果不进缓存"的原意（不把一次故障锁死），只是不再为同一次故障重复付超时代价。
- 实测：同一请求 8091 **12.2 s → 67 ms**（连测两次均稳定）。
- 探活超时 1.5s → 1.0s（localhost 双栈下实测 1.0s 约耗 2s）。
- `tests/test_db_cache.py` 增加 4 条：冷却内不重复建连、失败不写结果缓存且恢复后能取到真实行、探活成功清冷却、探活失败进冷却。

### 新增/更新的测试

| 文件 | 内容 |
| --- | --- |
| `backend/tests/test_plate_facts.py` | 16 例：展示层键归一、动爻爻题、变爻描述、节气归约（当天 / 非当天退回下一节气）、上下卦字典名扁平化、step2 瘦身 |
| `backend/tests/test_db_cache.py` | 9 例：查询缓存、空结果不缓存、失败冷却与恢复 |
| `frontend/tests/labels-contract.test.mjs` | 5 例：`SYSTEMS`/`CASTING_METHODS` 与后端取值域逐项相等、分类 11 项 id 唯一、`localDateTimeValue` 格式、`newCastNonce` 正则 |
| `frontend/tests/workflow-display.test.mjs` | 6 例：干支对象/pillars 优先/缺失兜底/节气 current/节气退 next/`solarTermLabel` 标注 |
| `frontend/tests/smoke.mjs` | 新增"交互推演 7 步工作流"整段：创建会话 → 起盘 → 等结果 → 结构化数据 → 断言历法行不含 `[object Object]` 且含干支与"使用体系" → 溢出检查 + 截图 |

### 验证结果（本轮）

| 验证项 | 命令 | 结果 |
| --- | --- | --- |
| 后端全量回归 | `python -m pytest backend/tests -q` | **698 passed / 10 skipped / 0 failed**（skip 全是 ClickHouse 不可达；隔离 venv 补装 `zhconv==1.4.3` 后 6 个简繁检索用例恢复通过） |
| 后端静态检查 | `python -m ruff check app tests` | All checks passed |
| 前端构建 | `npm run build` | 通过：`WorkflowPanel 41.58KB` / `ResultWorkspace 91.44KB` / `react 182.10KB` / `index 60.87KB`（均已分包） |
| 前端单测 | `npm run test:unit` | 7 文件 / **45 用例**通过 |
| 浏览器烟测 | `npm run test:browser` | **passed**：风水单盘/合参、桌面结果、规则抽屉、**交互推演 7 步结果**、移动端结果；`ERRORS: []` |

### 本轮实测到的真实渲染（可作为回归基线）

- 吉凶卡：`大吉 | 用神相（月令生用），力量充足；用生体，外部条件滋养自身`
- 步骤2：`使用体系：meihua、liuyao | 萃 | ☱兑 上 | ☷坤 下 | … 动爻：二爻 | 历法基线：丙午年 戊戌月 癸未日 丁巳时 · 立冬（下一节气）`
- 步骤4：`用神定位：用神官鬼取第5爻（官鬼，静爻），纳甲地支申属金` / `用神旺衰：相（月令生用）` / `体用关系：用生体`

### 环境说明（不写死端口）

- 本机 8090 曾被一个查不到实体的僵尸监听占住（`taskkill`/`Stop-Process`/`Get-CimInstance` 全部失败，`/health` 仍返回 200 但跑的是旧代码）。
  本轮改用 8091，并把 `vite.config.js` 的 `proxy.target` 改为 `process.env.VITE_PROXY_TARGET || "http://127.0.0.1:8090"`，
  用环境变量切换后端，不必让每个开发者维护自己的配置副本。
- 后端进程用前台常驻方式（`python -m uvicorn app.main:app --port 8091`）而不是 `Start-Process`：后者起的子进程会随父 shell 结束一起消失。

### 仍然不做（诚实边界）

1. 审计 13 的大文件拆分（`ResultWorkspace.jsx` 2244 行、`WorkflowPanel.jsx` 1114 行、`styles.css` 7416 行 / 27 处 `!important`）仍未做，需要视觉回归基线；
2. 审计 14 的 localStorage↔后端会话双向打通已于第九轮（正向）与第十三轮（反向）落地；审计 22 的会话归属校验仍未做（需身份体系）；
3. （已完成）审计 24 的 pydantic v2 迁移已于第十二轮落地，见 ADR-016「迁移结果」。

## 第九轮（2026-11-05）：分发收敛（审计 8）+ pre-commit（审计 26）

第八轮之后剩下的两条工程项都指向同一件事：**同一份"哪个方法调哪个引擎"的知识被写在多处，
改一处忘一处**。本轮把它收敛成一张表，并把提交前检查真正跑起来。

### 审计 8：一条调用链，一张表

| 层 | 收敛前 | 收敛后 |
| --- | --- | --- |
| 工作流选体系 → 排请求 | `workflow/scheduler.py` 里 if/elif 长链，按体系 × 起盘方式分支 | `REQUEST_BUILDERS` 表（体系 → {方法 → 构造器}）+ `DEFAULT_METHOD` 兜底；新增体系只加一条 |
| HTTP 端点 → 引擎 | 27 个独立端点各自 `return {"data": xxx_cast(**request.dict())}`，`/v1/calculations` 又是另一套 `CALCULATION_ENTRIES`（模型 + lambda 调用） | 端点统一 `execute_calculation(module, method, payload)`；`main.py` 只保留 `CALCULATION_MODELS`（27 条，只管"用什么模型校验"），调用全部委托 `common/calculation_dispatch.CALCULATION_HANDLERS` |
| `main.py` 的引擎导入 | 26 个 `xxx_cast` 导入，端点直调 | 全部删除（端点已不再直接持有引擎） |

收敛过程中发现一处真实漂移：`main.py` 的 `CALCULATION_ENTRIES` 注册了 `("bazi","liunian")`，
而统一分发表没有——独立端点能算、`/v1/calculations/evaluate` 报 `unsupported calculation`。
现已补进 `CALCULATION_HANDLERS`（28 条），并由测试钉住两侧键集相等。

新增守卫：

| 文件 | 内容 |
| --- | --- |
| `backend/tests/test_scheduler_dispatch.py` | 5 例：调度表排出的每个 (module, method) 都已在分发表注册；可调度体系的方法全部可达；默认体系排出 `calendar → meihua → liuyao`（按序）；未知体系只排历法不排空盘；**排出的每个请求真能执行并返回盘面 dict** |
| `backend/tests/test_main_dispatch.py` | 4 例：`CALCULATION_MODELS` 键集 == `CALCULATION_HANDLERS` 键集；27 个组合都真有 HTTP 路由；路径映射表与模型表键集相等；未知组合抛 `ValueError` |
| `backend/tests/test_constant_sources.py` | 2 例：16 个常量端点都必须声明 `source` 且取值合法；声明 `unavailable` 时 `data` 必须为空且带 `warning` |

`test_constant_sources.py` 顺带查出了第四个合法来源：`/v1/constants/hexagram-explanations`
是「数据库 → 本地 rule 文件缓存」两级回退，其 `source: file_cache` 与 `in_memory_fallback` 不同义，
测试按真实取值域列举，没有为了断言好写而抹掉这个差异。

### 审计 26：pre-commit 真的装了、也真的跑了

- `.pre-commit-config.yaml`：`astral-sh/ruff-pre-commit` `rev: v0.17.3`（与本地验证用的 ruff 版本对齐），
  `files: ^backend/`，规则集不重复写——统一走 `backend/pyproject.toml` 的 `[tool.ruff]`；
- 实跑 `pre-commit run --all-files`：`ruff (legacy alias) … Passed`；
- 已执行 `pre-commit install`，钩子落到 `.git/hooks/pre-commit`；
- **纠正一条此前的误判**：`E:\code\destiny` 是 git 仓库（`.git` 存在，HEAD `babb96e` / 695 passed），
  之前判定"不是 git 仓库"是因为本机 `git` 不在 `PATH` 上（实际在 `C:\Program Files\Git\cmd\git.exe`），
  `git rev-parse` 报的是命令不存在而不是仓库不存在。

### 一次自造事故与恢复（记录过程，不是辩解）

批量改写 27 个端点用的脚本按 `@app.post("...")` 切块、只替换函数体；
但"下一个 `@app.post` 之前的一切"都被当成函数体尾部一并替换掉了，于是：

- 三个请求模型 `BazhaiRequest` / `XuankongRequest` / `FengshuiProfileRequest` 被删；
- `GET /v1/fengshui/bazhai` 端点被删。

恢复依据不是记忆，而是**当时仍在运行的旧实例**：它的 `/openapi.json` 里保留了这三个模型与
该端点的原始 schema（字段、默认值、`ge/le` 边界），按原值还原；再用路由差集脚本
（旧 openapi 的全部 (path, method) vs 当前 `main.py` 的装饰器）核到
**MISSING = 空、EXTRA = 空**，并 `git diff` 逐块确认改动只落在预期位置。
教训：对多端点文件做正则替换，边界必须钉在"函数体结束"而不是"下一个装饰器"。

### 审计 14 的一半：历史抽屉直连后端会话

此前「历史与案例」抽屉只读 localStorage 的经典推演存档，后端 `/v1/sessions` 的推演会话
只能进「交互推演」后手动填会话 ID 才看得到——同一件事有两套入口。

本轮把抽屉做成两栏：

| 区域 | 数据源 | 动作 |
| --- | --- | --- |
| 本地推演存档（原有） | `localStorage`（`lib/storage.js`） | 复盘载入 / 导出 Markdown / 删除 / 备份导出与导入 |
| 后端推演会话（新增） | `GET /v1/sessions?limit=50` | 「在交互推演中打开」→ 切视图并把 `session_id` 传给 `WorkflowPanel`，复用已有的 `getSession` 恢复路径 |

- 后端不可达时只在抽屉内提示「后端会话不可达」，本地存档照旧可用（不把两套存储绑成一起坏）；
- `WorkflowPanel` 新增可选 props `recoverSessionId` / `onRecovered`，外壳传入 id 后直接恢复并回调清空，避免重复触发；
- 烟测新增真实点击：`历史与案例` → 断言 `region[aria-label=后端推演会话]` 里有卡片 →
  点刚创建的那条 → 等到「推演结果」与 `.fortune-banner` → 断言抽屉已关闭；
- 运行时实测：抽屉列出 9 个后端会话，点开恢复出 `吉凶定性 平 …`，`PAGEERRORS: []`。

**仍未打通的反向路径**：本地存档是 `module_results` 结构，后端会话是七步 `workflow_result`，
把本地存档"写回后端"等于重新起盘而不是搬运结果，本轮不做；会话归属校验（审计 22）仍缺身份体系。

### 验证结果（本轮，第九轮）

| 验证项 | 命令 | 结果 |
| --- | --- | --- |
| 后端全量回归 | `pytest backend/tests -q` | **709 passed / 10 skipped / 0 failed**（698 → 709：新增 11 例守卫） |
| 后端静态检查 | `ruff check app tests` | All checks passed |
| 提交前钩子 | `pre-commit run --all-files` | `ruff … Passed`（已 `pre-commit install`） |
| 前端构建 | `npm run build` | 通过：`index 63.97kB / icons 19.73kB / WorkflowPanel 40.61kB / ResultWorkspace 91.44kB / react 182.10kB` |
| 前端单测 | `npm run test:unit` | 7 文件 / 45 用例通过 |
| 浏览器烟测 | `npm run test:browser` | **passed**：风水单盘/合参、桌面结果、规则抽屉、交互推演 7 步、**历史抽屉 ↔ 后端会话**、移动端结果 |
| 路由零漂移 | 旧 openapi vs 当前装饰器 | MISSING / EXTRA 均为空 |

### 仍然不做（诚实边界，更新后）

1. 审计 13 还剩两块：`WorkflowPanel.jsx` 1114 行（有 20 多个 `useState`，抽视图需要连着状态一起设计）与 `styles.css` 里 27 处 `!important`（每条都要先定位它在压谁，靠视觉回归验证）；
2. （已完成）审计 14 反向打通（本地存档 → 后端会话）已于第十三轮落地：按期用存档事由与起盘时刻重建，随机种子重生成并在界面标注；审计 22 的会话归属校验仍需身份体系；
3. （已完成）审计 24 的 pydantic v2 迁移已于第十二轮落地，见 ADR-016「迁移结果」。

## 第十轮（2026-11-05）：超大文件拆分（审计 13）

审计 13 的原始描述是「`ResultWorkspace.jsx` 101KB / `WorkflowPanel.jsx` / `styles.css` 134KB 且含 27 处
`!important`」。本轮拆掉其中两处，都是**纯搬家**：不改 props、不改渲染逻辑、不改样式值。

### `ResultWorkspace.jsx`：2332 行 → 151 行

按原有顶层 `function` / `const` 边界机械切分，每个体系的视图独立成文件：

| 文件 | 行数 | 内容 |
| --- | --- | --- |
| `components/result/shared.jsx` | 235 | `findModule`、`DataState`、`CastingIdentity`、`HexagramLines/Tile`、`Pillars`、`Notice`、`Steps`、`Evidence`、`TargetedFindings`、`MissingModule` |
| `components/result/labels.js` | 66 | 8 组展示映射常量（柱标签、分类、场景、类象、起盘方式、类象角色、五行配色） |
| `components/result/Overview.jsx` | 182 | 总览 |
| `components/result/CalendarView.jsx` | 196 | 历法基准与干支四柱 |
| `components/result/ZhouyiView.jsx` | 71 | 周易本变卦象 |
| `components/result/MeihuaView.jsx` | 78 | 梅花易数 |
| `components/result/LiuyaoView.jsx` | 305 | 六爻纳甲盘（含纳甲表、六亲推导、伏神飞神） |
| `components/result/LiurenView.jsx` | 156 | 大六壬盘 |
| `components/result/QimenView.jsx` | 179 | 奇门九宫（含宫格卡片） |
| `components/result/BaziView.jsx` | 249 | 八字四柱与大运 |
| `components/result/ZiweiView.jsx` | 173 | 紫微十二宫（含宫位卡与三方四正高亮） |
| `components/result/FengshuiView.jsx` | 174 | 阳宅风水（含罗盘拨盘与多次测量共识） |
| `components/result/ComparisonView.jsx` | 162 | 多模块对照 |
| `components/result/ExplanationView.jsx` | 376 | 结论建议与古籍引证 |

**保真校验**：拆分脚本先把原文件按顶层 chunk 打散，再按名字归组；校验脚本对 47 个 chunk
逐段做**原文包含**比对，结果 `chunks kept: 47 of 47, missing: []`——没有一行代码在搬运中丢失。

### `styles.css`：7416 行 → 7 个文件

第一版按文件里的 `/* ===` 分节注释切，结果发现早期分节注释风格不统一，前 3400 行全被当成"没有分节的
前言"，切得很偏，已作废重来。

第二版按**规则边界**（括号回到顶层且已攒够 1200 行）机械均分，主文件只剩 `@import`：

| 文件 | 行数 |
| --- | --- |
| `styles/01-base-and-input.css` | 1207 |
| `styles/02-result-shell-and-calendar.css` | 1205 |
| `styles/03-liuyao-liuren.css` | 1202 |
| `styles/04-qimen-bazi-ziwei.css` | 1202 |
| `styles/05-fengshui-and-comparison.css` | 1200 |
| `styles/06-explanation.css` | 1204 |
| `styles/07-workflow-and-overlays.css` | 196 |

7 个文件行数相加 = **7416**，与原文件行数完全相同；每个文件内部括号配平（脚本强制校验，不平衡就中止）。

**关键验证方式**：CSS 拆分的正确性判据不是"看起来一样"，而是**产物逐字节一致**——
拆分前后 `npm run build` 输出的都是 `dist/assets/index-Dmmh7YvJ.css`，98.96 kB / gzip 17.82 kB。
哈希相同说明级联顺序没变，视觉不可能改变。

### 验证结果（第十轮）

| 验证项 | 命令 | 结果 |
| --- | --- | --- |
| 前端构建 | `npm run build` | 通过；CSS 产物哈希与拆分前**完全相同**（`index-Dmmh7YvJ.css` 98.96 kB） |
| 前端单测 | `npm run test:unit` | 7 文件 / 45 用例通过 |
| 全部 12 个页签 | `npm run test:browser` 新增逐页签渲染段 | 通过：历法、周易、梅花、六爻、大六壬、奇门、八字、紫微、风水、对照、结论、总览 |
| 交互推演与抽屉 | 同上 | 7 步结果与「历史抽屉 ↔ 后端会话」两段仍通过 |

**烟测为什么加逐页签那一段**：拆分后每个视图都是独立模块，少一个 import 时 `npm run build` 依然
通过（打包器不校验标识符是否存在），只有真正点到那个页签才会 `ReferenceError`。原来烟测只覆盖了
历法外的 6 个页签，奇门/八字/紫微/对照四个页签从没在浏览器里跑过——这正是审计第 27 条（`SYSTEMS is not defined`）
暴露过的同一类问题，所以这次把 12 个页签全钉进烟测。

## 第十一轮（2026-11-05）：`WorkflowPanel` 拆分与 `!important` 第一批（审计 13）

### `WorkflowPanel.jsx`：1114 行 → 628 行

三个阶段（创建 / 信息补全 / 结果交互）的 JSX 原来埋在同一个带 20 多个 `useState` 的大函数里，
所以这一轮只做「提 JSX、不提 state」：视图组件不持有任何状态，所有 `useState`、请求函数、
`isLoading(key)` 仍留在 `WorkflowPanel`，由父组件显式透传。

| 文件 | 行数 | 内容 | props |
| --- | --- | --- | --- |
| `components/workflow/CreatePhase.jsx` | 303 | 求测表单、报数/手工起卦输入、历史会话面板、恢复面板 | 24 |
| `components/workflow/CompletionPhase.jsx` | 82 | 起盘前信息补全问答 | 9 |
| `components/workflow/ResultPhase.jsx` | 285 | 吉凶卡、四个页签、交互深化四个折叠面板 | 36 |
| `components/workflow/CollapsibleSection.jsx` | 15 | 折叠面板 | 4 |
| `components/WorkflowPanel.jsx`（主文件） | 628 | state、请求函数、`casting` 过渡态、阶段分发 | — |

**做法与两个坑**：

1. 用括号配对从原文件取三个 `if (phase === …) { return (…) }` 的整块 JSX 与末尾 `CollapsibleSection`，
   再按标识符白名单正则统计每块引用了哪些父作用域名字（`create` 引 28 个、`completion` 引 9 个、
   `result` 引 36 个），据此生成显式 props。
2. **坑一**：`if (phase === "create") {` 在文件里出现两次——草稿自动保存的 `useEffect` 里也有一处，
   首次 `str.index` 取到的是 7 行的错误块，改用 `rindex` 才拿到正确的 252 行块。
3. **坑二**：新文件在 `components/workflow/` 子目录下，脚本沿用了原文件的 `from "../lib/labels"`，
   少一层目录；rolldown 报 `UNRESOLVED_IMPORT`，改成 `"../../lib/labels"`（3 个文件）后通过。注意
   `../StructuredDisplay` 这类同级组件路径是对的，不能一起改。

**保真校验**：对原文件重新计算四块原文，逐段做包含比对——`create: preserved (251 lines)` /
`completion: preserved (45 lines)` / `result: preserved (219 lines)` / `collapsible: preserved`，
`missing: []`。

### `!important`：27 处 → 20 处（第一批 7 条）

这 27 处不能凭"删了就没事"处理：每一条都在压某个更具体的选择器，删掉就是视觉回退。本轮改成
**用更高特异性替代 `!important`**，并且用运行时计算样式做判据——改前改后各跑一遍同一套 Playwright
探针，逐项比对 `getComputedStyle`，全部相同才算通过。

| 位置 | 原写法 | 原来在压谁 | 改法 |
| --- | --- | --- | --- |
| `04` `.branch-active` ×2 | `background/color … !important` | `.liuren-plate-row > strong`（0,1,1）、`.liuren-plate-row.generals span`（0,2,1） | 拆成 `.liuren-plate-row > .branch-active`（0,2,0）与 `.liuren-plate-row.generals .branch-active`（0,3,0） |
| `04` `.selected-line` | `background … !important` | 无同属性竞争者（`tr.moving-line td` 在 `td` 上，不争 `tr` 的背景） | 直接去掉 `!important` |
| `07` `.form-row` | `grid-template-columns: 1fr !important` | `06` 的 `@media (max-width:760px)` 同名规则（同特异性，靠顺序） | 去掉 `!important`（本文件最后加载，顺序已足够） |
| `07` `.numbers-row` | `repeat(3, 1fr) !important` | 同上 | 去掉 `!important` |
| `07` `.manual-row` | `grid-template-columns: 1fr !important` | **`.manual-input .manual-row`（0,2,0）**，它是两段选择器 | 选择器改为 `.manual-input .manual-row`（0,2,0），不再用 `!important` |
| `07` `.workflow-container` | `padding: 10px 12px !important` | `06` 的两处同名规则 | 去掉 `!important` |

**实测结果**（改前 / 改后两轮探针，9 项全部 `identical`）：

| 观测点 | 值 |
| --- | --- |
| 六爻选中行 `td` 背景 / 文字 / 字重 | `rgba(0,0,0,0)` / `rgb(32,38,34)` / `400` |
| 六爻发动爻 `td` 背景 / 文字 / 字重 | `rgb(245,238,232)` / `rgb(130,48,36)` / `650` |
| 大六壬地盘/天盘/天将悬停（三行同地支） | 背景 `rgb(166,109,30)`、文字 `rgb(255,255,255)`、圆角 `3px` |
| 375px 下 `.workflow-container` padding | `10px 12px` |
| 375px 下 `.form-row` / `.numbers-row` / `.manual-row` 列宽 | `317px` / `100.328px 100.328px 100.344px` / `317px` |

**这一步抓到一个真实回退**：第一版只把 `07` 的 `.manual-row` 去掉 `!important`，探针立刻报
`.manual-row` 从 `317px` 变成 `100.5px 100.5px 100px`——因为基础规则 `.manual-input .manual-row`
是两段选择器（0,2,0），压得过单段的 `.manual-row`（0,1,0）。把媒体查询里的选择器也写成
`.manual-input .manual-row` 才恢复。**没有这个计算样式比对，这个回退只会在手机上肉眼可见。**

### 第二批（同一轮继续）：打印态与 `casting-note`，20 处 → 3 处

第一批之后剩的 20 条集中在打印与无障碍，验证方式换成 Playwright 的
`page.emulateMedia({ media: "print" })`：同一套探针在 **1440 与 375 两个宽度**、**屏幕与打印两种媒体**
下采集 `getComputedStyle`，并覆盖经典结果页与七步结果页两套界面。

| 位置 | 原写法 | 原来在压谁 | 改法 |
| --- | --- | --- | --- |
| `05` 打印块 `body` ×2 | `background/color … !important` | 01 里的 `body` 基础规则（0,0,1） | 选择器写 `html body`（0,0,2） |
| `05` 打印块 7 个隐藏项 | `display: none !important` | 03/07 里的同名规则，且多在移动端媒体查询里（更晚加载） | 统一加 `.app-shell` 前缀（0,2,0），不依赖加载顺序 |
| `05` `.result-workspace` ×3 | `padding/max-width/box-shadow !important` | 03 移动端 `.result-workspace`（0,1,0） | 加 `.app-shell` 前缀 |
| `06` 打印块 `.workflow-container` ×2 | `overflow/padding !important` | 06 更早的媒体查询同名规则 | 加 `.app-shell` 前缀 |
| `06` 打印块 11 个隐藏项 | `display: none !important` | 07 的 `.result-tabs`、`.collapsible-header` 等（更晚文件） | 加 `.app-shell` 前缀 |
| `06` 打印块 `.result-content` | `display: block !important` | 同时挂着 `.interact-view`，两条隐藏规则会抢 | 加前缀并保持**后置**（同特异性靠顺序取胜） |
| `06` 打印块 `.formatted-result` ×4 | `max-height/overflow/border/padding !important` | **07 的 `.formatted-result { max-height: 60vh; padding: 10px 12px }`（更晚文件）** | 加 `.app-shell` 前缀（0,2,0）压过 0,1,0 |
| `06` `.casting-note` ×3 | `font-size/color/margin-top !important` | `.casting-state p`（0,1,1），单类名的 `.casting-note` 压不过 | 选择器写 `.casting-state .casting-note`（0,2,0） |
| `06` 无障碍 `prefers-reduced-motion` ×3 | `!important` | 任意组件上的 animation/transition 声明 | **保留并写明理由**：要覆盖未知选择器，靠特异性无法穷举 |

**实测结果**（23 个观测点全部 `identical`）：

| 观测面 | 观测点与值 |
| --- | --- |
| 经典结果页 · 打印 · 1440 | `body` 背景 `rgb(255,255,255)` / 文字 `rgb(0,0,0)`；导航、输入列 `display:none`；`.result-workspace` padding `0px`、max-width `100%`、box-shadow `none`；`.result-tabs` `none`；`.result-content` `block` |
| 经典结果页 · 打印 · 375 | 同上 6 项全部一致（含 `.mobile-topbar` 隐藏） |
| 七步结果页 · 打印 · 1440 | `.result-tabs` `none`；`.result-content` `block`；`.formatted-result` max-height `none` / overflow `visible` / border `0px` / padding `0px`；`.btn-secondary` 与 `.result-actions` `none`；`.fortune-banner` `break-inside: avoid`；`.interact-view` `block`（原行为即如此，未改变）；`.collapsible-header` `none` |
| 创建页 · 打印 · 1440 / 375 | `.workflow-container` overflow `visible`、padding `0px` |
| `.casting-note`（等构 DOM 注入测级联） | `12px` / `rgb(166,109,30)` / margin-top `16px` |
| 打印态抽屉层（额外补验，前缀最担心的点） | `.history-drawer`、`.rules-drawer`、`.drawer-layer` 三者 `display: none`，且 `closest(".app-shell")` 均为真 |

**踩到的一个坑**：七步结果页那段一开始恢复到了错误的会话——数据库里同时存在「打印态探针」的
`draft` 与 `casted` 两条记录，抽屉按更新时间倒序，点中的是 `draft`，于是恢复出来是创建页而不是
结果页（超时 20s 才发现）。改成先按 `casted` 过滤卡片，并清掉残留 `draft` 后稳定复现。

打印截图**不做逐字节比对**（结果页含随机卦象，两次起盘内容不同），判据只用计算样式。

### 收尾：`!important` 27 → 3

| 文件 | 剩余 | 说明 |
| --- | --- | --- |
| `06-explanation.css` | 3 | `prefers-reduced-motion: reduce` 的 `scroll-behavior/animation-duration/transition-duration`，已就地写明保留理由 |
| 其余 6 个样式文件 | 0 | — |

### 验证结果（第十一轮）

| 验证项 | 命令 | 结果 |
| --- | --- | --- |
| 前端构建 | `npm run build` | 通过：`index-BgJPUQVB.css 99.06kB（gzip 17.83）/ WorkflowPanel-_dRwNEfE.js 42.84kB / ResultWorkspace-C32M0k6z.js 91.45kB / index-CGF2Qv_o.js 63.97kB / react 182.10kB` |
| 前端单测 | `npm run test:unit` | 7 文件 / 45 用例通过 |
| 浏览器烟测 | `npm run test:browser` | **passed**；新增「交互深化」段：展开折叠面板 → 选「符合」→ 提交现实校验 → 断言 `交互记录(N)` 页签带计数 |
| 后端全量回归 | `pytest backend/tests -q` | **709 passed / 10 skipped / 0 failed**（本轮未改后端，跑一次确认无漂移） |
| 视觉等价 | 两批 Playwright 计算样式比对 | 第一批 9 项 + 第二批 23 项，全部 `identical` |
| `!important` 计数 | `Select-String -Pattern "!important"` | 27 → **3 条声明**（只剩无障碍降级三条） |
| 会话数据 | 清理本轮探针/烟测会话 | 4 个探针会话已删，保留 4 个用户会话 |

**CSS 哈希说明**：第十轮记的「拆分前后 `index-Dmmh7YvJ.css` 逐字节相同」是**拆分当次**的判据；
第十一轮确实改了样式声明（24 条 `!important` 换成更高特异性选择器），产物因此一路变到
`index-BgJPUQVB.css`，体积 98.96 → 99.06 kB。这不是回退，是预期内的内容变化，视觉等价由计算样式比对保证。

## 第十二轮（2026-11-05）：pydantic v1 → v2 迁移（审计 24）

审计 24 是本轮最后一个未闭环项。它不是「能不能启动」的问题：FastAPI 0.103 在 pydantic 2 下照样起服务，
真正的问题是 v1 写法在 v2 里**语义变了但不报错**——`regex=` 被忽略、`min_items=` 不生效、`@validator`
的旧签名抛 TypeError 被 422 兜住、`.dict()` 不存在。对「同一输入必须同一输出」的推演系统来说，
入参约束被悄悄放宽是最坏的一类失败。

### 改了什么（46 处 v1 写法，全部在 `app/main.py` 与两个 `models.py`）

| v1 写法 | v2 写法 | 数量 |
| --- | --- | --- |
| `constr(..., regex=r"^[A-Za-z0-9_-]+$")` | `constr(..., pattern=r"...")` | 1 |
| `conlist(..., min_items= / max_items=)` | `conlist(..., min_length= / max_length=)` | 8 处（16 个参数） |
| `@validator(..., pre=True)` 与 `@validator(...)` | `@field_validator(..., mode="before")` / `@field_validator(...)`，并补 `@classmethod` | 3 |
| `.dict()` | `.model_dump()` | 30 |
| `Field(..., example="...")` | `Field(..., json_schema_extra={"example": "..."})` | 19 |

`Field(example=)` 在 v2 里能落进 schema，但走的是「未知关键字」路径并会告警；改成显式
`json_schema_extra` 后 OpenAPI 里仍是同一个 `example` 键，文档形状不变、告警消失。

依赖同步改为 `pydantic>=2.9,<3`；`test_dependency_contract.py` 的断言从「主版本必须为 1」
改成「主版本必须为 2 + 上下界都在」，并新增一条**反向守卫**：`app/` 下不许再出现
`regex=` / `min_items=` / `max_items=` / `@validator(` / `.dict()`，命中就报出文件名和原因。

### 怎么证明没把契约改坏

迁移前先用 TestClient 采一份**契约基线**，迁移后用同一脚本重采并逐项比对：

| 比对项 | 结果 |
| --- | --- |
| 14 个非法入参用例的状态码 | 完全一致（13 个 422 + 1 个 200） |
| `detail[].loc` 层级路径 | 完全一致，含 `["body","lines",0]`、`["body","context","category"]` 这类嵌套路径 |
| 3 个合法请求的成功响应骨架 | 一致（键集合相同） |
| OpenAPI paths | 完全一致（55 条路由零漂移） |
| OpenAPI schema 数量 | 31 → 31 |

**两类预期内差异，已确认不是回退**：

1. OpenAPI 表达更准确：`Optional[X]` 从「直接写 X」变 `anyOf: [X, {"type": "null"}]`，
   `Dict[str, Any]` 补 `additionalProperties: true`。这是 v2 的 schema 生成方式，语义更准，不影响校验。
2. 校验失败文案与 `type` 码换成 v2 措辞，例如 `"ensure this value has at least 6 items"` +
   `value_error.list.min_items` → `"List should have at least 6 items after validation, not 3"` + `too_short`；
   自定义校验器抛的 `ValueError` 文案带 `"Value error, "` 前缀。**结构没变**（仍是 422 + `detail[]`，
   每项有 `loc/msg/type`），前端 `api.js` 读 `detail[0].msg` 照旧可用。

### 迁移带来的严格度变化（净收益）

v2 的 lax 模式不再把 `6.5` 截断成 `6`，也不再把数字自动转成字符串——这些原来会被悄悄放过的入参
现在直接 422。这正是本次迁移想要的结果。

### 验证结果（第十二轮）

| 验证项 | 命令 | 结果 |
| --- | --- | --- |
| 后端全量回归 | `pytest backend/tests -q` | **717 passed / 10 skipped / 0 failed**（迁移前 709；新增 `test_validation_contract.py` 7 例 + v1 语法守卫 1 例） |
| 后端 lint | `ruff check app tests` | All checks passed |
| 契约基线比对 | 迁移前后各跑一次同一脚本 | 状态码 / `loc` / 成功骨架 / 路由 / schema 数量全部一致 |
| 依赖声明 | `requirements.txt` | `pydantic>=2.9,<3`，注释同步改写 |
| 前端 | `npm run build` / `npm run test:unit` | 未改前端，产物无变化（`index-BgJPUQVB.css` 99.06 kB） |

### 审计 24 之后的余项（诚实边界）

28 条里仍**未做**的只剩审计 22 一处，且不是「改代码」能收口的：会话归属校验（`main.py` 的会话端点按 `session_id` 直取，没有身份体系就没有归属可言）。审计 14 的反向通道已在第十三轮补上。

## 第十三轮（2026-11-05）：本地存档 → 后端会话（审计 14 反向）

第九轮把「抽屉 → 后端会话」打通，留下的另一半是「本地存档 → 后端」。读代码后先确认一件事：
**两边不是同一份数据，所以"写回"不可能是把旧 JSON 塞进后端。**

| | 本地存档（`storage.js`） | 后端会话（`data/sessions/*.json`） |
| --- | --- | --- |
| 存什么 | `/v1/calculations/compare` 的应答包：`module_results` + `advisory` + `task_id` | 七步工作流的冻结快照 `snapshot` + `workflow_result` + 交互记录 |
| 有没有盘面 | 一次算完的九体系结果 | 不可变快照，按 step1–step7 组织 |
| 有没有交互 | 没有 | 现实校验 / 多方取象 / 多抉择 / 复盘 / 追问 |
| 有没有起盘入参 | 历史上只存 `{scene,category,question}` | `casting_source`（`local_datetime`/`timezone`/`cast_nonce`/…） |

所以通道做成「**用存档的事由与起盘时刻，在后端重建一个可继续交互的会话**」，而不是伪造一次写回。

### 改了什么

| 文件 | 改动 |
| --- | --- |
| `frontend/src/lib/sessionMigration.js`（新） | `resolveCastingSource` 三级回退取起盘时刻：新存档的 `item.input` → 旧存档里历法结果回显的 `input` → 存档的 `calculated_at`；`resolveCategory` 把旧别名（`wealth`/`job`/…）归一到后端 11 个规范键，认不出的一律 `other`；`buildMigrationPayload` 组装 `POST /v1/sessions` 请求体（`casting_method: "time"`、`cast_nonce` 每次新建）；`migrateHistoryItem` 串起 建会话 → `/cast`，返回 `session_id` 与保真说明 |
| `frontend/src/App.jsx` | 抽屉本地存档卡片新增「转到后端」按钮（失败在抽屉里显示错误条）；`handleSubmit` 的 `ctx` 增加 `input` 字段，把 `local_datetime`/`timezone`/`cast_nonce`/`use_true_solar_time` 随存档落盘，让今后的存档可精确还原 |
| `frontend/src/lib/sessionApi.js` | `import.meta.env?.VITE_API_ROOT` 改可选链：该模块现在也会被纯 node 测试进程 import，那里没有 `import.meta.env`，原写法直接 TypeError |
| `frontend/package.json` | `test:node` 纳入 `tests/session-migration.test.mjs` |
| `frontend/tests/session-migration.test.mjs`（新，8 例） | 起盘时刻三级回退、分类别名归一与降级、请求体契约、`cast_nonce` 每次重生成、无题存档明确报错 |
| `frontend/tests/smoke.mjs` | 新增反向段：桌面推演自动存下的本地存档 → 点「转到后端」→ 抽屉关闭 → 结果页出现 → 再查 `GET /api/v1/sessions` 断言确实多了一条 `status=casted`、事由一致的会话 |

### 保真边界（写进代码注释与界面提示，不靠口口相传）

- **能还原**：求测事由、事项分类、起盘时刻（`local_datetime` + `timezone`）；旧存档可依据历法结果里的 `input` 回显取回，不依赖用户重填。
- **不能还原**：`cast_nonce`（自动起卦的随机种子当时没落盘）。重建时重新生成，**因此盘面可能与存档盘面不同**——抽屉说明写的是「按存档时刻重建为交互推演会话」，代码与 `migrateHistoryItem` 的返回值里也带 `fidelity` 说明，不假装是原盘。
- **不做**：把 `module_results` 逐模块翻译成 step1–step7。那等于替引擎重推一遍，翻译错了没人能发现；宁可诚实地起一张新盘。
- 存档原件不清除：迁移只新增后端会话。

### 验证结果（第十三轮）

| 验证项 | 命令 | 结果 |
| --- | --- | --- |
| 前端纯模块测试 | `npm run test:node` | **34 passed / 0 failed**（26 + 新增 8） |
| 前端组件测试 | `npm run test:unit` | 45 passed（7 文件） |
| 前端构建 | `npm run build` | `built in 325ms`；`index-DwxeNsLe.js` 65.93 kB（上一轮 63.97，+1.96 kB 为迁移模块与按钮） |
| 浏览器烟测（含反向段） | `npm run test:browser` | **passed**：`history drawer ↔ backend sessions (both directions)` |
| 测试数据清理 | `clean_round13.py`（按 `question` + `created_at` 双条件） | 删掉 6 条本轮烟测会话；保留用户既有 4 条真实会话 |

烟测过程中修掉一个真实陷阱：抽屉打开时底下仍是上一次的结果页，直接等「推演结果」标题会被旧 DOM 瞬间满足，看起来"通过"但迁移其实是失败的。现在先等 `.history-drawer` **detached**（失败会留在抽屉里显示错误条），再断言结果页，并直接查后端会话列表确认新会话真的 `casted`。

## 第十四轮（2026-11-05）：会话归属校验（审计 22 收尾）

审计 22 的前两项（口令只从环境读、异常不外泄）第二轮就修了，剩下的「会话归属校验」一直卡在
"需要身份体系"。这轮换了问题切法：**不做账号，只做归属**。

问题本身很具体：`GET /v1/sessions` 列出这台机器上所有人的会话，`GET/DELETE/CAST/INTERACT`
只按 `session_id` 直取。`APP_API_TOKEN` 挡的是"外人进不来"，挡不住"同一部署里两个浏览器互读"。

### 改了什么

| 文件 | 改动 |
| --- | --- |
| `backend/app/session/ownership.py`（新） | `client_id_from` 校验 `X-Client-Id`（16–64 位 URL 安全字符）；`owner_hash` 只算 `sha256:` 前缀的哈希，原始 id 不落盘；`claim_or_match` 定义「空归属 → 认领、一致 → 通过、不一致 → 拒绝」 |
| `backend/app/session/models.py` | `DivinationSession` 增加 `owner_hash` 字段；`create_session(..., owner_hash=)` |
| `backend/app/session/store.py` | `list_sessions(limit, owner_hash=)` 按归属过滤（本人的 + 无归属的老会话），元数据里带上 `owner_hash` 供过滤，API 层再剥离 |
| `backend/app/main.py` | 6 个会话端点全部加 `Request` 参数并调 `_client_owner_or_error`：缺头/非法头 400 `CLIENT_ID_REQUIRED`；跨归属 403 `SESSION_FORBIDDEN`；列表只回本人；GET/DELETE/CAST/INTERACT 上首次访问老会话即认领并落盘。校验放在函数体内而不是 `Header(...)` 依赖，保证 `SessionCreateRequest` 的 422 契约先于归属校验发生（审计 24 的契约测试依赖这个顺序） |
| `backend/tests/test_session_ownership.py`（新，9 例） | 缺头/非法头 400；本人可读、他人 403；列表隔离且不泄漏 `owner_hash`；跨归属删除/排盘/交互 403 且不写盘；老会话首访问认领后他人 403、且仍在列表可见 |
| `frontend/src/lib/clientIdentity.js`（新） | 客户端 id 生成与持久化（`tianji_client_id_v1`）：`crypto.randomUUID` 去掉连字符，无则 16 字节随机；localStorage 里的值先校验再用，坏值重新生成；读写失败退化为进程内 id，不阻塞使用 |
| `frontend/src/lib/sessionApi.js` | 所有会话请求统一加 `X-Client-Id` 头 |
| `frontend/tests/client-identity.test.mjs`（新，4 例） | 进程内稳定、格式合法、写入约定键且"刷新"后不变、坏值重建 |
| `frontend/tests/smoke.mjs` | 反向段的会话列表断言改为带 `X-Client-Id`（否则 400） |

### 边界（写进代码与文档）

- **老会话的认领窗口**：迁移前的会话（`owner_hash` 为空）第一个带合法 id 访问它的客户端即成为 owner。
  这是有意的取舍——否则用户那几条真实历史会在升级后直接"消失"。窗口只在"还没人打开过"期间存在。
- **不做账号/登录**：换浏览器就是另一个身份，会话不会跟人走；这解决的是同部署互读，不是跨设备同步。
- **运维脚本**：`clean_round13.py` 这类维护动作改走存储层删除，不经 HTTP（没有浏览器里那份 id）。
  直接 `curl` 调试会话接口需要自行带 `X-Client-Id`，这是行为变化，已记入上面的清单第 8 条。

### 验证结果（第十四轮）

| 验证项 | 命令 | 结果 |
| --- | --- | --- |
| 归属校验用例 | `pytest tests/test_session_ownership.py -q` | **9 passed** |
| 后端全量回归 | `pytest tests -q` | **726 passed / 10 skipped / 0 failed**（上轮 717 + 新增 9） |
| 后端 lint | `ruff check app tests` | All checks passed |
| 真实运行验证 | 重启 8092 后打接口 | `/health` 200；无头 `GET /v1/sessions` **400 `CLIENT_ID_REQUIRED`**；带头 200 |
| 前端 | `npm run test:node` / `test:unit` / `build` | 38 passed / 45 passed / built in 410ms（`index-CGZBQK5I.js` 66.41 kB） |
| 浏览器烟测 | `npm run test:browser` | **passed**（归属校验开启后，创建/列表/恢复/重建全链路照常） |
| 测试数据清理 | `clean_round13.py`（改为存储层删除） | 删掉 2 条本轮烟测会话；保留用户既有 4 条真实会话 |

## 第十五轮（2026-11-07）：把「写了但没人读 / 读了但没人写」的展示字段补齐

这轮不再按清单走，而是成对核对「写入端—读取端」：组件用默认值兜底时不会抛异常，
构建和单测都绿，但用户看到的是另一份盘。

### 修掉的四个真实缺陷

| # | 现象 | 根因 | 修复 |
| --- | --- | --- | --- |
| 1 | 六爻六神永远是「青龙、朱雀、勾陈、螣蛇、白虎、玄武」固定序列，和日干推出来的无关 | 引擎只把 `six_spirit` 放在逐爻 `line_chart` 与 `steps` 里；`build_plate_facts` 和 `compact_plate_output` 都没收成 `six_spirits`，前端读到空值就回退到写死的默认数组 | `plate_facts.py` 新增 `_line_field`：按爻位顺序（初→上）从 `line_chart` 收 `six_spirits`/`liuqin`，六爻不齐则留空；`compact_plate_output` 同步补这两个键 |
| 2 | 即使拿到真实六神，六神也整体上下颠倒（初爻显示上爻的神） | `HexagramView` 用 `spirits[5 - lineIdx]`，而数组是初→上 | 改为 `spirits[lineIdx]`，并加组件测试钉住初爻/上爻/三爻 |
| 3 | 梅花与六爻同时存在（auto 默认场景）时六神/六亲取不到 | 组件拿到第一个有卦象的体系就 `break`，梅花那份没有六神 | 卦名取第一个体系，六神/六亲/动爻改为跨体系补齐 |
| 4 | 「转到后端」对真太阳时的存档直接起盘失败 | 反写只带 `use_true_solar_time`，没带 `longitude`；后端缺经度明确拒绝 | `resolveCastingSource` 从 `input.longitude` 或历法回显补经度；真太阳时找不到经度时明确报错，不静默降级；`App.jsx` 落盘补 `longitude` |

顺带修两处展示层不一致：

- 结果页事项分类标签原本手写 6 项，官司/寻人/失物/健康/抉择五类渲染成 `undefined`，
  另四项中文也与下拉不一致。改为从 `lib/labels.js` 的 `CATEGORIES` 派生，
  并加测试断言「11 类全覆盖且与下拉同字」。
- 「N 个计算模块」原本写死（综合推演显示 5，实际是日历 + 七个体系 = 8）。改为按
  `buildCalculations(form).length` 显示，并加组件测试。

### 验证结果（第十五轮）

| 验证项 | 命令 | 结果 |
| --- | --- | --- |
| 盘面事实用例 | `pytest tests/test_plate_facts.py -q` | **19 passed**（新增 3 例） |
| 后端全量回归 | `pytest tests -q` | **729 passed / 10 skipped / 0 failed**（上轮 726 + 3） |
| 后端 lint | `ruff check app tests` | All checks passed |
| 前端纯模块 | `npm run test:node` | **42 passed**（新增分类标签契约 + 迁移经度 3 例） |
| 前端组件 | `npm run test:unit` | **48 passed**（新增六神顺序 2 例 + 模块数 1 例） |
| 前端构建 | `npm run build` | 通过（`index-BhH4xOdD.js` 66.69 kB） |
| 真实运行 | 建会话 → cast → 读回 step2 | `six_spirits` 与引擎逐爻值完全一致（`玄武…白虎`）；真太阳时 + 经度起盘 **200**；`owner_hash` 未泄漏 |
| 浏览器烟测 | `npm run test:browser` | passed（开发服务器需 `VITE_PROXY_TARGET` 指向实际后端端口） |

### 仍未收口（事实陈述）

- 审计 11：ClickHouse 客户端与语料检索客户端未合并，依赖不同服务。
- 审计 12：前后端两份体系映射仍在。本轮核对过键集，当前没有漂移（前端能发出的
  `module/method` 全在后端分发表里），属于结构性问题而非缺陷；彻底收口需要新增计划接口。
- 第十五轮之前冻结的旧会话 `plate_facts` 里本来就没有六神字段，这些会话仍走前端回退序列；
  新起盘才会带真实值。

## 第十六轮（2026-11-07）：自测夹具掩盖的推导缺失

第十五轮补了 `build_plate_facts` 的六神收取，但 `compact_plate_output`（落盘快照与 `step2` 展示用的那一份）
仍然只读 `facts["six_spirits"]`。单测夹具预先放了这两个键，所以一直是绿的；真实起盘读回来却是
`six_spirits: None`。

| 现象 | 根因 | 修复 |
| --- | --- | --- |
| 真实快照 step2 读回 `six_spirits: None`、前端回退默认序列 | compact 侧没有从逐爻 `line_chart` 推导，夹具预置值把逻辑掩盖了 | `compact_plate_output` 增加与 `build_plate_facts` 相同的 `_line_field` 推导；测试先 `facts.pop("six_spirits")` 再断言，避免夹具再次掩盖 |

验证方式也改了：不再只看单测，而是重启后端后建会话 → cast → 读回 `step2`，逐字段与引擎 `line_chart` 比对，
`MATCH: True` 才收工。

## 第十七轮（2026-11-07）：继续写端—读端核对

### 修掉的六个缺陷

| # | 现象 | 根因 | 修复 |
| --- | --- | --- | --- |
| 1 | 任何卦都被画成「坤为地」（六条阴爻） | `_hexagram_brief` 只压平了卦名，没带 `lines`；`HexagramView` 在无 `lines` 时按 `TRIGRAMS[upper]` 拼爻，而快照里的上下卦键与组件读法不一致，查不到就退化成全阴 | `_hexagram_brief` 增加 `lines`（满 6 位才收，逐位归一到 0/1）；组件优先用 `lines`，无 `lines` 时才查卦名拼爻，并兼容 `upper_trigram.name` 与已压平的 `upper` |
| 2 | 奇门盘面在冻结快照与 step2 里完全空白 | `calculate_qimen_chart` 把 20 个键平铺在顶层，没有 `facts` 层；`step2_format_plate` 用 `result.get("facts", {})`、`build_plate_facts` 遇空 `facts` 直接 `continue` | 奇门结果补 `facts`（与其余体系同构），顶层键保留以不破坏既有契约 |
| 3 | 选八字/紫微/奇门/大六壬时 step2 整段空白，看不到四柱与局象 | `compact_plate_output` 只搬卦象字段（`original`/`line_chart`/`body_use`），这些体系根本没有这些键 | `plate_facts.py` 新增 `_dig`/`_domain_summary`：八字→日主/四柱/日主旺衰/大运，紫微→五行局/命宫/身宫/四化/宫位数，奇门→局象/节气/值符/值使/首选吉方，六壬→占日/占时/月将/三传/课体；`StructuredDisplay` step2 逐体系渲染 `{体系}盘面：` + 列表 |
| 4 | `step5.hexagram_explanation` 恒为 `null`，象义解读只剩六神 | `hexagram_service._FALLBACK_FILE` 用 `parents[2]` 拼成 `backend/data/rules/`，而文件在**仓库根** `data/rules/`；本地无 ClickHouse 时回退分支永远走不到 | 改为 `parents[3]`（与 `fengshui/storage.py`、`session/store.py`、`common/classics.py` 一致），并加 3 例测试：文件存在、无数据库时能取到「大有」释义、未知卦返回 `None` |
| 5 | 紫微「身宫」显示 `{'earthly_branch': '卯', ...}` 原始字典 | `shen_palace` 是 dict，摘要直接 `str()` | 先取 `palace_stem_branch`，退回 `earthly_branch`，只在确为字符串时才直接用 |
| 6 | 部分起卦方式在界面上显示英文 key | 前端 `CAST_METHOD_LABELS` 缺 `three_coins`/`six_lines`/`three_numbers`/`numbers`/`eight_palace_pure_hexagram` | 按后端实际取值补齐标签 |

### 真实运行核对（六体系逐个起盘）

| 体系 | step2 `summary` | step5 象义条目 |
| --- | --- | --- |
| 梅花 | `{}`（卦象走 `original`） | **2**（修前 **0**） |
| 六爻 | `{}` | **8**（6 条六神 + 本卦/类别象义，修前 **6**） |
| 奇门 | 局象 `阴遁3局·下元`、节气 `寒露`、值符 `天柱 落 6 宫`、值使 `惊门 落 4 宫`、首选吉方 `正南方 · 开门 · 离九宫` | 0（无卦象，符合设计） |
| 大六壬 | 占日 `癸未`、占时 `巳`、月将 `太冲`、三传 `巳 → 戌 → 卯`、课体 `比用` | 0 |
| 八字 | 日主 `癸（水）`、四柱 `丙午 戊戌 癸未 丁巳`、日主旺衰 `极弱`、大运 `8 步` | 0 |
| 紫微 | 五行局 `水二局`、命宫 `癸巳`、身宫 `辛卯`、四化四条、宫位 `12 宫` | 0 |

### 验证结果（第十六—十七轮，追补前）

| 验证项 | 命令 | 结果 |
| --- | --- | --- |
| 盘面事实 + 奇门 | `pytest tests/test_plate_facts.py tests/test_qimen.py -q` | **24 passed** |
| 卦象释义回退 | `pytest tests/test_hexagram_explanation_fallback.py tests/test_plate_facts.py -q` | **23 passed** |
| 后端全量回归 | `pytest tests -q` | **734 passed / 10 skipped / 0 failed**（上轮 729 + 5） |
| 后端 lint | `ruff check app tests` | All checks passed |
| 前端纯模块 | `npm run test:node` | **42 passed** |
| 前端组件 | `npm run test:unit` | **50 passed**（7 文件，新增非卦象盘面摘要 1 例） |
| 前端构建 | `npm run build` | 通过（`index-BO93z-s9.js` 66.69 kB / `index-BgJPUQVB.css` 99.06 kB，样式未变） |
| 真实运行 | 六体系逐个建会话 → cast | 六体系全部 200；各 `summary` 非空且字段值合理；step5 条目 2/8 |
| 浏览器烟测 | `npm run test:browser` | passed |

### 追补：非卦象体系不再借用六爻用神与卦象吉凶

上一版把这条记成「需要先定口径」。口径其实已经能定——**没有卦爻，就不该出现六亲**，
不是换一套吉凶算法，而是把不成立的概念撤掉。

| 体系 | 用神 | 依据 |
| --- | --- | --- |
| 八字 | 主：喜用五行（金、水）；辅：忌神五行 | 引擎 `day_master_strength.analysis.summary` 原文 |
| 紫微 | 按事项取用事宫（事业→官禄宫、财运→财帛宫、感情→夫妻宫、健康→疾厄宫…） | `ZIWEI_CATEGORY_PALACES`，辅以命宫/迁移宫 |
| 奇门 | 日干（求测人）/ 时干（所测之事） | 值符值使与用神宫门星神同参 |
| 大六壬 | 日干（求测人）/ 三传（事态脉络） | 初传发端、中传经过、末传结果 |

配套改动：

- `step3` 输出 `yongshen_framework`；`yongshen_by_system` 在无卦象时只放本体系一条。
- `step4` 对这类盘面给 `level: "不适用"`，不再用月令去算卦象旺衰；体用/世应置空并写明理由，
  `rule_ids` 为空（没有适用规则就不挂规则号）。
- `step6` 返回 `fortune_level: "未评级"`、`fortune_score: null`，依据写明「未排卦象体系，
  按 WF-FORTUNE-001 的口径无法出具等级」，不再伪造「平」；`timing` 置空。
- `step7` 首条建议改为「未排卦象体系，以盘面事实与顾问结论为参考」，不再说「卦象有阻」。
- `reference_library` / `reality_check` 两个附加模块同步更正：没有卦名时不再拼「本卦「」」，
  未评级时不再给「待用神得令」「吉凶参半」这类卦象口径文案；`reality_check` 的用神条目
  改为写明体系口径（「该体系不以卦象旺衰论强弱」）。
- 事后复盘（`interaction/review.py`）遇到「未评级」只写「不作吉凶应验判断」，不再拿
  未评级去比对方向、造出「未应验」。
- 前端：`FORTUNE_COLORS` 增加「未评级」灰；步骤3 多一行「取用体系」；大六壬四课关系改成
  查表显示（未知值原样输出，不再一律当「上克下」）。

实测（六体系逐个起盘）：梅花/六爻仍为 官鬼/父母 + 大吉/平；奇门、大六壬、八字、紫微均为
各自的用神口径、旺衰「不适用」、吉凶「未评级」、`fortune_score` 为 `null`。

### 验证结果（追补后）

| 验证项 | 命令 | 结果 |
| --- | --- | --- |
| 工作流 + 交互模组 | `pytest tests/test_workflow_steps.py tests/test_interaction_modules.py -q` | **217 passed**（工作流新增 9 例、复盘新增 1 例） |
| 后端全量回归 | `pytest tests -q` | **744 passed / 10 skipped / 0 failed** |
| 后端 lint | `ruff check app tests` | All checks passed |
| 前端组件 | `npm run test:unit` | **51 passed** |
| 前端纯模块 | `npm run test:node` | **42 passed** |
| 前端构建 | `npm run build` | 通过（`index-DdjovD7s.js` 66.71 kB / `index-BgJPUQVB.css` 99.06 kB） |
| 真实运行 | 六体系起盘核对 step3–step7 + `reference_library`/`reality_check` | 卦象体系口径不变；非卦象体系无六亲、无吉凶分、附加模块文案同步 |
| 浏览器烟测 | `npm run test:browser` | passed |
| 测试数据清理 | `clean_round13.py` | 删掉 2 条探测会话，保留 4 条真实会话 |

### 追补二：固定文本与交互文案里的卦象残留

界面和结构化数据改完后，继续按「写端—读端」核对文本与交互，又发现六处：

| # | 问题 | 修法 |
| --- | --- | --- |
| 1 | `render_plate_text` 对非卦象体系只输出一个「【奇门】」空标题，四柱/局象一概没有 | 补 `domain_summary` 摘要行；`plate_facts._domain_summary` 转公开 `domain_summary` |
| 2 | 固定文本的「本卦重点风险隐患」「本卦常见误读误区」「卦局显示」「卦象现状核对」对非卦象盘面仍是卦象措辞 | 按 `step5.hexagram_name` 有无切换「本卦/盘面」「卦象/盘面」 |
| 3 | `【起盘方式】：auto（{'local_datetime': …}）` 直接打印 dict；`timing` 为 `None` 时打印字符串 `None` | 起盘方式改为「体系 · 方法 · 起局时间」；`timing` 空值不再输出 |
| 4 | 未评级盘面的固定文本仍打印空的「有利点：」「阻碍点：」 | 未评级时各补一行「（本次未评级，不输出…因素）」 |
| 5 | 现实校验的换角度建议对非卦象盘面仍让人「更换动爻取象」「结合月令重估旺衰」 | `_suggest_angles` 按 `yongshen_framework` 给体系内建议；前端折叠面板标题改「盘面现状核对」（烟测同步） |
| 6 | 六爻静卦时「第  爻动」输出空爻位；`reference_library` 的可能性和误区仍是纯卦象话术、后续菜单写「本卦」 | 静卦显示「静卦无动爻」；无卦象时换成盘面口径文案，菜单改「本盘」 |

### 验证结果（追补二后）

| 验证项 | 命令 | 结果 |
| --- | --- | --- |
| 后端全量回归 | `pytest tests -q` | **746 passed / 10 skipped / 0 failed** |
| 后端 lint | `ruff check app tests` | All checks passed |
| 前端组件 | `npm run test:unit` | **51 passed** |
| 前端纯模块 | `npm run test:node` | **42 passed** |
| 前端构建 | `npm run build` | 通过（`index-Dz0gBI21.js` 66.71 kB / `ResultWorkspace-CEulSKua.js` 91.62 kB） |
| 真实运行 | 六体系起盘核对固定文本 | 奇门/六壬/八字/紫微都有「盘面摘要」行，无 `None`、无 dict repr、无「本卦」 |
| 浏览器烟测 | `npm run test:browser` | passed（标题改名后同步更新断言） |

### 追补三：交互深化不再把六爻符号套到非卦象盘面

固定文本收口后，用真实接口（建奇门会话 → cast → 三种 interact）核对，发现交互层仍会说六爻话：

| # | 问题 | 修法 |
| --- | --- | --- |
| 1 | `deep_question` 对奇门/八字盘面的「本卦和动爻怎么理解」仍输出【卦象符号深化】【动爻符号深化】【用神符号深化】，讲六亲六神、入墓绝 | 先读 `yongshen_framework`；非卦象盘面改走体系说明：本体系用神口径、旺衰`不适用`、盘面摘要、`未评级`，并说明卦名/动爻/六亲/六神不适用 |
| 2 | `angle_shift` 对非卦象盘面仍「重新审视本卦」「本卦无动爻」「妻财爻是本角度的核心用神」 | 非卦象盘面改讲本体系用神、旺衰、盘面摘要与吉凶定性；角度关键词只决定取象重心，不换卦爻 |
| 3 | `multi_choice` 未评级时落进「小凶/大凶」分支，输出「用神休囚或体用相克」「当前卦象整体偏阻滞」 | 非卦象盘面按体系给视角（日干/时干、命宫/用事宫、日干/三传…），明确「未做卦象吉凶评级，不按吉凶倾向排序」 |
| 4 | `core/interpretation.MODULE_LABELS` 只有 5 个体系，`step2` 对奇门/八字/风水直接拿 `qimen`、`bazi` 当 `system_label` 发给前端 | 补齐 `bazi`/`qimen`/`fengshui`/`daliuren`，并新增测试断言「每个可分发的体系都有中文标签且与 `SYSTEM_LABELS` 一致」 |

真实接口复测（奇门）：深度追问问「本卦和动爻」得到「奇门遁甲，未排梅花/六爻/周易，卦名、动爻、六亲、六神均不适用」+ 日干/时干口径；换角度得到「3. 奇门遁甲盘面摘要：…」；多选得到「未做卦象吉凶评级，不按吉凶倾向排序」。

验证：`pytest tests` **751 passed / 10 skipped / 0 failed**；`ruff check app tests` All checks passed；前端三套（51 / 42 / build）与浏览器烟测仍通过。

### 仍未收口（事实陈述）

- 第十五轮之前冻结的旧会话没有新字段（六神、`lines`、`summary`、`yongshen_framework`），
  界面仍走各自回退分支；新起盘才带真实值。
- 审计 11 / 12 的结构性收口仍未做（见第十五轮说明）。
- 「未评级」是撤掉假评分后的诚实结果，不代表已经给这些体系设计了独立的吉凶算法；
  若要让八字/紫微也有吉凶档位，需要另外立规则并登记到规则库。

## 第十八轮修复（2026-11-07）

本轮针对全项目深度 Review 发现的算法节气边界缺陷、解释/考据体系完备性、历法语料库接入断层以及前端组件契约鲁棒性进行专项修复与验证。

### 修复项清单

| # | 模块 | 缺陷/缺口 | 根因与修复方案 | 落地位置 |
| --- | --- | --- | --- | --- |
| 1 | 奇门遁甲 | 夏至等中气起盘时节气判断偏差 | `lunar_python` 的 `getPrevJie()` 仅返回 12 节，而夏至/冬至为中气。导致夏至当日查到芒种、阴阳遁与三元错翻。修复为优先使用当前或前一全节气 `(solar_terms.current or solar_terms.previous)` | `backend/app/qimen/engine.py`、`tests/test_qimen.py` |
| 2 | 解释系统 | 八字与奇门缺少专属事实解释器 | `backend/app/core/explanation.py` 仅覆盖六爻/梅花/周易，未对 `bazi` 与 `qimen` 生成结构化解释段落。补齐 `_bazi_explanation`（强弱/格局/用神）与 `_qimen_explanation`（局象/值符值使/门星象意）并注册到分发入口 | `backend/app/core/explanation.py`、`tests/test_explanation.py` |
| 3 | 典籍考据 | 奇门与紫微经典引证与候选匹配缺失 | `core/literature.py` 缺乏《奇门遁甲统宗》与《紫微斗数全书》典籍定义，关键词提取漏掉门星格局与命宫四化。补齐经典条目定义、query_terms 提取与打分权重 | `backend/app/core/literature.py`、`tests/test_literature.py` |
| 4 | 典籍库语料 | 历法语料库未参与检索索引构建 | 脚本生成的 `data/generated/calendar-corpus`（《历法溯源》、《中国古代天体测量学》、《步天歌》等）未被 `ClassicsLibrary` 加载。配置 `DEFAULT_CALENDAR_CORPUS_DIR` 并合并至内存倒排索引与典籍清单 | `backend/app/common/classics.py`、`tests/test_classic_grounded_modules.py` |
| 5 | 前端解释视图 | ExplanationView 标题与规则标识渲染契约不兼容 | 后端返回 `title` 与 `rule_ids: list`，前端视图组件仅读取 `heading` 与 `rule_id: string`。增加 `section.heading \|\| section.title` 与列表拼接兼容降级，补齐前端组件单测 | `frontend/src/components/result/ExplanationView.jsx`、`tests/components/ExplanationView.test.jsx` |
| 6 | 工作流用神 | 非卦象体系多方人物取象误套用世应 | 多方人物分析时在奇门/八字盘面上仍输出「世爻/应爻」。修改为使用本体系对应符号（如奇门日干/时干）映射并断言 | `backend/app/workflow/steps.py`、`tests/test_workflow_steps.py` |
| 7 | 测试与加固 | API 加固用例断言错误封套与参数缺失 | 修正 `test_api_hardening.py` 对 422/限流错误封套的断言口径，修复玄空端点缺失的年份入参 | `backend/tests/test_api_hardening.py` |

### 验证结果

| 验证项 | 命令 | 结果 |
| --- | --- | --- |
| 后端全量回归 | `python -m pytest backend/tests` | **768 passed / 10 skipped / 0 failed**（无任何异常失败） |
| 前端纯模块测试 | `npm --prefix frontend run test:node` | **42 passed** |
| 前端单元测试 | `npm --prefix frontend run test:unit` | **53 passed**（8 个测试套件全绿） |
| 前端生产构建 | `npm --prefix frontend run build` | **通过**（Rollup 按需分包构建完成，零告警） |






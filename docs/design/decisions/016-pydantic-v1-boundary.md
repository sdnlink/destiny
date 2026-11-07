# 016 pydantic v1 与 v2 的边界

- 状态：已接受，且**已于 2026-11-05 完成 v1 → v2 迁移**（见文末「迁移结果」）
- 日期：2026-11-04（决策）／2026-11-05（迁移落地）

## 背景

后端 `requirements.txt` 锁定 `pydantic==1.10.26`，代码里用的是 v1 API：

- `constr(strip_whitespace=True, min_length=..., regex=...)`
- `conlist(..., min_items=..., max_items=...)`
- `@validator(...)`
- `model.dict()`

FastAPI 0.103 同时支持 v1/v2，所以环境升级 pydantic 到 2.x 不会报错启动，
但上面这些写法在 v2 里语义变了：`regex=` 改名 `pattern=`、`min_items` 改名 `min_length`、
`validator` 改名 `field_validator` 且默认不再接受 `pre=True` 的旧签名、`.dict()` 变 `.model_dump()`。
装到 v2 的直接后果不是崩，而是**入参校验被静默放宽或抛 TypeError 被 422 兜住**，
对「确定性计算」的项目来说这是最坏的一类失败。

## 决策

1. `requirements.txt` 把依赖写成 `pydantic>=1.10.26,<2`，让上界成为显式约定，而不是恰好装到的版本。
2. 本轮不做 v1 → v2 迁移。理由是迁移会改变全部 26 个入参模型的错误结构与字段约束，
   与工作流快照、校验案例的既有输出兼容性需要单独一轮验证窗口，不适合与其他修复混在一次提交里。
3. 迁移时的验收清单（下一轮直接照做）：
   - `constr(regex=...)` → `constr(pattern=...)` 或 `Annotated[str, StringConstraints(pattern=...)]`；
   - `conlist(..., min_items/max_items)` → `min_length/max_length`；
   - `@validator(..., pre=True)` → `@field_validator(..., mode="before")`；
   - `.dict()` → `.model_dump()`；
   - 跑完整 `pytest`，并核对 `/v1/calculations` 的 422 响应体结构未变。

## 后果

- 干净机器上 `pip install -r requirements.txt` 不会拉到 v2；
- `tests/test_dependency_contract.py` 会断言当前安装的 pydantic 主版本为 1，防止 CI 环境漂移；
- 迁移成本被显式记录，不再靠注释口口相传。

## 迁移结果（2026-11-05）

上面第 2 条的「本轮不做迁移」已被执行，本节记录实际做了什么、验证到什么程度。

### 代码改动（全部集中在 `app/main.py`，共 4 类写法）

| v1 写法 | v2 写法 | 数量 |
| --- | --- | --- |
| `constr(..., regex=r"...")` | `constr(..., pattern=r"...")` | 1 |
| `conlist(..., min_items=/max_items=)` | `conlist(..., min_length=/max_length=)` | 8 处（16 个参数） |
| `@validator(..., pre=True)` / `@validator(...)` | `@field_validator(..., mode="before")` + `@classmethod` / `@field_validator(...)` + `@classmethod` | 3 |
| `.dict()` | `.model_dump()` | 30 |
| `Field(..., example="...")` | `Field(..., json_schema_extra={"example": "..."})` | 19（`main.py` 14 + `bazi/models.py` 3 + `qimen/models.py` 2） |

`Field(example=...)` 在 v2 里虽仍能落进 schema，但会走「未知关键字」分支并告警；改成显式
`json_schema_extra` 后 OpenAPI 里仍然是同一个 `example` 键，不改变文档形状。

依赖声明同步改为 `pydantic>=2.9,<3`（`requirements.txt`），`test_dependency_contract.py` 的
断言从「主版本必须为 1」改为「主版本必须为 2 + 上下界都在」。

### 验证方法

迁移前先用 TestClient 采了一份**契约基线**（`pyd1_baseline.json`）：14 个非法入参用例的
完整响应体、3 个合法用例的响应骨架、31 个 OpenAPI schema。迁移后用同一脚本重采并逐项比对。

| 比对项 | 结果 |
| --- | --- |
| HTTP 状态码（14 个用例） | 完全一致（13 个 422 + 1 个 200） |
| `detail[].loc` 层级路径 | 完全一致（含 `["body","lines",0]`、`["body","context","category"]` 这类嵌套路径） |
| 3 个合法请求的成功响应 | 骨架一致（键集合相同） |
| OpenAPI paths | 完全一致（55 条路由零漂移） |
| OpenAPI schema 数量 | 31 → 31 |

### 两类预期内的差异（已确认不是回退）

1. **OpenAPI 表达更准确**：`Optional[X]` 从「直接写 X」变成 `anyOf: [X, {"type": "null"}]`，
   `Dict[str, Any]` 补上 `additionalProperties: true`。这是 v2 的 JSON Schema 生成方式，语义更准确，
   不影响请求校验。
2. **校验失败文案与 `type` 码换成 v2 措辞**：例如
   `"ensure this value has at least 6 items"` + `value_error.list.min_items`
   → `"List should have at least 6 items after validation, not 3"` + `too_short`；
   自定义校验器抛的 `ValueError` 文案会带 `"Value error, "` 前缀（`type` 仍是 `value_error`）。
   **响应结构没变**（仍是 422 + `detail[]` 且每项有 `loc/msg/type`），前端 `api.js` 读
   `detail[0].msg` 照旧可用。`tests/test_validation_contract.py` 把这条结构写成 7 个断言守住。

### 迁移后的校验严格度变化（更严，符合「确定性计算」取向）

v2 的 lax 模式不再把 `6.5` 截断成 `6`、也不再把数字自动转成字符串——原来会被悄悄放过的入参
现在直接 422。这正是本次迁移想要的净收益。

### 回归结果

`pytest backend/tests -q`：**717 passed / 10 skipped / 0 failed**（迁移前 709；新增
`test_validation_contract.py` 7 例 + `test_dependency_contract.py` 1 例 v1 语法守卫）；
`ruff check app tests`：All checks passed。

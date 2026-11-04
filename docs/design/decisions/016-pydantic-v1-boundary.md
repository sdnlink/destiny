# 016 pydantic v1 与 v2 的边界

- 状态：已接受
- 日期：2026-11-04

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

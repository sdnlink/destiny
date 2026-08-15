# MVP计算服务

> 状态：工程基线可运行，术数解释规则与标准案例待专家签署
> 服务入口：`http://127.0.0.1:8090`

## 1. 能力边界

当前服务提供确定性的历法、周易和梅花易数事实计算，以及多模块并列计算和结构化判断比较。计算内核不访问语料库，不调用语言模型，也不根据未经审核的经典文本自动生成吉凶、应期或事项建议。

设置`SERVE_WEB=1`后，服务会在所有API路由之后挂载`frontend/dist`。生产启动脚本负责设置该变量；计算内核本身不依赖前端代码。

已实现：

- 显式IANA时区、公农历、节气、四柱和可选真太阳时。
- 周易手工六爻、双数起卦及本卦、变卦、互卦、错卦、综卦。
- 梅花农历时间起卦、双数起卦、体用和五行关系事实。
- 规范输入哈希、幂等任务编号、多模块并行计算。
- 规则登记、来源引用、规则集合校验和工程案例回归。
- 对已发布结构化判断进行一致、互补、冲突和无法判断分类。
- 根据本次计算事实生成可追溯的结果摘要和逐模块详细说明。

未实现或未批准：

- 周易事项解释、梅花旺衰、应期和行动建议。
- 任何自动吉凶总分、现实概率或准确率。
- 专家规则发布工作流及签署后的生产规则。
- 用户账号、案例档案、持久化任务、报告和前端结果页。
- 六壬、八宅、玄空飞星及其他专业风水规则。

## 2. 启动与安全

安装依赖后启动：

```bash
./scripts/run_mvp_api.sh
```

默认只监听`127.0.0.1:8090`。修改端口：

```bash
APP_API_PORT=8091 ./scripts/run_mvp_api.sh
```

监听非回环地址时必须设置令牌，否则启动脚本直接退出：

```bash
APP_API_BIND=0.0.0.0 APP_API_TOKEN='replace-me' ./scripts/run_mvp_api.sh
```

启用令牌后，所有请求添加`Authorization: Bearer <token>`。当前令牌方案只用于受控内部环境，不能替代正式账号、租户权限、限流、审计和TLS。

## 3. 接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/health` | 健康状态和模块版本 |
| `GET` | `/v1/constants/trigrams` | 八卦常量 |
| `GET` | `/v1/constants/hexagrams` | 六十四卦常量 |
| `GET` | `/v1/rules` | 规则目录，可按`system`、`status`筛选 |
| `GET` | `/v1/validation-cases` | 工程案例，可按`system`筛选 |
| `POST` | `/v1/validation-cases/run` | 执行全部工程案例回归 |
| `POST` | `/v1/calendar/analyze` | 历法和四柱分析 |
| `POST` | `/v1/zhouyi/manual` | 手工六爻起卦 |
| `POST` | `/v1/zhouyi/numbers` | 周易双数起卦 |
| `POST` | `/v1/meihua/time` | 梅花时间起卦 |
| `POST` | `/v1/meihua/numbers` | 梅花双数起卦 |
| `POST` | `/v1/calculations/evaluate` | 统一单模块计算封装 |
| `POST` | `/v1/calculations/compare` | 最多8个模块并行计算和综合比较 |

OpenAPI文档位于`/docs`，机器契约位于`/openapi.json`。

### 3.1 历法示例

```bash
curl -X POST http://127.0.0.1:8090/v1/calendar/analyze \
  -H 'Content-Type: application/json' \
  -d '{"local_datetime":"2026-08-15T16:00:00","timezone":"Asia/Shanghai"}'
```

`local_datetime`不能自带偏移，必须另外提供IANA时区。启用真太阳时时同时提交`longitude`和`use_true_solar_time: true`。

### 3.2 多模块比较示例

```bash
curl -X POST http://127.0.0.1:8090/v1/calculations/compare \
  -H 'Content-Type: application/json' \
  -d '{
    "calculations": [
      {"module":"zhouyi","method":"numbers","input":{"lower_number":8,"upper_number":8}},
      {"module":"meihua","method":"time","input":{"local_datetime":"2026-08-15T16:00:00","timezone":"Asia/Shanghai"}}
    ]
  }'
```

相同计算集合不受字段顺序和模块顺序影响，返回相同`task_id`和`input_hash`。当前任务只在请求期间计算，尚未持久化。

### 3.3 推演结果与详细说明

多模块接口返回`explanation`：

```json
{
  "generation_method": "deterministic_fact_template",
  "review_status": "factual_only_pending_expert_rules",
  "summary": "本次完成历法、周易、梅花易数模块的确定性推演……",
  "modules": [
    {
      "module": "zhouyi",
      "title": "周易推演结果",
      "summary": "本卦、动爻和变卦摘要",
      "sections": [
        {"title": "本卦结构", "text": "……", "rule_ids": ["YI-MANUAL-001"]}
      ],
      "limitations": []
    }
  ],
  "conclusion": {
    "status": "factual_result_only",
    "text": "当前没有引用已发布解释规则的结构化判断……"
  },
  "limitations": []
}
```

说明由确定性模板直接读取本次盘面和步骤生成，不访问语料，不调用语言模型。每个说明段落保留规则编号。当前`review_status`表示只允许复述事实；在解释规则发布前，不能生成事项吉凶、应期和行动建议。

## 4. 综合分类规则

综合层只处理包含`dimension`、`time_range`、`polarity`和`rule_ids`的结构化`judgements`。所有规则编号必须存在且状态为`published`，否则判断进入`excluded`，不参与综合结果。

同一分析维度和完全相同的时间范围内：

- 多条相同倾向进入`consistent`。
- 同时包含`favorable`和`unfavorable`进入`conflicts`。
- 其他不同倾向进入`complementary`。
- 只有一条判断进入`unpaired`。
- 包含`indeterminate`进入`indeterminate`。

当前登记的12条规则均为`draft`工程基线，各模块也没有解释性`judgements`，因此正常综合结果是保留模块事实，并提示没有可比较的已发布判断。系统不会把五行关系事实擅自转换为吉凶。

## 5. 规则与案例

- 规则登记表：`data/rules/mvp-engineering-baseline.json`
- 工程案例集：`data/validation-cases/mvp-engineering-baseline.json`
- 批量执行器：`scripts/run_validation_cases.py`

执行案例：

```bash
./scripts/run_validation_cases.py
```

当前7个案例是代码回归基线，不是计划书要求的专家标准案例。案例文件使用`engineering_regression_pending_expert_review`标识，审核人为空。专家签署前不得将其状态改为已批准或对外声称为权威案例。

## 6. 验证

```bash
.venv/bin/python -m unittest discover -s backend/tests -v
.venv/bin/python -m compileall -q backend/app backend/tests
./scripts/run_validation_cases.py
```

提交前还应检查`git diff --check`。计算规则变更必须同步更新规则版本、案例预期和ADR；不得用新结果覆盖旧任务或旧报告。

# 风水功能模块

## 功能范围

当前版本完成风水功能的第一层基础能力：独立领域内的罗盘方位标准化、磁偏角修正、坐向换算、二十四山判定、测量误差传播和边界预警；数据层已有九宫基础数据及房屋、户型要素结构。

八宅、玄空飞星、三元九运和形势判断属于流派规则层。数据库已能通过 `rule_definitions.school` 和 `rule_version` 保存不同规则，但在获得专家审核案例前，不生成确定性吉凶结论。

## 输入数据

一次坐向计算至少需要：

- 向首角度：正北为0度，顺时针递增。
- 角度基准：磁北或真北。
- 磁偏角：输入为磁北角度时用于换算真北。
- 测量误差：由设备精度和多次测量结果确定。

房屋项目还可以记录经纬度、建造年份、入住日期、加密地址、户型图要素和测量方法。地址和户型属于敏感数据，应用写入前必须加密并按租户隔离。

## 命令行使用

```bash
./scripts/fengshui_direction.py 183.2 --declination -2.1
```

如输入已经相对真北测量：

```bash
./scripts/fengshui_direction.py 181.1 --reference true
```

输出示例中的核心字段：

```json
{
  "true_facing_degree": 181.1,
  "true_sitting_degree": 1.1,
  "facing": {"mountain": "午", "trigram": "离", "element": "火"},
  "sitting": {"mountain": "子", "trigram": "坎", "element": "水"},
  "boundary_warning": false,
  "rule_version": "fengshui-direction-1.0.0"
}
```

## 二十四山区间

每山占15度，山中心依次为0、15、30至345度。区间采用左闭右开，例如：

- 子山：`[352.5°, 360°)` 与 `[0°, 7.5°)`。
- 癸山：`[7.5°, 22.5°)`。
- 午山：`[172.5°, 187.5°)`。
- 壬山：`[337.5°, 352.5°)`。

向首与分界线距离不足1度，或正负测量误差覆盖多个山向时会产生边界警告。响应同时返回`candidate_mountains`和`classification_stable`。此时应要求用户在不同位置、不同时间复测，而不是直接采用某一山向。

## API使用

```bash
curl -X POST http://127.0.0.1:8090/v1/fengshui/direction \
  -H 'Content-Type: application/json' \
  -d '{"facing_degree":6,"input_reference":"magnetic","magnetic_declination":2,"measurement_error":1}'
```

统一计算接口使用`module: fengshui`和`method: direction`。响应遵守统一事实协议，`judgements`在本阶段固定为空数组。

多次测量使用三至十二个独立读数：

```bash
curl -X POST http://127.0.0.1:8090/v1/fengshui/measurements \
  -H 'Content-Type: application/json' \
  -d '{"measurements":[{"facing_degree":359,"input_reference":"true","measurement_error":0.5},{"facing_degree":0,"input_reference":"true","measurement_error":0.5},{"facing_degree":1,"input_reference":"true","measurement_error":0.5}]}'
```

多次测量采用圆周均值而非普通平均。结果状态为`consistent`、`boundary_sensitive`或`inconsistent`，并保留逐次真北修正和合并误差。

## ClickHouse 数据表

| 表 | 用途 |
| --- | --- |
| `fengshui_mountains` | 二十四山角度、八卦、五行和方位 |
| `luoshu_palaces` | 洛书九宫基础关系 |
| `fengshui_properties` | 房屋坐向、位置、时间与测量元数据 |
| `floorplan_features` | 门、窗、床、灶、卫生间等户型要素 |
| `fengshui_assessments` | 按流派和规则版本保存分析过程与结论 |
| `rule_definitions` | 保存八宅、玄空等不同流派规则 |
| `geo_features` | 保存道路、水体、建筑和地形要素 |

查询基础方位数据：

```sql
SELECT ordinal, name, center_degree, trigram, element, direction
FROM destiny.fengshui_mountains
ORDER BY ordinal;
```

## 后续功能顺序

1. 户型图坐标校准、中宫计算和九宫覆盖。
2. 门、主、灶、床、窗及卫生间标注和空间查询。
3. 八宅命卦与宅卦规则，按流派分别保存和测试（大游年通行传本已落地为 `draft` 端点 `/v1/fengshui/bazhai`）。
4. 三元九运及玄空运盘、山盘、向盘计算（下卦挨星已落地为 `draft` 端点 `/v1/fengshui/xuankong`；替卦起星盘按库内《沈氏玄空學》起星图 216 局实现为工程基线，经 `include_tihua_chart=true` 显式请求才提供、默认关闭；寅午庚丁替星已据两套原典口诀与 430 条可解析实例逆行计算裁定为弼星 9，中宫五按「无替可寻」不替、仍五入中；产物 `signed=false`，尚无专家签署）。
5. 道路、水体、高程和周边建筑的GIS辅助分析。
6. 专家复核、冲突规则展示及报告生成。

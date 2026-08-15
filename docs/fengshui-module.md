# 风水功能模块

## 功能范围

当前版本完成风水功能的第一层基础能力：罗盘方位标准化、磁偏角修正、坐向换算、二十四山判定、九宫基础数据，以及房屋和户型要素的数据结构。

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

向首与分界线距离不足1度时会产生边界警告。此时应结合测量误差要求用户在不同位置、不同时间复测，而不是直接采用某一山向。

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
3. 八宅命卦与宅卦规则，按流派分别保存和测试。
4. 三元九运及玄空运盘、山盘、向盘计算。
5. 道路、水体、高程和周边建筑的GIS辅助分析。
6. 专家复核、冲突规则展示及报告生成。

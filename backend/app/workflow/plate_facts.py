"""冻结快照的盘面事实视图。

快照的 raw_plate 若只记录调度信息，交互层（深度追问、换角度解读）读到的卦名、
动爻、体用卦会恒为空。本模块把各体系 facts 归一成一套稳定键，随快照一起冻结，
交互层只读这里，不再各自猜字段名。

同时提供 `compact_plate_output`：工作流结果里的 step2 只需要展示字段，
完整盘面已经整份存在快照的 module_results 里，不必再存一遍。
"""

from typing import Any, Dict, List, Optional

LINE_POSITION_NAMES = ("初", "二", "三", "四", "五", "上")
HEXAGRAM_KEYS = ("original", "changed", "mutual", "opposite", "reversed")
DISPLAY_HEXAGRAM_KEYS = ("original", "changed", "mutual")


def _hexagram_brief(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {"name": value if isinstance(value, str) else "", "ordinal": None, "symbol": ""}
    brief = {
        "ordinal": value.get("ordinal"),
        "name": value.get("name") or "",
        "symbol": value.get("symbol") or "",
    }
    # 阴阳爻线直接带上，前端就不必再按上/下卦名查一张本地八卦表反推——
    # 那是第二份映射，卦名读法一变就会画错爻。
    lines = value.get("lines")
    if isinstance(lines, (list, tuple)) and len(lines) == 6:
        brief["lines"] = [1 if bit else 0 for bit in lines]
    # 前端卦象图按上下卦名查八卦表再画爻线。引擎把上下卦存成 trigram 字典，
    # 只认字符串的读法会拿不到卦名，结果整卦默认画成坤（六条断线）。
    for key, source_key in (("upper", "upper_trigram"), ("lower", "lower_trigram")):
        raw = value.get(key)
        if isinstance(raw, str) and raw:
            brief[key] = raw
            continue
        trigram = value.get(source_key)
        if isinstance(trigram, dict) and trigram.get("name"):
            brief[key] = trigram["name"]
    return brief


def _trigram_brief(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {"number": None, "name": "", "element": ""}
    return {
        "number": value.get("number"),
        "name": value.get("name") or "",
        "element": value.get("element") or "",
    }


def _branch_name(value: Any) -> str:
    if isinstance(value, dict):
        return value.get("name") or value.get("branch") or ""
    return value if isinstance(value, str) else ""


def _line_records(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    lines = facts.get("line_chart") or []
    return [
        {
            "position": line.get("position"),
            "yin_yang": line.get("yin_yang"),
            "is_moving": bool(line.get("is_moving")),
            "element": line.get("element"),
            "six_relative": line.get("six_relative"),
            "six_spirit": line.get("six_spirit"),
            "najia_branch": line.get("najia_branch"),
            "roles": list(line.get("roles") or []),
        }
        for line in lines
        if isinstance(line, dict)
    ]


def _line_field(facts: Dict[str, Any], key: str) -> List[str]:
    """按爻位顺序（初→上）取某一爻字段的六个值。

    只有齐全的六爻才返回数组：缺一爻或读法变了就返回空列表，
    让前端明确走回退分支，而不是画出一份半真半假的盘。
    """
    values = [
        line.get(key)
        for line in facts.get("line_chart") or []
        if isinstance(line, dict) and line.get(key)
    ]
    return values if len(values) == 6 else []


def _moving_line_desc(original: Any, moving_line: Optional[int]) -> str:
    """动爻的爻题。卦象数据只存阴阳位，不含爻辞原文。

    爻题顺序是「极性 + 爻位」（九二、六三），且首末两爻用「初/上」：
    九三 而不是「三九」。此前把位置名放在前面，输出「三九」是错的。
    """
    if not moving_line or not isinstance(original, dict):
        return ""
    bits = original.get("lines") or []
    index = moving_line - 1
    if index < 0 or index >= len(bits) or index >= len(LINE_POSITION_NAMES):
        return ""
    polarity = "九" if bits[index] == 1 else "六"
    if index == 0:
        title = "初" + polarity
    elif index == 5:
        title = "上" + polarity
    else:
        title = polarity + LINE_POSITION_NAMES[index]
    return "{}（第{}爻）".format(title, moving_line)


def _changed_line_desc(original: Any, changed: Any, moving_line: Optional[int]) -> str:
    """变爻描述：动爻由阴变阳（或由阳变阴）后的那一爻。"""
    if not moving_line or not isinstance(original, dict):
        return ""
    before = original.get("lines") or []
    after = (changed or {}).get("lines") or [] if isinstance(changed, dict) else []
    index = moving_line - 1
    if index < 0 or index >= len(before):
        return ""
    if index >= len(after):
        return "第{}爻变".format(moving_line)
    return "第{}爻由{}变{}".format(
        moving_line,
        "阳" if before[index] == 1 else "阴",
        "阳" if after[index] == 1 else "阴",
    )


def build_plate_facts(module_results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """把各体系计算结果里的 facts 归一为盘面事实。"""
    facts_by_system: Dict[str, Dict[str, Any]] = {}
    for item in module_results or []:
        module = item.get("module")
        if not module:
            continue
        facts = ((item.get("result") or {}).get("facts")) or {}
        if not isinstance(facts, dict) or not facts:
            continue

        original = facts.get("original")
        moving_lines = [int(line) for line in facts.get("moving_lines") or [] if isinstance(line, int)]
        moving_line = facts.get("moving_line")
        if moving_line is None and len(moving_lines) == 1:
            moving_line = moving_lines[0]
        body_use = facts.get("body_use") or {}
        entry: Dict[str, Any] = {
            "module": module,
            "moving_line": moving_line,
            "moving_line_text": _moving_line_desc(original, moving_line),
            # 变爻＝动爻变化后的那一爻（阴阳翻转），与变卦名分开存
            "bian_yao": _changed_line_desc(original, facts.get("changed"), moving_line),
            "moving_lines": moving_lines,
            "moving_branches": [
                line.get("najia_branch")
                for line in facts.get("line_chart") or []
                if isinstance(line, dict) and line.get("is_moving") and line.get("najia_branch")
            ],
            "line_chart": _line_records(facts),
            # 六神/六亲此前只存在于引擎的 steps 里，盘面事实没往上收一层，
            # 于是 compact 输出里那两个键永远是空的：前端只能按「青龙起」的
            # 固定默认顺序画，跟真实日干起出来的六神无关。这里按爻位顺序
            # （初→上）收成两个数组，和 line_chart 同序。
            "six_spirits": _line_field(facts, "six_spirit"),
            "liuqin": _line_field(facts, "six_relative"),
            "palace": facts.get("palace") if isinstance(facts.get("palace"), dict) else None,
            "body_use": body_use if isinstance(body_use, dict) else None,
            "body_use_relation": facts.get("body_use_relation")
            if isinstance(facts.get("body_use_relation"), dict)
            else None,
            "month_branch": _branch_name(facts.get("month_branch")),
            "day_branch": _branch_name(facts.get("day_branch")),
            "day_pillar": facts.get("day_pillar") if isinstance(facts.get("day_pillar"), str) else "",
            "four_lessons": facts.get("four_lessons"),
            "three_transmissions": facts.get("three_transmissions"),
        }
        for key in HEXAGRAM_KEYS:
            entry[key] = _hexagram_brief(facts.get(key))
        if isinstance(body_use, dict):
            entry["ti_gua"] = _trigram_brief(body_use.get("body_trigram"))
            entry["yong_gua"] = _trigram_brief(body_use.get("use_trigram"))
        else:
            entry["ti_gua"] = _trigram_brief(None)
            entry["yong_gua"] = _trigram_brief(None)
        facts_by_system[module] = entry
    return facts_by_system


def build_plate_view(snapshot: Any) -> Dict[str, Any]:
    """交互层统一读取入口：优先用冻结的盘面事实，兼容旧快照顶层键。"""
    raw = getattr(snapshot, "raw_plate", None) or {}
    facts_by_system = raw.get("plate_facts") or {}
    view: Dict[str, Any] = {
        "scheduling_note": raw.get("scheduling_note"),
        "systems_used": raw.get("systems_used") or [],
        "calculation_requests": raw.get("calculation_requests") or [],
        "facts_by_system": facts_by_system,
        "ben_gua": "",
        "bian_gua": "",
        "hu_gua": "",
        "ti_gua": "",
        "yong_gua": "",
        "moving_line": None,
        "bian_yao": "",
        "yao_ci": "",
    }

    primary = None
    for module in ("liuyao", "meihua", "zhouyi", "liuren"):
        facts = facts_by_system.get(module)
        if facts and facts["original"]["name"]:
            primary = facts
            break
    # 体卦/用卦只有梅花体系有，单独取，避免主体系是六爻时恒空
    body_use_source = None
    for module in ("meihua", "zhouyi"):
        facts = facts_by_system.get(module)
        if facts and facts["ti_gua"]["name"]:
            body_use_source = facts
            break
    if primary:
        view.update({
            "system": primary["module"],
            "ben_gua": primary["original"]["name"],
            "bian_gua": primary["changed"]["name"],
            "hu_gua": primary["mutual"]["name"],
            "moving_line": primary.get("moving_line"),
            # bian_yao 是「变化后的那一爻」的描述，不是变卦名；变卦名在 bian_gua
            "bian_yao": primary.get("bian_yao") or primary["changed"]["name"],
            "yao_ci": primary.get("moving_line_text") or "",
            "moving_branches": primary.get("moving_branches") or [],
            "palace": primary.get("palace"),
        })
    if body_use_source:
        view.update({
            "ti_gua": body_use_source["ti_gua"]["name"],
            "yong_gua": body_use_source["yong_gua"]["name"],
            "tiyong_relation": (body_use_source.get("body_use_relation") or {}).get("original"),
        })

    # 旧快照：raw_plate 顶层已有这些键时以其为准，避免历史会话失效
    for legacy in ("ben_gua", "bian_gua", "hu_gua", "ti_gua", "yong_gua", "moving_line", "bian_yao", "yao_ci"):
        value = raw.get(legacy)
        if value not in (None, "", [], {}):
            view[legacy] = value
    return view


def _solar_term_display(value: Any) -> Dict[str, str]:
    """节气字段是 {previous/current/next/...} 结构，展示层要名字 + 相对关系。

    不在节气当天时 `current` 为 null，这时退回最近的下一/上一节气，
    并标注关系，避免把「立冬」当成当前节气展示。
    """
    if isinstance(value, str):
        return {"name": value, "note": ""}
    if not isinstance(value, dict):
        return {"name": "", "note": ""}
    for key, note in (("current", "当前节气"), ("next", "下一节气"), ("previous", "上一节气")):
        item = value.get(key)
        name = item.get("name") if isinstance(item, dict) else item
        if name:
            return {"name": str(name), "note": note}
    for key in ("name", "text"):
        if value.get(key):
            return {"name": str(value[key]), "note": ""}
    return {"name": "", "note": ""}


def _calendar_display(calendar: Any) -> Optional[Dict[str, Any]]:
    """历法基线只保留展示需要的字段，并把干支压成可直接渲染的字符串。"""
    if not isinstance(calendar, dict) or not calendar:
        return None
    pillars = calendar.get("pillars") if isinstance(calendar.get("pillars"), dict) else {}
    ganzhi = calendar.get("ganzhi") if isinstance(calendar.get("ganzhi"), dict) else {}
    display_ganzhi = {}
    for key in ("year", "month", "day", "hour"):
        item = ganzhi.get(key)
        if isinstance(item, dict):
            display_ganzhi[key] = item.get("text") or "{}{}".format(item.get("stem") or "", item.get("branch") or "")
        elif isinstance(item, str):
            display_ganzhi[key] = item
    lunar = calendar.get("lunar") if isinstance(calendar.get("lunar"), dict) else {}
    solar_term = _solar_term_display(calendar.get("solar_term"))
    return {
        "pillars": {key: str(value) for key, value in pillars.items() if value},
        "ganzhi": display_ganzhi,
        "solar_term": solar_term["name"],
        "solar_term_note": solar_term["note"],
        "lunar": {
            key: lunar.get(key)
            for key in ("year", "month_name", "day_name")
            if lunar.get(key) is not None
        },
    }


def _dig(value: Any, *path: str) -> Any:
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def domain_summary(module: str, facts: Dict[str, Any]) -> Dict[str, str]:
    """非卦象体系（八字/紫微/奇门/六壬）的展示摘要。

    它们的盘面不在 original/line_chart 里，compact 只搬卦象字段时 step2 会整段空白，
    用户选了八字却看不到四柱。这里按展示需要抽出少量标量，完整盘面仍在快照里。
    """
    summary: Dict[str, str] = {}

    def add(label: str, value: Any) -> None:
        if value in (None, "", [], {}):
            return
        summary[label] = value if isinstance(value, str) else str(value)

    if module == "bazi":
        pillars = facts.get("pillars") or {}
        four = " ".join(
            str((pillars.get(key) or {}).get("ganzhi") or "")
            for key in ("year", "month", "day", "hour")
        ).strip()
        day_master = facts.get("day_master") or ""
        element = facts.get("day_master_element") or ""
        add("日主", "{}（{}）".format(day_master, element) if element else day_master)
        add("四柱", four)
        add("日主旺衰", _dig(facts, "day_master_strength", "level"))
        luck = facts.get("luck_pillars") or []
        add("大运", "{} 步".format(len(luck)) if luck else "")
    elif module == "ziwei":
        add("五行局", _dig(facts, "bureau", "name"))
        add("命宫", _dig(facts, "ming_palace", "palace_stem_branch") or _dig(facts, "ming_palace", "earthly_branch"))
        add("身宫", _dig(facts, "shen_palace", "palace_stem_branch")
            or _dig(facts, "shen_palace", "earthly_branch")
            or (facts.get("shen_palace") if isinstance(facts.get("shen_palace"), str) else ""))
        si_hua = facts.get("si_hua") or {}
        add("四化", " · ".join("{} {}".format(key, value) for key, value in si_hua.items()))
        palaces = facts.get("palaces_by_order") or []
        add("宫位", "{} 宫".format(len(palaces)) if palaces else "")
    elif module == "qimen":
        dun = facts.get("dun_type") or ""
        ju = facts.get("ju_number")
        add("局象", "{}{}局·{}".format(dun, ju, facts.get("yuan_type") or "").rstrip("·"))
        add("节气", facts.get("solar_term"))
        add("值符", "{} 落 {} 宫".format(facts.get("zhi_fu_star") or "", facts.get("zhi_fu_palace") or "").strip())
        add("值使", "{} 落 {} 宫".format(facts.get("zhi_shi_gate") or "", facts.get("zhi_shi_palace") or "").strip())
        favorable = facts.get("favorable_directions") or []
        if favorable:
            top = favorable[0]
            add("首选吉方", "{}方 · {} · {}".format(top.get("direction") or "", top.get("gate") or "", top.get("palace_name") or ""))
    elif module in ("daliuren", "liuren"):
        add("占日", facts.get("day_pillar"))
        add("占时", facts.get("actual_time_branch") or _dig(facts, "occupation_time", "branch"))
        add("月将", _dig(facts, "month_general", "name"))
        transmissions = (_dig(facts, "three_transmissions", "transmissions") or [])
        add("三传", " → ".join(str(item) for item in transmissions))
        add("课体", _dig(facts, "three_transmissions", "lesson_type"))
    return summary


def compact_plate_output(step2: Dict[str, Any]) -> Dict[str, Any]:
    """把 step2 压成「展示用」结构。

    完整盘面（line_chart、计算轨迹、steps、almanac 等）已经整份存在快照的
    module_results 里，会话文件里再存一份纯属体积翻倍。
    交互层要问盘面事实走 build_plate_view，不依赖这里。
    """
    plates = {}
    for module, plate in (step2.get("plates") or {}).items():
        if not isinstance(plate, dict):
            continue
        facts = plate.get("facts") if isinstance(plate.get("facts"), dict) else {}
        display_facts: Dict[str, Any] = {}
        for key in DISPLAY_HEXAGRAM_KEYS:
            if facts.get(key):
                display_facts[key] = _hexagram_brief(facts.get(key))
        for key in ("moving_line", "moving_lines"):
            if facts.get(key):
                display_facts[key] = facts[key]
        # 六神/六亲：引擎只把它们放在逐爻 line_chart 与 steps 里，
        # facts 顶层没有这两个键。不在这里补出来，前端就只能画固定默认序列。
        for display_key, line_key in (("six_spirits", "six_spirit"), ("liuqin", "six_relative")):
            values = facts.get(display_key) or _line_field(facts, line_key)
            if values:
                display_facts[display_key] = values
        body_use = facts.get("body_use")
        if isinstance(body_use, dict):
            display_facts["body_use"] = {
                "body_trigram": _trigram_brief(body_use.get("body_trigram")),
                "use_trigram": _trigram_brief(body_use.get("use_trigram")),
            }
        # 体用生克是 step4 判定「体用关系」的唯一真源；compact 丢掉它会让
        # tiyong_relation 永远是 None，吉凶评分里也少了这一项。
        if isinstance(facts.get("body_use_relation"), dict):
            display_facts["body_use_relation"] = facts["body_use_relation"]
        plates[module] = {
            "system_label": plate.get("system_label") or module,
            "facts": display_facts,
            "summary": domain_summary(module, facts),
            "warnings": plate.get("warnings") or [],
            "engine_version": plate.get("engine_version") or "",
            "rule_version": plate.get("rule_version") or "",
        }
    return {
        "step": step2.get("step", 2),
        "name": step2.get("name") or "完整排盘输出",
        "systems": step2.get("systems") or [],
        "plates": plates,
        "calendar": _calendar_display(step2.get("calendar")),
        "plate_facts_dropped": True,
    }

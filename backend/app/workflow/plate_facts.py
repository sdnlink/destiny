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
        for key in ("moving_line", "moving_lines", "six_spirits", "liuqin"):
            if facts.get(key):
                display_facts[key] = facts[key]
        body_use = facts.get("body_use")
        if isinstance(body_use, dict):
            display_facts["body_use"] = {
                "body_trigram": _trigram_brief(body_use.get("body_trigram")),
                "use_trigram": _trigram_brief(body_use.get("use_trigram")),
            }
        plates[module] = {
            "system_label": plate.get("system_label") or module,
            "facts": display_facts,
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

import json
import logging
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, conint, conlist, constr, validator

from app.common.classics import get_library as get_classics_library
from app.common.hashing import canonical_hash
from app.core.advisory import CATEGORY_PROFILES, generate_advisory
from app.calendar import calendar_analysis
from app.core.constants import HEXAGRAM_NAMES, KING_WEN_MATRIX, TRIGRAMS
from app.core.explanation import explain_calculation_set
from app.zhouyi import auto_cast as yi_auto_cast
from app.zhouyi import manual_cast as yi_manual_cast
from app.zhouyi import number_cast as yi_number_cast
from app.zhouyi import three_number_cast as yi_three_number_cast
from app.zhouyi import time_cast as yi_time_cast
from app.core.interpretation import explain_correspondences
from app.core.literature import collect_literature_opinions
from app.core.imagery import collect_imagery
from app.daliuren import auto_cast as liuren_auto_cast
from app.daliuren import number_cast as liuren_number_cast
from app.daliuren import time_cast as liuren_time_cast
from app.fengshui import analyze_measurements as fengshui_measurements
from app.fengshui import calculate_direction as fengshui_direction
from app.fengshui.bazhai import calculate_bazhai
from app.fengshui.storage import (
    delete_profile, get_profile, list_profiles, upsert_profile,
)
from app.fengshui.xuankong import calculate_xuankong
from app.liuyao import auto_cast as liuyao_auto_cast
from app.liuyao import number_cast as liuyao_number_cast
from app.liuyao import coin_cast as liuyao_coin_cast
from app.liuyao import line_cast as liuyao_line_cast
from app.liuyao import time_cast as liuyao_time_cast
from app.meihua import auto_cast as meihua_auto_cast
from app.meihua import number_cast as meihua_number_cast
from app.meihua import three_number_cast as meihua_three_number_cast
from app.meihua import time_cast as meihua_time_cast
from app.ziwei import time_cast as ziwei_time_cast, auto_cast as ziwei_auto_cast
from app.bazi import time_cast as bazi_time_cast, auto_cast as bazi_auto_cast, liunian_cast as bazi_liunian_cast
from app.qimen import time_cast as qimen_time_cast, auto_cast as qimen_auto_cast
from app.core.db import db_repository
from app.core.registry import load_rule_registry, load_validation_cases
from app.core.synthesis import synthesize
from app.core.validation import run_validation_cases
from app.core.yuanhui import analyze_yuan_hui_yun_shi
from app.session import create_session, get_store
from app.workflow import run_workflow
from app.interaction import (
    analyze_branches,
    analyze_multi_party,
    angle_shift,
    apply_completion_answers,
    deep_question,
    generate_completion_prompt,
    process_reality_response,
    review_outcome,
)


APP_VERSION = "0.2.0"
API_TOKEN = os.environ.get("APP_API_TOKEN")

logger = logging.getLogger("destiny.api")
if not API_TOKEN:
    logger.warning(
        "APP_API_TOKEN 未设置：/v1 接口当前不做鉴权，仅应在本地开发环境使用"
    )


class CalendarRequest(BaseModel):
    local_datetime: str = Field(..., example="2026-08-15T16:00:00")
    timezone: str = Field(..., example="Asia/Shanghai")
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    use_true_solar_time: bool = False


class AutoCastRequest(CalendarRequest):
    cast_nonce: constr(
        strip_whitespace=True, min_length=16, max_length=128,
        regex=r"^[A-Za-z0-9_-]+$",
    )


class YiManualRequest(BaseModel):
    lines: conlist(conint(ge=6, le=9), min_items=6, max_items=6)


class YiNumberRequest(BaseModel):
    lower_number: int
    upper_number: int


class YiThreeNumberRequest(BaseModel):
    numbers: conlist(conint(strict=True, ge=0), min_items=3, max_items=3)
    mapping_version: constr(strip_whitespace=True, min_length=1, max_length=80) = "earlier-heaven-number-v1"


class MeihuaNumberRequest(BaseModel):
    upper_number: int
    lower_number: int


class MeihuaThreeNumberRequest(BaseModel):
    numbers: conlist(conint(strict=True), min_items=3, max_items=3)


class LiuyaoCalendarRequest(CalendarRequest):
    focus: Optional[str] = Field(None, example="求财买卖")


class LiuyaoAutoRequest(AutoCastRequest):
    focus: Optional[str] = Field(None, example="求财买卖")


class LiuyaoNumberRequest(LiuyaoCalendarRequest):
    lower_number: int
    upper_number: int


class LiuyaoLineRequest(LiuyaoCalendarRequest):
    lines: conlist(conint(strict=True, ge=6, le=9), min_items=6, max_items=6)


CoinRound = conlist(conint(strict=True, ge=2, le=3), min_items=3, max_items=3)


class LiuyaoCoinRequest(LiuyaoCalendarRequest):
    coins: conlist(CoinRound, min_items=6, max_items=6)


class LiurenNumberRequest(CalendarRequest):
    number: conint(strict=True)


class ZiweiRequest(CalendarRequest):
    gender: str = Field("男", example="男")


class ZiweiAutoRequest(AutoCastRequest):
    gender: str = Field("男", example="男")


class BaZiRequest(CalendarRequest):
    gender: str = Field("男", example="男")


class BaZiAutoRequest(AutoCastRequest):
    gender: str = Field("男", example="男")


class BaZiLiunianRequest(CalendarRequest):
    gender: str = Field("男", example="男")
    start_year: Optional[int] = Field(None, ge=1900, le=2100, description="起始公历年，默认起运年")
    count: int = Field(10, ge=1, le=60, description="流年条数（1-60）")


class FengshuiDirectionRequest(BaseModel):
    facing_degree: float
    input_reference: str = "magnetic"
    magnetic_declination: float = 0.0
    measurement_error: float = Field(0.0, ge=0, le=180)
    declination_source: Optional[constr(strip_whitespace=True, min_length=1, max_length=200)] = None
    measurement_method: Optional[constr(strip_whitespace=True, min_length=1, max_length=100)] = None

    @validator("facing_degree", "magnetic_declination", "measurement_error", pre=True)
    def numeric_fields_are_strict_and_finite(cls, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("must be a finite number")
        return value

    @validator("input_reference")
    def reference_is_supported(cls, value):
        if value not in ("magnetic", "true"):
            raise ValueError("must be magnetic or true")
        return value


class FengshuiMeasurementsRequest(BaseModel):
    measurements: conlist(FengshuiDirectionRequest, min_items=3, max_items=12)


class CalculationRequest(BaseModel):
    module: str
    method: str
    input: Dict[str, Any]


class AdvisoryContext(BaseModel):
    category: str
    question_summary: constr(strip_whitespace=True, min_length=1, max_length=200)

    @validator("category")
    def category_is_supported(cls, value):
        if value not in CATEGORY_PROFILES:
            raise ValueError("unsupported category")
        return value


class ComparisonRequest(BaseModel):
    calculations: conlist(CalculationRequest, min_items=1, max_items=8)
    context: Optional[AdvisoryContext] = None


def _calendar_payload(values):
    return calendar_analysis(**values)


def _liuyao_numbers_call(values):
    request_values = dict(values)
    lower_number = request_values.pop("lower_number")
    upper_number = request_values.pop("upper_number")
    return liuyao_number_cast(lower_number, upper_number, **request_values)


def _liuyao_lines_call(values):
    request_values = dict(values)
    lines = request_values.pop("lines")
    return liuyao_line_cast(lines, **request_values)


def _liuyao_coins_call(values):
    request_values = dict(values)
    coins = request_values.pop("coins")
    return liuyao_coin_cast(coins, **request_values)


def _liuren_numbers_call(values):
    request_values = dict(values)
    number = request_values.pop("number")
    return liuren_number_cast(number, **request_values)


# module/method → (入参校验模型, 引擎调用)。/v1/calculations 与 /v1/comparisons 共用这一张表，
# 不再用长 if 链，新增体系只加一条。
CALCULATION_ENTRIES = {
    ("calendar", "analyze"): (CalendarRequest, _calendar_payload),
    ("zhouyi", "manual"): (YiManualRequest, lambda values: yi_manual_cast(values["lines"])),
    ("zhouyi", "auto"): (AutoCastRequest, lambda values: yi_auto_cast(**values)),
    ("zhouyi", "time"): (CalendarRequest, lambda values: yi_time_cast(**values)),
    ("zhouyi", "numbers"): (YiNumberRequest, lambda values: yi_number_cast(values["lower_number"], values["upper_number"])),
    ("zhouyi", "three_numbers"): (
        YiThreeNumberRequest,
        lambda values: yi_three_number_cast(*values["numbers"], mapping_version=values["mapping_version"]),
    ),
    ("meihua", "time"): (CalendarRequest, lambda values: meihua_time_cast(**values)),
    ("meihua", "auto"): (AutoCastRequest, lambda values: meihua_auto_cast(**values)),
    ("meihua", "numbers"): (MeihuaNumberRequest, lambda values: meihua_number_cast(values["upper_number"], values["lower_number"])),
    ("meihua", "three_numbers"): (MeihuaThreeNumberRequest, lambda values: meihua_three_number_cast(*values["numbers"])),
    ("liuyao", "time"): (CalendarRequest, lambda values: liuyao_time_cast(**values)),
    ("liuyao", "auto"): (AutoCastRequest, lambda values: liuyao_auto_cast(**values)),
    ("liuyao", "numbers"): (LiuyaoNumberRequest, _liuyao_numbers_call),
    ("liuyao", "lines"): (LiuyaoLineRequest, _liuyao_lines_call),
    ("liuyao", "coins"): (LiuyaoCoinRequest, _liuyao_coins_call),
    ("liuren", "time"): (CalendarRequest, lambda values: liuren_time_cast(**values)),
    ("liuren", "auto"): (AutoCastRequest, lambda values: liuren_auto_cast(**values)),
    ("liuren", "numbers"): (LiurenNumberRequest, _liuren_numbers_call),
    ("ziwei", "time"): (ZiweiRequest, lambda values: ziwei_time_cast(**values)),
    ("ziwei", "auto"): (ZiweiAutoRequest, lambda values: ziwei_auto_cast(**values)),
    ("bazi", "time"): (BaZiRequest, lambda values: bazi_time_cast(**values)),
    ("bazi", "auto"): (BaZiAutoRequest, lambda values: bazi_auto_cast(**values)),
    ("qimen", "time"): (CalendarRequest, lambda values: qimen_time_cast(**values)),
    ("qimen", "auto"): (AutoCastRequest, lambda values: qimen_auto_cast(**values)),
    ("fengshui", "direction"): (FengshuiDirectionRequest, lambda values: fengshui_direction(**values)),
    ("fengshui", "measurements"): (
        FengshuiMeasurementsRequest,
        lambda values: fengshui_measurements(values["measurements"]),
    ),
}


def execute(module, method, payload):
    """校验入参后调用对应引擎。未知组合直接报错。"""
    entry = CALCULATION_ENTRIES.get((module, method))
    if entry is None:
        raise ValueError(f"unsupported calculation: {module}/{method}")
    model, call = entry
    values = model(**payload).dict()
    return call(values)


def calculation_envelope(module, method, payload):
    normalized = {"module": module, "method": method, "input": payload}
    input_hash = canonical_hash(normalized)
    result = execute(module, method, payload)
    return {
        "task_id": f"calc_{input_hash[:24]}",
        "status": "completed",
        "module": module,
        "method": method,
        "input_hash": f"sha256:{input_hash}",
        "result": result,
        "calculated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def comparison_envelope(calculations, context=None):
    normalized = [
        calculation.dict() if isinstance(calculation, CalculationRequest) else calculation
        for calculation in calculations
    ]
    normalized = sorted(
        normalized,
        key=lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    )
    normalized_context = context.dict() if isinstance(context, AdvisoryContext) else context
    input_hash = canonical_hash({"calculations": normalized, "context": normalized_context})
    # 各引擎都是纯 CPU 计算，串行执行；线程池在 GIL 下没有收益，还会放大共享缓存并发写风险
    results = [execute(item["module"], item["method"], item["input"]) for item in normalized]
    module_results = [
        {
            "module": item["module"],
            "method": item["method"],
            "input_hash": "sha256:" + canonical_hash(item["input"]),
            "result": result,
        }
        for item, result in zip(normalized, results)
    ]
    comparison = synthesize(results)
    imagery = collect_imagery(module_results, normalized_context)
    yuan_hui = analyze_yuan_hui_yun_shi(module_results)
    interp_result = explain_correspondences(module_results, normalized_context, imagery, yuan_hui)
    return {
        "task_id": "compare_{}".format(input_hash[:24]),
        "status": "completed",
        "input_hash": "sha256:" + input_hash,
        "module_results": module_results,
        "comparison": comparison,
        "explanation": explain_calculation_set(module_results, comparison),
        "advisory": generate_advisory(module_results, normalized_context),
        "literature": collect_literature_opinions(module_results, context=normalized_context),
        "imagery": imagery,
        "yuan_hui_yun_shi": yuan_hui,
        "interpretation": interp_result,
        "targeted_deduction": interp_result.get("targeted_findings") if interp_result else None,
        "calculated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


app = FastAPI(
    title="天机演象MVP计算API",
    version=APP_VERSION,
    description="确定性历法、周易、梅花易数、六爻、大六壬和阳宅方位事实计算。解释规则尚待专家签署。",
)


@app.middleware("http")
async def internal_token_middleware(request: Request, call_next):
    if API_TOKEN:
        path = request.url.path
        # SERVE_WEB=1 时根路径挂载的是浏览器静态资源，无法携带 Bearer 头；
        # 鉴权只覆盖计算/会话 API 与接口文档，静态页面和 /health 探活保持公开。
        protected = (
            path.startswith("/v1")
            or path == "/docs"
            or path.startswith("/docs/")
            or path == "/openapi.json"
            or path == "/redoc"
        )
        if protected and request.headers.get("Authorization") != f"Bearer {API_TOKEN}":
            return JSONResponse(status_code=401, content={"error": {"code": "UNAUTHORIZED", "message": "valid bearer token required"}})
    return await call_next(request)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=422, content={"error": {"code": "INVALID_CALCULATION_INPUT", "message": str(exc)}})


def constant_payload(rows, fallback=None):
    """常量端点统一返回。

    只有数据库真的连上时才声明 clickhouse 来源；连不上时明确标注 unavailable，
    不再用「数据库来源 + 空数组」把不可达伪装成「表里就是空的」。
    """
    if db_repository.is_available():
        return {"data": rows or [], "source": "clickhouse_database"}
    if fallback:
        return {"data": fallback, "source": "in_memory_fallback"}
    return {
        "data": [],
        "source": "unavailable",
        "warning": "数据库不可达，常量表未加载",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "tianji-mvp-calculation",
        "version": APP_VERSION,
        "modules": [
            "calendar",
            "zhouyi",
            "meihua",
            "liuyao",
            "liuren",
            "ziwei",
            "bazi",
            "qimen",
            "fengshui",
        ],
    }


@app.get("/v1/constants/trigrams")
def trigrams():
    db_rows = db_repository.get_trigrams()
    if db_rows:
        return {"data": db_rows, "source": "clickhouse_database"}
    return {
        "data": [{"number": number, **value} for number, value in TRIGRAMS.items()],
        "source": "in_memory_fallback",
    }


@app.get("/v1/constants/trigram-imagery")
def trigram_imagery(trigram: Optional[str] = None, dimension: Optional[str] = None):
    db_rows = db_repository.get_trigram_imagery(trigram, dimension)
    return constant_payload(db_rows)


@app.get("/v1/constants/hexagrams")
def hexagrams():
    db_rows = db_repository.get_hexagrams()
    if db_rows:
        return {"data": db_rows, "source": "clickhouse_database"}
    rows = []
    seen = set()
    for upper_index, matrix_row in enumerate(KING_WEN_MATRIX, 1):
        for lower_index, ordinal in enumerate(matrix_row, 1):
            if ordinal in seen:
                continue
            seen.add(ordinal)
            rows.append({
                "ordinal": ordinal,
                "name": HEXAGRAM_NAMES[ordinal - 1],
                "symbol": chr(0x4DBF + ordinal),
                "upper_trigram_number": upper_index,
                "lower_trigram_number": lower_index,
            })
    return {"data": sorted(rows, key=lambda row: row["ordinal"]), "source": "in_memory_fallback"}


@app.get("/v1/constants/hexagram-explanations")
def hexagram_explanations(name: Optional[str] = None):
    db_rows = db_repository.get_hexagram_explanations(name)
    if db_rows:
        return {"data": db_rows, "source": "clickhouse_database"}
    from app.core.hexagram_service import get_hexagram_explanation, _load_all
    if name:
        res = get_hexagram_explanation(name)
        return {"data": [res] if res else [], "source": "file_cache"}
    all_data = _load_all()
    unique_rows = sorted({v["ordinal"]: v for v in all_data.values()}.values(), key=lambda x: x["ordinal"])
    return {"data": unique_rows, "source": "file_cache"}


@app.get("/v1/constants/five-elements")
def five_elements():
    db_rows = db_repository.get_five_elements()
    return constant_payload(db_rows)


@app.get("/v1/constants/stems")
def heavenly_stems():
    db_rows = db_repository.get_heavenly_stems()
    return constant_payload(db_rows)


@app.get("/v1/constants/branches")
def earthly_branches():
    db_rows = db_repository.get_earthly_branches()
    return constant_payload(db_rows)


@app.get("/v1/constants/solar-terms")
def solar_terms():
    db_rows = db_repository.get_solar_terms()
    return constant_payload(db_rows)


@app.get("/v1/constants/sexagenary-cycle")
def sexagenary_cycle():
    db_rows = db_repository.get_sexagenary_cycle()
    return constant_payload(db_rows)


@app.get("/v1/constants/fengshui-mountains")
def fengshui_mountains():
    db_rows = db_repository.get_fengshui_mountains()
    return constant_payload(db_rows)


@app.get("/v1/constants/luoshu-palaces")
def luoshu_palaces():
    db_rows = db_repository.get_luoshu_palaces()
    return constant_payload(db_rows)


@app.get("/v1/constants/twenty-eight-mansions")
def twenty_eight_mansions(quadrant: Optional[str] = None):
    db_rows = db_repository.get_twenty_eight_mansions(quadrant=quadrant)
    return constant_payload(db_rows)


@app.get("/v1/constants/three-enclosures")
def three_enclosures():
    db_rows = db_repository.get_three_enclosures()
    return constant_payload(db_rows)


@app.get("/v1/constants/historical-calendars")
def historical_calendars(dynasty: Optional[str] = None):
    db_rows = db_repository.get_historical_calendars(dynasty=dynasty)
    return constant_payload(db_rows)


@app.get("/v1/constants/hetu-numerology")
def hetu_numerology(element: Optional[str] = None):
    db_rows = db_repository.get_hetu_numerology(element=element)
    return constant_payload(db_rows)


@app.get("/v1/constants/lunar-phases")
def lunar_phases():
    db_rows = db_repository.get_lunar_phase_regimes()
    return constant_payload(db_rows)


@app.get("/v1/database/stats")
def database_stats():
    rows = db_repository.get_database_stats()
    available = db_repository.is_available()
    return {
        "status": "connected" if available else "disconnected",
        "tables": rows or [],
        "source": "clickhouse",
    }


@app.get("/v1/rules")
def rules(system: Optional[str] = None, status: Optional[str] = None):
    registry = load_rule_registry()
    rows = registry["rules"]
    if system:
        rows = [rule for rule in rows if rule["system"] == system]
    if status:
        rows = [rule for rule in rows if rule["status"] == status]
    return {
        "data": rows,
        "meta": {
            "registry_id": registry["registry_id"],
            "qualification": registry["qualification"],
            "checksum": registry["checksum"],
            "count": len(rows),
        },
    }


@app.get("/v1/classics/status")
def classics_status():
    """本地典籍库状态：收录书目、字符量与待补来源清单。"""
    library = get_classics_library()
    if not library.available:
        return {"data": {"available": False, "corpus_dir": str(library.corpus_dir)}}
    status = library.status()
    status["available"] = True
    return {"data": status}


@app.get("/v1/classics/search")
def classics_search(
    q: str,
    category: Optional[str] = None,
    title: Optional[str] = None,
    limit: int = 5,
):
    """按关键词检索本地典籍原文段落，作为结论依据。"""
    limit = max(1, min(limit, 20))
    library = get_classics_library()
    if not library.available:
        return {"data": [], "meta": {"available": False}}
    return {
        "data": library.search(q, category=category, title_query=title, limit=limit),
        "meta": {"available": True, "query": q},
    }


@app.get("/v1/validation-cases")
def validation_cases(system: Optional[str] = None):
    document = load_validation_cases()
    rows = document["cases"]
    if system:
        rows = [case for case in rows if case["system"] == system]
    return {
        "data": rows,
        "meta": {
            "case_set_id": document["case_set_id"],
            "qualification": document["qualification"],
            "checksum": document["checksum"],
            "count": len(rows),
        },
    }


@app.post("/v1/validation-cases/run")
def run_cases():
    return {"data": run_validation_cases()}


@app.post("/v1/calendar/analyze")
def analyze_calendar(request: CalendarRequest):
    return {"data": calendar_analysis(**request.dict())}


@app.post("/v1/zhouyi/manual")
def cast_yi_manual(request: YiManualRequest):
    return {"data": yi_manual_cast(request.lines)}


@app.post("/v1/zhouyi/auto")
def cast_yi_auto(request: AutoCastRequest):
    return {"data": yi_auto_cast(**request.dict())}


@app.post("/v1/zhouyi/time")
def cast_yi_time(request: CalendarRequest):
    return {"data": yi_time_cast(**request.dict())}


@app.post("/v1/zhouyi/numbers")
def cast_yi_numbers(request: YiNumberRequest):
    return {"data": yi_number_cast(request.lower_number, request.upper_number)}


@app.post("/v1/zhouyi/three-numbers")
def cast_yi_three_numbers(request: YiThreeNumberRequest):
    return {"data": yi_three_number_cast(*request.numbers, mapping_version=request.mapping_version)}


@app.post("/v1/meihua/time")
def cast_meihua_time(request: CalendarRequest):
    return {"data": meihua_time_cast(**request.dict())}


@app.post("/v1/meihua/auto")
def cast_meihua_auto(request: AutoCastRequest):
    return {"data": meihua_auto_cast(**request.dict())}


@app.post("/v1/meihua/numbers")
def cast_meihua_numbers(request: MeihuaNumberRequest):
    return {"data": meihua_number_cast(request.upper_number, request.lower_number)}


@app.post("/v1/meihua/three-numbers")
def cast_meihua_three_numbers(request: MeihuaThreeNumberRequest):
    return {"data": meihua_three_number_cast(*request.numbers)}


@app.post("/v1/liuyao/time")
def cast_liuyao_time(request: LiuyaoCalendarRequest):
    return {"data": liuyao_time_cast(**request.dict())}


@app.post("/v1/liuyao/auto")
def cast_liuyao_auto(request: LiuyaoAutoRequest):
    return {"data": liuyao_auto_cast(**request.dict())}


@app.post("/v1/liuyao/numbers")
def cast_liuyao_numbers(request: LiuyaoNumberRequest):
    values = request.dict()
    lower_number = values.pop("lower_number")
    upper_number = values.pop("upper_number")
    return {"data": liuyao_number_cast(lower_number, upper_number, **values)}


@app.post("/v1/liuyao/lines")
def cast_liuyao_lines(request: LiuyaoLineRequest):
    values = request.dict()
    lines = values.pop("lines")
    return {"data": liuyao_line_cast(lines, **values)}


@app.post("/v1/liuyao/coins")
def cast_liuyao_coins(request: LiuyaoCoinRequest):
    values = request.dict()
    coins = values.pop("coins")
    return {"data": liuyao_coin_cast(coins, **values)}


@app.post("/v1/liuren/time")
def cast_liuren_time(request: CalendarRequest):
    return {"data": liuren_time_cast(**request.dict())}


@app.post("/v1/liuren/auto")
def cast_liuren_auto(request: AutoCastRequest):
    return {"data": liuren_auto_cast(**request.dict())}


@app.post("/v1/liuren/numbers")
def cast_liuren_numbers(request: LiurenNumberRequest):
    values = request.dict()
    number = values.pop("number")
    return {"data": liuren_number_cast(number, **values)}


@app.post("/v1/ziwei/time")
def cast_ziwei_time(request: ZiweiRequest):
    return {"data": ziwei_time_cast(**request.dict())}


@app.post("/v1/ziwei/auto")
def cast_ziwei_auto(request: ZiweiAutoRequest):
    return {"data": ziwei_auto_cast(**request.dict())}


@app.post("/v1/bazi/time")
def cast_bazi_time(request: BaZiRequest):
    return {"data": bazi_time_cast(**request.dict())}


@app.post("/v1/bazi/auto")
def cast_bazi_auto(request: BaZiAutoRequest):
    return {"data": bazi_auto_cast(**request.dict())}


@app.post("/v1/bazi/liunian")
def cast_bazi_liunian(request: BaZiLiunianRequest):
    return {"data": bazi_liunian_cast(**request.dict())}


@app.post("/v1/qimen/time")
def cast_qimen_time(request: CalendarRequest):
    return {"data": qimen_time_cast(**request.dict())}


@app.post("/v1/qimen/auto")
def cast_qimen_auto(request: AutoCastRequest):
    return {"data": qimen_auto_cast(**request.dict())}


class BazhaiRequest(BaseModel):
    sitting_mountain: str = Field(..., example="午")
    birth_year: Optional[int] = Field(None, ge=1864, le=2100)
    gender: str = Field("男", example="男")


class XuankongRequest(BaseModel):
    sitting_mountain: str = Field(..., example="午")
    year: Optional[int] = Field(None, ge=1864, le=2100)
    period: Optional[int] = Field(None, ge=1, le=9)
    sitting_degree: Optional[float] = Field(None, ge=0, le=360)


class FengshuiProfileRequest(BaseModel):
    tenant_id: str = Field(..., example="tenant-a")
    building_id: str = Field(..., example="building-001")
    profile: dict


class FengshuiProfileQuery(BaseModel):
    tenant_id: str = Field(..., example="tenant-a")


@app.get("/v1/fengshui/bazhai")
def fengshui_bazhai(
    sitting_mountain: str,
    birth_year: Optional[int] = None,
    gender: str = "男",
):
    return {"data": calculate_bazhai(sitting_mountain, birth_year=birth_year, gender=gender)}


@app.post("/v1/fengshui/bazhai")
def fengshui_bazhai_post(request: BazhaiRequest):
    return {"data": calculate_bazhai(request.sitting_mountain, birth_year=request.birth_year, gender=request.gender)}


@app.get("/v1/fengshui/xuankong")
def fengshui_xuankong(
    sitting_mountain: str,
    year: Optional[int] = None,
    period: Optional[int] = None,
    sitting_degree: Optional[float] = None,
):
    return {"data": calculate_xuankong(sitting_mountain, year=year, period=period, sitting_degree=sitting_degree)}


@app.post("/v1/fengshui/xuankong")
def fengshui_xuankong_post(request: XuankongRequest):
    return {"data": calculate_xuankong(
        request.sitting_mountain, year=request.year, period=request.period,
        sitting_degree=request.sitting_degree,
    )}


@app.get("/v1/fengshui/buildings")
def fengshui_profiles(tenant_id: str):
    try:
        rows = list_profiles(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"data": rows, "meta": {"tenant_id": tenant_id, "count": len(rows)}}


@app.get("/v1/fengshui/buildings/{building_id}")
def fengshui_profile_detail(building_id: str, tenant_id: str):
    try:
        row = get_profile(tenant_id, building_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if row is None:
        raise HTTPException(status_code=404, detail="building profile not found")
    return {"data": row}


@app.post("/v1/fengshui/buildings")
def fengshui_profile_upsert(request: FengshuiProfileRequest):
    try:
        row = upsert_profile(request.tenant_id, request.building_id, request.profile)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"data": row}


@app.delete("/v1/fengshui/buildings/{building_id}")
def fengshui_profile_delete(building_id: str, tenant_id: str):
    try:
        deleted = delete_profile(tenant_id, building_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if not deleted:
        raise HTTPException(status_code=404, detail="building profile not found")
    return {"data": {"deleted": True, "tenant_id": tenant_id, "building_id": building_id}}


@app.post("/v1/fengshui/direction")
def calculate_fengshui_direction(request: FengshuiDirectionRequest):
    return {"data": fengshui_direction(**request.dict())}


@app.post("/v1/fengshui/measurements")
def analyze_fengshui_measurements(request: FengshuiMeasurementsRequest):
    return {"data": fengshui_measurements([value.dict() for value in request.measurements])}


@app.post("/v1/calculations/evaluate")
def evaluate_calculation(request: CalculationRequest):
    return {"data": calculation_envelope(request.module, request.method, request.input)}


@app.post("/v1/calculations/compare")
def compare_calculations(request: ComparisonRequest):
    return {"data": comparison_envelope(request.calculations, request.context)}


# ============================================================
# 交互式推演会话 API（工作流引擎 + 交互模块A-G）
# ============================================================

class SessionCreateRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="求测事由")
    category: str = Field("other", description="事项类别：career/finance/relationship/study/lawsuit/travel/missing_person/lost_item/health/decision/other")
    system: str = Field("auto", description="术数门类：auto/meihua/liuyao/qimen/daliuren/bazi/ziwei")
    casting_method: str = Field("auto", description="起盘方式：auto/time/numbers/manual/coins")
    casting_source: Dict[str, Any] = Field(default_factory=dict, description="起盘素材：local_datetime/timezone/cast_nonce/numbers/gender等")
    user_profile: Dict[str, Any] = Field(default_factory=dict, description="用户信息：gender/age/current_stage等")


class SessionCastRequest(BaseModel):
    pass  # 排盘使用会话中已保存的起盘信息


class SessionInteractRequest(BaseModel):
    interaction_type: str = Field(..., description="交互类型：reality_check/multi_party/multi_choice/review/deep_question/angle_shift")
    payload: Dict[str, Any] = Field(default_factory=dict, description="交互参数")


@app.post("/v1/sessions")
def create_divination_session(request: SessionCreateRequest):
    """创建推演会话（draft 状态），返回信息补全提示或会话信息。"""
    session = create_session(
        question=request.question,
        category=request.category,
        system=request.system,
        casting_method=request.casting_method,
        casting_source=request.casting_source,
        user_profile=request.user_profile,
    )
    store = get_store()
    store.save(session)
    # 信息补全提示（模块A）
    completion = generate_completion_prompt(session)
    return {
        "data": {
            "session_id": session.session_id,
            "status": session.status,
            "question": session.question,
            "category": session.category,
            "system": session.system,
            "casting_method": session.casting_method,
            "info_completion": completion,
        }
    }


@app.get("/v1/sessions")
def list_sessions(limit: int = 50):
    """列出推演会话列表。"""
    store = get_store()
    return {"data": store.list_sessions(limit=limit)}


@app.get("/v1/sessions/{session_id}")
def get_session(session_id: str):
    """获取推演会话完整状态（含不可变快照、交互记录、工作流结果）。"""
    store = get_store()
    session = store.load(session_id)
    if session is None:
        return JSONResponse(status_code=404, content={"error": {"code": "SESSION_NOT_FOUND", "message": "会话不存在"}})
    return {"data": session.to_dict()}


@app.delete("/v1/sessions/{session_id}")
def delete_session(session_id: str):
    """删除推演会话（含不可变快照与交互记录）。"""
    store = get_store()
    session = store.load(session_id)
    if session is None:
        return JSONResponse(status_code=404, content={"error": {"code": "SESSION_NOT_FOUND", "message": "会话不存在"}})
    deleted = store.delete(session_id)
    return {"data": {"session_id": session_id, "deleted": deleted}}


@app.post("/v1/sessions/{session_id}/cast")
def cast_session(session_id: str, request: Optional[SessionCastRequest] = None):
    """执行排盘：运行7步工作流，冻结不可变快照，返回完整推演结果。

    铁律：盘面一经生成永久固定，后续交互不得修改原始卦盘。
    """
    store = get_store()
    session = store.load(session_id)
    if session is None:
        return JSONResponse(status_code=404, content={"error": {"code": "SESSION_NOT_FOUND", "message": "会话不存在"}})
    if session.snapshot is not None and session.snapshot.frozen:
        return JSONResponse(
            status_code=409,
            content={"error": {"code": "SNAPSHOT_FROZEN", "message": "盘面已冻结，不可重新排盘。如需重起，请创建新会话或更换术数门派。"}},
        )
    try:
        session, workflow_result = run_workflow(session)
    except ValueError as exc:
        return JSONResponse(status_code=422, content={"error": {"code": "INSUFFICIENT_INFO", "message": str(exc)}})
    return {
        "data": {
            "session_id": session.session_id,
            "status": session.status,
            "snapshot_id": session.snapshot.snapshot_id if session.snapshot else None,
            "snapshot_frozen": session.snapshot.frozen if session.snapshot else False,
            "formatted_text": workflow_result.get("formatted_text", ""),
            "workflow_result": workflow_result,
        }
    }


@app.post("/v1/sessions/{session_id}/interact")
def interact_session(session_id: str, request: SessionInteractRequest):
    """交互入口：处理现实校验、多方取象、分支推演、事后复盘等交互。

    铁律：所有交互均不得修改已冻结的原始盘面（snapshot）。
    """
    store = get_store()
    session = store.load(session_id)
    if session is None:
        return JSONResponse(status_code=404, content={"error": {"code": "SESSION_NOT_FOUND", "message": "会话不存在"}})
    if session.snapshot is None:
        return JSONResponse(status_code=409, content={"error": {"code": "NOT_CAST_YET", "message": "请先执行排盘（/cast），再进行交互。"}})

    itype = request.interaction_type
    payload = request.payload

    try:
        if itype == "reality_check":
            # 模块B：现实校验
            result = process_reality_response(
                session,
                response=payload.get("response", ""),
                details=payload.get("details"),
            )
            from app.session import append_interaction
            session = append_interaction(
                session, "reality_check",
                user_input={"response": payload.get("response", ""), "details": payload.get("details", "")},
                system_response=result,
                interpretation_shift=result.get("interpretation_shift"),
            )
        elif itype == "multi_party":
            # 模块E：多方人物取象
            result = analyze_multi_party(
                session,
                parties=payload.get("parties"),
                focus_party=payload.get("focus_party"),
            )
            from app.session import append_interaction
            session = append_interaction(session, "multi_party", user_input=payload, system_response=result)
        elif itype == "multi_choice":
            # 模块F：多抉择分支推演
            result = analyze_branches(session, choices=payload.get("choices", []))
            from app.session import append_interaction
            session = append_interaction(session, "multi_choice", user_input=payload, system_response=result)
        elif itype == "review":
            # 模块G：事后复盘
            result = review_outcome(
                session,
                actual_outcome=payload.get("actual_outcome", ""),
                outcome_details=payload.get("outcome_details"),
            )
            from app.session import append_interaction
            session = append_interaction(session, "review", user_input=payload, system_response=result)
        elif itype == "info_completion":
            # 模块A：应用信息补全答案
            session = apply_completion_answers(session, payload.get("answers", {}))
            store.save(session)
            result = {"applied": True, "session": session.to_dict()}
        elif itype == "deep_question":
            # 模块D②：深度追问（基于已冻结盘面的符号/断语深化解读）
            result = deep_question(session, question=payload.get("question", ""))
            from app.session import append_interaction
            session = append_interaction(session, "deep_question", user_input=payload, system_response=result)
        elif itype == "angle_shift":
            # 模块D③：换角度解读（仅调整事理解读视角，原始卦盘不变）
            result = angle_shift(session, new_angle=payload.get("new_angle", ""))
            from app.session import append_interaction
            session = append_interaction(
                session, "angle_shift",
                user_input=payload, system_response=result,
                interpretation_shift={"note": result.get("shift_focus", ""), "suggested_angles": result.get("suggested_angles", [])},
            )
        else:
            return JSONResponse(status_code=400, content={"error": {"code": "UNKNOWN_INTERACTION", "message": f"不支持的交互类型：{itype}"}})

        store.save(session)
        return {"data": {"session_id": session.session_id, "interaction_result": result, "snapshot_unchanged": True}}
    except Exception:
        # 异常详情只进服务端日志；回给客户端的信息不含内部路径、库名与堆栈
        logger.exception("interaction failed: session=%s type=%s", session_id, payload.get("interaction_type"))
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERACTION_ERROR", "message": "交互处理失败，请查看服务端日志"}},
        )


if os.environ.get("SERVE_WEB") == "1":
    default_web_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    web_dist = Path(os.environ.get("WEB_DIST_DIR", str(default_web_dist))).resolve()
    if not (web_dist / "index.html").is_file():
        raise RuntimeError("compiled web assets are missing: {}".format(web_dist))
    app.mount("/", StaticFiles(directory=str(web_dist), html=True), name="web")

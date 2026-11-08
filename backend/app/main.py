import hmac
import json
import logging
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, conint, conlist, constr, field_validator

from app.common.classics import get_library as get_classics_library
from app.common.calculation_dispatch import execute_calculation
from app.common.hashing import canonical_hash
from app.core.advisory import CATEGORY_PROFILES, generate_advisory
from app.calendar import calendar_analysis
from app.core.constants import HEXAGRAM_NAMES, KING_WEN_MATRIX, TRIGRAMS
from app.core.explanation import explain_calculation_set
from app.core.interpretation import explain_correspondences
from app.core.literature import collect_literature_opinions
from app.core.imagery import collect_imagery
from app.fengshui.bazhai import calculate_bazhai
from app.fengshui.storage import (
    delete_profile, get_profile, list_profiles, resolve_tenant, upsert_profile,
)
from app.fengshui.xuankong import calculate_xuankong
from app.core.db import db_repository
from app.core.registry import load_rule_registry, load_validation_cases
from app.core.synthesis import synthesize
from app.core.validation import run_validation_cases
from app.core.yuanhui import analyze_yuan_hui_yun_shi
from app.core.yuanhui_readonly import cycle_cast
from app.bazi.lifeline import analyze_lifeline
from app.bazi.tieban import tieban_status
from app.session import create_session, get_store
from app.session.ownership import HEADER_NAME as OWNER_HEADER_NAME
from app.session.ownership import claim_or_match, client_id_from, owner_hash
from app.workflow import run_workflow
from app.workflow.scheduler import SUPPORTED_SYSTEMS
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
    local_datetime: str = Field(..., json_schema_extra={"example": "2026-08-15T16:00:00"})
    timezone: str = Field(..., json_schema_extra={"example": "Asia/Shanghai"})
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    use_true_solar_time: bool = False


class AutoCastRequest(CalendarRequest):
    cast_nonce: constr(
        strip_whitespace=True, min_length=16, max_length=128,
        pattern=r"^[A-Za-z0-9_-]+$",
    )


class YiManualRequest(BaseModel):
    lines: conlist(conint(ge=6, le=9), min_length=6, max_length=6)


class YiNumberRequest(BaseModel):
    lower_number: int
    upper_number: int


class YiThreeNumberRequest(BaseModel):
    numbers: conlist(conint(strict=True, ge=0), min_length=3, max_length=3)
    mapping_version: constr(strip_whitespace=True, min_length=1, max_length=80) = "earlier-heaven-number-v1"


class MeihuaNumberRequest(BaseModel):
    upper_number: int
    lower_number: int


class MeihuaThreeNumberRequest(BaseModel):
    numbers: conlist(conint(strict=True), min_length=3, max_length=3)


class LiuyaoCalendarRequest(CalendarRequest):
    focus: Optional[str] = Field(None, json_schema_extra={"example": "求财买卖"})


class LiuyaoAutoRequest(AutoCastRequest):
    focus: Optional[str] = Field(None, json_schema_extra={"example": "求财买卖"})


class LiuyaoNumberRequest(LiuyaoCalendarRequest):
    lower_number: int
    upper_number: int


class LiuyaoLineRequest(LiuyaoCalendarRequest):
    lines: conlist(conint(strict=True, ge=6, le=9), min_length=6, max_length=6)


CoinRound = conlist(conint(strict=True, ge=2, le=3), min_length=3, max_length=3)


class LiuyaoCoinRequest(LiuyaoCalendarRequest):
    coins: conlist(CoinRound, min_length=6, max_length=6)


class LiurenNumberRequest(CalendarRequest):
    number: conint(strict=True)


class ZiweiRequest(CalendarRequest):
    gender: str = Field("男", json_schema_extra={"example": "男"})


class ZiweiAutoRequest(AutoCastRequest):
    gender: str = Field("男", json_schema_extra={"example": "男"})


class BaZiRequest(CalendarRequest):
    gender: str = Field("男", json_schema_extra={"example": "男"})


class BaZiAutoRequest(AutoCastRequest):
    gender: str = Field("男", json_schema_extra={"example": "男"})


class BaZiLiunianRequest(CalendarRequest):
    gender: str = Field("男", json_schema_extra={"example": "男"})
    start_year: Optional[int] = Field(None, ge=1900, le=2100, description="起始公历年，默认起运年")
    count: int = Field(10, ge=1, le=60, description="流年条数（1-60）")


class BaZiLifelineRequest(CalendarRequest):
    gender: str = Field("男", json_schema_extra={"example": "男"})
    start_year: Optional[int] = Field(None, ge=1900, le=2100, description="起始公历年，默认起运年")
    count: int = Field(12, ge=1, le=60, description="生平时间轴年数（1-60）")
    events: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="已发生事件（只读对齐，须含整数 year；不用于反推生辰或预测）",
    )


class YuanhuiCycleRequest(BaseModel):
    year: int = Field(..., ge=1900, le=2100, json_schema_extra={"example": 2026})


class FengshuiDirectionRequest(BaseModel):
    facing_degree: float
    input_reference: str = "magnetic"
    magnetic_declination: float = 0.0
    measurement_error: float = Field(0.0, ge=0, le=180)
    declination_source: Optional[constr(strip_whitespace=True, min_length=1, max_length=200)] = None
    measurement_method: Optional[constr(strip_whitespace=True, min_length=1, max_length=100)] = None

    @field_validator("facing_degree", "magnetic_declination", "measurement_error", mode="before")
    @classmethod
    def numeric_fields_are_strict_and_finite(cls, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("must be a finite number")
        return value

    @field_validator("input_reference")
    @classmethod
    def reference_is_supported(cls, value):
        if value not in ("magnetic", "true"):
            raise ValueError("must be magnetic or true")
        return value


class FengshuiMeasurementsRequest(BaseModel):
    measurements: conlist(FengshuiDirectionRequest, min_length=3, max_length=12)


class CalculationRequest(BaseModel):
    module: str
    method: str
    input: Dict[str, Any]


class AdvisoryContext(BaseModel):
    category: str
    question_summary: constr(strip_whitespace=True, min_length=1, max_length=200)

    @field_validator("category")
    @classmethod
    def category_is_supported(cls, value):
        if value not in CATEGORY_PROFILES:
            raise ValueError("unsupported category")
        return value


class ComparisonRequest(BaseModel):
    calculations: conlist(CalculationRequest, min_length=1, max_length=8)
    context: Optional[AdvisoryContext] = None


def _calendar_payload(values):
    return calendar_analysis(**values)


# module/method → 入参校验模型。引擎调用统一由 common/calculation_dispatch 的
# CALCULATION_HANDLERS 承担：这里只保留"用什么模型校验"，不再维护第二份调用表，
# 新增方法只需在分发表加一条、在这里加一个模型。
CALCULATION_MODELS = {
    ("calendar", "analyze"): CalendarRequest,
    ("zhouyi", "manual"): YiManualRequest,
    ("zhouyi", "auto"): AutoCastRequest,
    ("zhouyi", "time"): CalendarRequest,
    ("zhouyi", "numbers"): YiNumberRequest,
    ("zhouyi", "three_numbers"): YiThreeNumberRequest,
    ("meihua", "time"): CalendarRequest,
    ("meihua", "auto"): AutoCastRequest,
    ("meihua", "numbers"): MeihuaNumberRequest,
    ("meihua", "three_numbers"): MeihuaThreeNumberRequest,
    ("liuyao", "time"): CalendarRequest,
    ("liuyao", "auto"): AutoCastRequest,
    ("liuyao", "numbers"): LiuyaoNumberRequest,
    ("liuyao", "lines"): LiuyaoLineRequest,
    ("liuyao", "coins"): LiuyaoCoinRequest,
    ("liuren", "time"): CalendarRequest,
    ("liuren", "auto"): AutoCastRequest,
    ("liuren", "numbers"): LiurenNumberRequest,
    ("ziwei", "time"): ZiweiRequest,
    ("ziwei", "auto"): ZiweiAutoRequest,
    ("bazi", "time"): BaZiRequest,
    ("bazi", "auto"): BaZiAutoRequest,
    ("bazi", "liunian"): BaZiLiunianRequest,
    ("qimen", "time"): CalendarRequest,
    ("qimen", "auto"): AutoCastRequest,
    ("fengshui", "direction"): FengshuiDirectionRequest,
    ("fengshui", "measurements"): FengshuiMeasurementsRequest,
}


def execute(module, method, payload):
    """校验入参后交给统一分发表执行。未知组合直接报错。"""
    model = CALCULATION_MODELS.get((module, method))
    if model is None:
        raise ValueError(f"unsupported calculation: {module}/{method}")
    return execute_calculation(module, method, model(**payload).model_dump())


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
        calculation.model_dump() if isinstance(calculation, CalculationRequest) else calculation
        for calculation in calculations
    ]
    normalized = sorted(
        normalized,
        key=lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    )
    normalized_context = context.model_dump() if isinstance(context, AdvisoryContext) else context
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
        supplied = request.headers.get("Authorization", "")
        if protected and not hmac.compare_digest(supplied, f"Bearer {API_TOKEN}"):
            return JSONResponse(status_code=401, content={"error": {"code": "UNAUTHORIZED", "message": "valid bearer token required"}})
    return await call_next(request)


# 速率限制（仅在生产受保护部署启用：RATE_LIMIT_PER_MINUTE>0 时对写操作限流）
# + 审计日志（记录方法/路径/客户端标识/鉴权状态/响应码）。默认关闭限流，避免本地开发与测试被节流。
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "0") or "0")
_audit_logger = logging.getLogger("destiny.audit")
_rate_limit_buckets: Dict[str, list] = {}


@app.middleware("http")
async def rate_limit_and_audit_middleware(request: Request, call_next):
    path = request.url.path
    client_tag = (
        request.headers.get(OWNER_HEADER_NAME)
        or (request.client.host if request.client else "anonymous")
    )
    if RATE_LIMIT_PER_MINUTE and request.method in ("POST", "DELETE", "PUT"):
        now = time.monotonic()
        bucket = _rate_limit_buckets.get(client_tag)
        if bucket is None or now - bucket[1] >= 60:
            _rate_limit_buckets[client_tag] = [1, now]
        else:
            bucket[0] += 1
            if bucket[0] > RATE_LIMIT_PER_MINUTE:
                return JSONResponse(
                    status_code=429,
                    content={"error": {"code": "RATE_LIMITED", "message": "请求过于频繁，请稍后再试"}},
                )
    response = await call_next(request)
    if path != "/health":
        _audit_logger.info(
            "audit method=%s path=%s status=%s client=%s auth=%s",
            request.method, path, response.status_code,
            "set" if request.headers.get(OWNER_HEADER_NAME) else "unset",
            "set" if request.headers.get("Authorization") else "unset",
        )
    return response


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    if request.url.scheme == "https":
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "INVALID_CALCULATION_INPUT", "message": str(exc)}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_{}".format(exc.status_code), "message": exc.detail}},
    )


@app.on_event("startup")
def warm_classics():
    try:
        get_classics_library()
        logging.getLogger("destiny.startup").info("classics library warmed on startup")
    except Exception as exc:  # noqa: BLE001 - 启动预热失败不应阻断服务
        logging.getLogger("destiny.startup").warning("classics warm-up skipped: %s", exc)


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
    """本地典籍库状态：收录书目、字符量与来源补齐记录/残余缺口。"""
    library = get_classics_library()
    if not library.available:
        return {"data": {"available": False, "corpus_dir": str(library.corpus_dir)}}
    status = library.status()
    status["available"] = True
    return {"data": status}


@app.get("/v1/classics/search")
def classics_search(
    q: str = Query(..., min_length=1, max_length=100),
    category: Optional[str] = Query(None, max_length=40),
    title: Optional[str] = Query(None, max_length=100),
    limit: int = Query(5, ge=1, le=20),
):
    """按关键词检索本地典籍原文段落，作为结论依据。"""
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
    return {"data": execute_calculation("calendar", "analyze", request.model_dump())}


@app.post("/v1/zhouyi/manual")
def cast_yi_manual(request: YiManualRequest):
    return {"data": execute_calculation("zhouyi", "manual", request.model_dump())}


@app.post("/v1/zhouyi/auto")
def cast_yi_auto(request: AutoCastRequest):
    return {"data": execute_calculation("zhouyi", "auto", request.model_dump())}


@app.post("/v1/zhouyi/time")
def cast_yi_time(request: CalendarRequest):
    return {"data": execute_calculation("zhouyi", "time", request.model_dump())}


@app.post("/v1/zhouyi/numbers")
def cast_yi_numbers(request: YiNumberRequest):
    return {"data": execute_calculation("zhouyi", "numbers", request.model_dump())}


@app.post("/v1/zhouyi/three-numbers")
def cast_yi_three_numbers(request: YiThreeNumberRequest):
    return {"data": execute_calculation("zhouyi", "three_numbers", request.model_dump())}


@app.post("/v1/meihua/time")
def cast_meihua_time(request: CalendarRequest):
    return {"data": execute_calculation("meihua", "time", request.model_dump())}


@app.post("/v1/meihua/auto")
def cast_meihua_auto(request: AutoCastRequest):
    return {"data": execute_calculation("meihua", "auto", request.model_dump())}


@app.post("/v1/meihua/numbers")
def cast_meihua_numbers(request: MeihuaNumberRequest):
    return {"data": execute_calculation("meihua", "numbers", request.model_dump())}


@app.post("/v1/meihua/three-numbers")
def cast_meihua_three_numbers(request: MeihuaThreeNumberRequest):
    return {"data": execute_calculation("meihua", "three_numbers", request.model_dump())}


@app.post("/v1/liuyao/time")
def cast_liuyao_time(request: LiuyaoCalendarRequest):
    return {"data": execute_calculation("liuyao", "time", request.model_dump())}


@app.post("/v1/liuyao/auto")
def cast_liuyao_auto(request: LiuyaoAutoRequest):
    return {"data": execute_calculation("liuyao", "auto", request.model_dump())}


@app.post("/v1/liuyao/numbers")
def cast_liuyao_numbers(request: LiuyaoNumberRequest):
    return {"data": execute_calculation("liuyao", "numbers", request.model_dump())}


@app.post("/v1/liuyao/lines")
def cast_liuyao_lines(request: LiuyaoLineRequest):
    return {"data": execute_calculation("liuyao", "lines", request.model_dump())}


@app.post("/v1/liuyao/coins")
def cast_liuyao_coins(request: LiuyaoCoinRequest):
    return {"data": execute_calculation("liuyao", "coins", request.model_dump())}


@app.post("/v1/liuren/time")
def cast_liuren_time(request: CalendarRequest):
    return {"data": execute_calculation("liuren", "time", request.model_dump())}


@app.post("/v1/liuren/auto")
def cast_liuren_auto(request: AutoCastRequest):
    return {"data": execute_calculation("liuren", "auto", request.model_dump())}


@app.post("/v1/liuren/numbers")
def cast_liuren_numbers(request: LiurenNumberRequest):
    return {"data": execute_calculation("liuren", "numbers", request.model_dump())}


@app.post("/v1/ziwei/time")
def cast_ziwei_time(request: ZiweiRequest):
    return {"data": execute_calculation("ziwei", "time", request.model_dump())}


@app.post("/v1/ziwei/auto")
def cast_ziwei_auto(request: ZiweiAutoRequest):
    return {"data": execute_calculation("ziwei", "auto", request.model_dump())}


@app.post("/v1/bazi/time")
def cast_bazi_time(request: BaZiRequest):
    return {"data": execute_calculation("bazi", "time", request.model_dump())}


@app.post("/v1/bazi/auto")
def cast_bazi_auto(request: BaZiAutoRequest):
    return {"data": execute_calculation("bazi", "auto", request.model_dump())}


@app.post("/v1/bazi/liunian")
def cast_bazi_liunian(request: BaZiLiunianRequest):
    try:
        return {"data": execute_calculation("bazi", "liunian", request.model_dump())}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.post("/v1/bazi/lifeline")
def cast_bazi_lifeline(request: BaZiLifelineRequest):
    """个人生平时间轴：子平月令事实 + 岁运 + 皇极经世背景 + 已录事件对齐。

    不预测未来事件、不由事件反推生辰、不生成吉凶断语。
    """
    try:
        return {"data": analyze_lifeline(**request.model_dump())}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/v1/yuanhui/cycle")
def yuanhui_cycle(year: int = Query(2026, ge=1900, le=2100)):
    """皇极经世元会运世定位（只读，纪元锚点待专家审核）。"""
    try:
        return {"data": cycle_cast(year)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/v1/tieban/status")
def tieban_capability_status():
    """铁板神数能力状态：如实声明条文库/考刻/映射的数据缺口，不输出条数或断语。"""
    return {"data": tieban_status()}


@app.post("/v1/qimen/time")
def cast_qimen_time(request: CalendarRequest):
    return {"data": execute_calculation("qimen", "time", request.model_dump())}


@app.post("/v1/qimen/auto")
def cast_qimen_auto(request: AutoCastRequest):
    return {"data": execute_calculation("qimen", "auto", request.model_dump())}


# ============================================================
# 阳宅风水：八宅 / 玄空 / 房屋档案
# ============================================================

class BazhaiRequest(BaseModel):
    sitting_mountain: str = Field(..., json_schema_extra={"example": "午"})
    birth_year: Optional[int] = Field(None, ge=1864, le=2100)
    gender: str = Field("男", json_schema_extra={"example": "男"})


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


class XuankongRequest(BaseModel):
    sitting_mountain: str = Field(..., json_schema_extra={"example": "午"})
    year: Optional[int] = Field(None, ge=1864, le=2100)
    period: Optional[int] = Field(None, ge=1, le=9)
    sitting_degree: Optional[float] = Field(None, ge=0, le=360)
    include_tihua_reference: bool = Field(False, json_schema_extra={"example": False})
    include_tihua_chart: bool = Field(False, json_schema_extra={"example": False})


@app.get("/v1/fengshui/xuankong")
def fengshui_xuankong(
    sitting_mountain: str,
    year: Optional[int] = Query(None, ge=1864, le=2100),
    period: Optional[int] = Query(None, ge=1, le=9),
    sitting_degree: Optional[float] = None,
    include_tihua_reference: bool = False,
    include_tihua_chart: bool = False,
):
    return {"data": calculate_xuankong(
        sitting_mountain, year=year, period=period, sitting_degree=sitting_degree,
        include_tihua_reference=include_tihua_reference,
        include_tihua_chart=include_tihua_chart,
    )}


@app.post("/v1/fengshui/xuankong")
def fengshui_xuankong_post(request: XuankongRequest):
    return {"data": calculate_xuankong(
        request.sitting_mountain, year=request.year, period=request.period,
        sitting_degree=request.sitting_degree,
        include_tihua_reference=request.include_tihua_reference,
        include_tihua_chart=request.include_tihua_chart,
    )}


@app.get("/v1/fengshui/buildings")
def fengshui_profiles(tenant_id: Optional[str] = None):
    try:
        resolved = resolve_tenant(tenant_id or "")
        rows = list_profiles(resolved)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"data": rows, "meta": {"tenant_id": resolved, "count": len(rows)}}


@app.get("/v1/fengshui/buildings/{building_id}")
def fengshui_profile_detail(building_id: str, tenant_id: Optional[str] = None):
    try:
        resolved = resolve_tenant(tenant_id or "")
        row = get_profile(resolved, building_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if row is None:
        raise HTTPException(status_code=404, detail="building profile not found")
    return {"data": row}


class FengshuiProfileRequest(BaseModel):
    tenant_id: str = Field(..., json_schema_extra={"example": "tenant-a"})
    building_id: str = Field(..., json_schema_extra={"example": "building-001"})
    profile: Dict[str, Any]


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
def fengshui_profile_delete(building_id: str, tenant_id: Optional[str] = None):
    try:
        resolved = resolve_tenant(tenant_id or "")
        deleted = delete_profile(resolved, building_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if not deleted:
        raise HTTPException(status_code=404, detail="building profile not found")
    return {"data": {"deleted": True, "tenant_id": resolved, "building_id": building_id}}


@app.post("/v1/fengshui/direction")
def calculate_fengshui_direction(request: FengshuiDirectionRequest):
    return {"data": execute_calculation("fengshui", "direction", request.model_dump())}


@app.post("/v1/fengshui/measurements")
def analyze_fengshui_measurements(request: FengshuiMeasurementsRequest):
    return {"data": execute_calculation("fengshui", "measurements", {"measurements": [value.model_dump() for value in request.measurements]})}


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


def _client_owner_or_error(http_request: Request):
    """从 X-Client-Id 取归属；缺失或非法时返回 (None, JSONResponse)。

    放在处理函数体内而不是 Header(...) 依赖里：会话创建接口的请求体校验
    （422 + detail 结构）必须先于归属校验发生，契约测试依赖这个顺序。
    """
    client_id = client_id_from(http_request.headers.get(OWNER_HEADER_NAME))
    if client_id is None:
        return None, JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "CLIENT_ID_REQUIRED",
                    "message": f"缺少或非法的 {OWNER_HEADER_NAME} 请求头：会话接口需要客户端标识才能做归属校验",
                }
            },
        )
    return owner_hash(client_id), None


def _forbidden_session():
    return JSONResponse(
        status_code=403,
        content={"error": {"code": "SESSION_FORBIDDEN", "message": "该会话属于其他客户端，当前客户端无权访问"}},
    )


@app.post("/v1/sessions")
def create_divination_session(request: SessionCreateRequest, http_request: Request):
    """创建推演会话（draft 状态），返回信息补全提示或会话信息。"""
    requested_owner, error = _client_owner_or_error(http_request)
    if error is not None:
        return error
    if request.system not in SUPPORTED_SYSTEMS:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "INVALID_SYSTEM",
                    "message": "不支持的术数门类：{}".format(request.system),
                }
            },
        )
    session = create_session(
        question=request.question,
        category=request.category,
        system=request.system,
        casting_method=request.casting_method,
        casting_source=request.casting_source,
        user_profile=request.user_profile,
        owner_hash=requested_owner,
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
def list_sessions(http_request: Request, limit: int = Query(50, ge=1, le=200)):
    """列出推演会话列表（只含本客户端的会话与迁移前的老会话）。"""
    requested_owner, error = _client_owner_or_error(http_request)
    if error is not None:
        return error
    store = get_store()
    rows = store.list_sessions(limit=limit, owner_hash=requested_owner)
    # 归属哈希只用于服务端比对，不出现在响应里
    for row in rows:
        row.pop("owner_hash", None)
    return {"data": rows}


@app.get("/v1/sessions/{session_id}")
def get_session(session_id: str, http_request: Request):
    """获取推演会话完整状态（含不可变快照、交互记录、工作流结果）。"""
    requested_owner, error = _client_owner_or_error(http_request)
    if error is not None:
        return error
    store = get_store()
    session = store.load(session_id)
    if session is None:
        return JSONResponse(status_code=404, content={"error": {"code": "SESSION_NOT_FOUND", "message": "会话不存在"}})
    adopted = not session.owner_hash
    if not claim_or_match(session, requested_owner):
        return _forbidden_session()
    if adopted:
        # 迁移前的老会话没有 owner：这一次访问即为认领，落盘后其他客户端再来就是 403。
        # 已归属的会话不再每次读取都重写文件。
        store.save(session)
    payload = session.to_dict()
    # 归属哈希只用于服务端比对，不回给客户端
    payload.pop("owner_hash", None)
    return {"data": payload}


@app.delete("/v1/sessions/{session_id}")
def delete_session(session_id: str, http_request: Request):
    """删除推演会话（含不可变快照与交互记录）。"""
    requested_owner, error = _client_owner_or_error(http_request)
    if error is not None:
        return error
    store = get_store()
    session = store.load(session_id)
    if session is None:
        return JSONResponse(status_code=404, content={"error": {"code": "SESSION_NOT_FOUND", "message": "会话不存在"}})
    if not claim_or_match(session, requested_owner):
        return _forbidden_session()
    deleted = store.delete(session_id)
    return {"data": {"session_id": session_id, "deleted": deleted}}


@app.post("/v1/sessions/{session_id}/cast")
def cast_session(session_id: str, http_request: Request, request: Optional[SessionCastRequest] = None):
    """执行排盘：运行7步工作流，冻结不可变快照，返回完整推演结果。

    铁律：盘面一经生成永久固定，后续交互不得修改原始卦盘。
    """
    requested_owner, error = _client_owner_or_error(http_request)
    if error is not None:
        return error
    store = get_store()
    session = store.load(session_id)
    if session is None:
        return JSONResponse(status_code=404, content={"error": {"code": "SESSION_NOT_FOUND", "message": "会话不存在"}})
    if not session.owner_hash:
        # 认领即刻落盘：即使随后排盘失败/被拒，归属也不会退回「谁都能认领」
        if not claim_or_match(session, requested_owner):
            return _forbidden_session()
        store.save(session)
    elif session.owner_hash != requested_owner:
        return _forbidden_session()
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
def interact_session(session_id: str, request: SessionInteractRequest, http_request: Request):
    """交互入口：处理现实校验、多方取象、分支推演、事后复盘等交互。

    铁律：所有交互均不得修改已冻结的原始盘面（snapshot）。
    """
    requested_owner, error = _client_owner_or_error(http_request)
    if error is not None:
        return error
    store = get_store()
    session = store.load(session_id)
    if session is None:
        return JSONResponse(status_code=404, content={"error": {"code": "SESSION_NOT_FOUND", "message": "会话不存在"}})
    if not session.owner_hash:
        if not claim_or_match(session, requested_owner):
            return _forbidden_session()
        store.save(session)
    elif session.owner_hash != requested_owner:
        return _forbidden_session()
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

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, conint, conlist, constr, validator

from app.core.advisory import CATEGORY_PROFILES, generate_advisory
from app.core.calendar import calendar_analysis
from app.core.constants import HEXAGRAM_NAMES, KING_WEN_MATRIX, TRIGRAMS
from app.core.explanation import explain_calculation_set
from app.core.iching import manual_cast as yi_manual_cast
from app.core.iching import number_cast as yi_number_cast
from app.core.literature import collect_literature_opinions
from app.core.meihua import number_cast as meihua_number_cast
from app.core.meihua import time_cast as meihua_time_cast
from app.core.registry import load_rule_registry, load_validation_cases
from app.core.synthesis import synthesize
from app.core.validation import run_validation_cases


APP_VERSION = "0.1.0"
API_TOKEN = os.environ.get("APP_API_TOKEN")


class CalendarRequest(BaseModel):
    local_datetime: str = Field(..., example="2026-08-15T16:00:00")
    timezone: str = Field(..., example="Asia/Shanghai")
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    use_true_solar_time: bool = False


class YiManualRequest(BaseModel):
    lines: conlist(conint(ge=6, le=9), min_items=6, max_items=6)


class YiNumberRequest(BaseModel):
    lower_number: int
    upper_number: int


class MeihuaNumberRequest(BaseModel):
    upper_number: int
    lower_number: int


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


def canonical_hash(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def execute(module, method, payload):
    if module == "calendar" and method == "analyze":
        request = CalendarRequest(**payload)
        return calendar_analysis(**request.dict())
    if module == "zhouyi" and method == "manual":
        request = YiManualRequest(**payload)
        return yi_manual_cast(request.lines)
    if module == "zhouyi" and method == "numbers":
        request = YiNumberRequest(**payload)
        return yi_number_cast(request.lower_number, request.upper_number)
    if module == "meihua" and method == "time":
        request = CalendarRequest(**payload)
        return meihua_time_cast(**request.dict())
    if module == "meihua" and method == "numbers":
        request = MeihuaNumberRequest(**payload)
        return meihua_number_cast(request.upper_number, request.lower_number)
    raise ValueError(f"unsupported calculation: {module}/{method}")


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
    with ThreadPoolExecutor(max_workers=len(normalized)) as executor:
        futures = [
            executor.submit(execute, item["module"], item["method"], item["input"])
            for item in normalized
        ]
        results = [future.result() for future in futures]
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
    return {
        "task_id": "compare_{}".format(input_hash[:24]),
        "status": "completed",
        "input_hash": "sha256:" + input_hash,
        "module_results": module_results,
        "comparison": comparison,
        "explanation": explain_calculation_set(module_results, comparison),
        "advisory": generate_advisory(module_results, normalized_context),
        "literature": collect_literature_opinions(module_results),
        "calculated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


app = FastAPI(
    title="天机演象MVP计算API",
    version=APP_VERSION,
    description="确定性历法、周易和梅花易数事实计算。解释规则尚待专家签署。",
)


@app.middleware("http")
async def internal_token_middleware(request: Request, call_next):
    if API_TOKEN and request.headers.get("Authorization") != f"Bearer {API_TOKEN}":
        return JSONResponse(status_code=401, content={"error": {"code": "UNAUTHORIZED", "message": "valid bearer token required"}})
    return await call_next(request)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=422, content={"error": {"code": "INVALID_CALCULATION_INPUT", "message": str(exc)}})


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "tianji-mvp-calculation",
        "version": APP_VERSION,
        "modules": ["calendar", "zhouyi", "meihua"],
    }


@app.get("/v1/constants/trigrams")
def trigrams():
    return {"data": [{"number": number, **value} for number, value in TRIGRAMS.items()]}


@app.get("/v1/constants/hexagrams")
def hexagrams():
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
    return {"data": sorted(rows, key=lambda row: row["ordinal"])}


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


@app.post("/v1/zhouyi/numbers")
def cast_yi_numbers(request: YiNumberRequest):
    return {"data": yi_number_cast(request.lower_number, request.upper_number)}


@app.post("/v1/meihua/time")
def cast_meihua_time(request: CalendarRequest):
    return {"data": meihua_time_cast(**request.dict())}


@app.post("/v1/meihua/numbers")
def cast_meihua_numbers(request: MeihuaNumberRequest):
    return {"data": meihua_number_cast(request.upper_number, request.lower_number)}


@app.post("/v1/calculations/evaluate")
def evaluate_calculation(request: CalculationRequest):
    return {"data": calculation_envelope(request.module, request.method, request.input)}


@app.post("/v1/calculations/compare")
def compare_calculations(request: ComparisonRequest):
    return {"data": comparison_envelope(request.calculations, request.context)}


if os.environ.get("SERVE_WEB") == "1":
    default_web_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    web_dist = Path(os.environ.get("WEB_DIST_DIR", str(default_web_dist))).resolve()
    if not (web_dist / "index.html").is_file():
        raise RuntimeError("compiled web assets are missing: {}".format(web_dist))
    app.mount("/", StaticFiles(directory=str(web_dist), html=True), name="web")

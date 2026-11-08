import { useState } from "react";
import { CircleAlert, LoaderCircle, LocateFixed, Mountain, Plus, Trash2 } from "lucide-react";
import { analyzeFengshuiDirection, analyzeFengshuiMeasurements } from "../../lib/api";
import { FengshuiView } from "../result/FengshuiView";
import { WorkspaceShell } from "../workspace/WorkspaceShell";

function EmptyState() {
  return (
    <div className="destiny-empty" role="status">
      <Mountain size={22} />
      <strong>尚未生成阳宅坐向</strong>
      <p>在左侧录入向首读数、方位基准与测量误差，然后点击「生成阳宅坐向」。</p>
    </div>
  );
}

function parseNumber(value) {
  return String(value).trim() === "" ? Number.NaN : Number(value);
}

export default function FengshuiPanel() {
  const [mode, setMode] = useState("single");
  const [facing, setFacing] = useState("180");
  const [measurements, setMeasurements] = useState(["179", "180", "181"]);
  const [reference, setReference] = useState("magnetic");
  const [declination, setDeclination] = useState("0");
  const [measurementError, setMeasurementError] = useState("1");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const edit = (setter) => (value) => {
    setter(value);
    setResult(null);
    setError("");
  };

  const updateMeasurement = (index, value) => {
    setMeasurements((current) => current.map((item, itemIndex) => (itemIndex === index ? value : item)));
    setResult(null);
    setError("");
  };

  const addMeasurement = () => {
    setMeasurements((current) => [...current, current[current.length - 1] || "180"]);
    setResult(null);
    setError("");
  };

  const removeMeasurement = (index) => {
    setMeasurements((current) => current.filter((_, itemIndex) => itemIndex !== index));
    setResult(null);
    setError("");
  };

  const buildMeasurement = (degree) => ({
    facing_degree: parseNumber(degree),
    input_reference: reference,
    magnetic_declination: parseNumber(declination),
    measurement_error: parseNumber(measurementError),
    measurement_method: mode === "multiple" ? "web_multi_entry" : "web_manual_entry",
  });

  const handleSubmit = async (event) => {
    event.preventDefault();
    const errorValue = parseNumber(measurementError);
    if (!Number.isFinite(errorValue) || errorValue < 0 || errorValue > 180) {
      setError("测量误差需在 0–180° 之间");
      return;
    }
    if (!Number.isFinite(parseNumber(declination))) {
      setError("磁偏角必须是有效数字");
      return;
    }
    const single = buildMeasurement(facing);
    const rows = measurements.map((degree) => buildMeasurement(degree));
    if (mode === "single" && !Number.isFinite(single.facing_degree)) {
      setError("向首方位角必须是有效数字");
      return;
    }
    if (mode === "multiple" && rows.some((row) => !Number.isFinite(row.facing_degree))) {
      setError("每次向首读数都必须是有效数字");
      return;
    }
    if (mode === "multiple" && (rows.length < 3 || rows.length > 12)) {
      setError("多次共识需要 3–12 次读数");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const data = mode === "single"
        ? await analyzeFengshuiDirection(single)
        : await analyzeFengshuiMeasurements({ measurements: rows });
      setResult(data);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <WorkspaceShell
      kicker="FENGSHUI WORKSPACE"
      title="阳宅风水"
      description="独立录入向首读数与测量基准，计算真北坐向、二十四山、误差范围与多次测量共识。"
      badge="坐向 · 二十四山 · 多次共识"
      sidebar={(
        <form className="form-section fengshui-entry-form" onSubmit={handleSubmit} noValidate>
          <div className="section-title"><Mountain size={16} /><span>阳宅坐向测量</span></div>
          <p className="destiny-form-hint">正北为 0°，顺时针增加；读数应来自建筑向首的现场测量。</p>

          <div className="segmented method-switch" role="radiogroup" aria-label="坐向测量模式">
            <button type="button" className={mode === "single" ? "active" : ""} onClick={() => edit(setMode)("single")}>单次分析</button>
            <button type="button" className={mode === "multiple" ? "active" : ""} onClick={() => edit(setMode)("multiple")}>多次共识</button>
          </div>

          {mode === "single" ? (
            <label>
              <span className="field-label">向首方位角</span>
              <input
                type="number"
                step="0.01"
                value={facing}
                onChange={(event) => edit(setFacing)(event.target.value)}
                required
              />
            </label>
          ) : (
            <div className="measurement-inputs">
              <div className="measurement-inputs-head"><span className="field-label">向首读数</span><small>{measurements.length} / 12</small></div>
              {measurements.map((value, index) => (
                <div className="measurement-input-row" key={index}>
                  <span>{index + 1}</span>
                  <input
                    aria-label={`第${index + 1}次向首读数`}
                    type="number"
                    step="0.01"
                    value={value}
                    onChange={(event) => updateMeasurement(index, event.target.value)}
                    required
                  />
                  <button
                    className="icon-button"
                    type="button"
                    title="删除本次读数"
                    aria-label={`删除第${index + 1}次读数`}
                    disabled={measurements.length <= 3}
                    onClick={() => removeMeasurement(index)}
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              ))}
              <button className="secondary-command" type="button" disabled={measurements.length >= 12} onClick={addMeasurement}>
                <Plus size={15} />增加读数
              </button>
            </div>
          )}

          <div className="segmented method-switch" role="radiogroup" aria-label="方位角基准">
            <button type="button" className={reference === "magnetic" ? "active" : ""} onClick={() => edit(setReference)("magnetic")}>磁北测量</button>
            <button type="button" className={reference === "true" ? "active" : ""} onClick={() => edit(setReference)("true")}>真北测量</button>
          </div>

          <div className="number-pair">
            <label>
              <span className="field-label">磁偏角</span>
              <input
                type="number"
                step="0.01"
                value={declination}
                onChange={(event) => edit(setDeclination)(event.target.value)}
                required
              />
            </label>
            <label>
              <span className="field-label">测量误差 ±</span>
              <input
                type="number"
                step="0.01"
                min="0"
                max="180"
                value={measurementError}
                onChange={(event) => edit(setMeasurementError)(event.target.value)}
                required
              />
            </label>
          </div>

          <div className="method-note">
            <LocateFixed size={16} />
            <p>{mode === "multiple" ? "每次读数独立修正真北，再用圆周均值汇总；离散超过 10° 时不生成可信坐向。" : "磁北角按“真北角 = 磁北角 + 磁偏角”修正；误差跨界时保留全部候选。"}</p>
          </div>

          <button className="primary-button full-button" type="submit" disabled={loading}>
            {loading ? <LoaderCircle size={16} className="spin" /> : <Mountain size={16} />}
            {result ? "重新分析" : "生成阳宅坐向"}
          </button>
        </form>
      )}
    >
      {error && (
        <div className="destiny-error" role="alert">
          <CircleAlert size={16} />
          <span>{error}</span>
        </div>
      )}
      {result ? <FengshuiView result={result} /> : <EmptyState />}
    </WorkspaceShell>
  );
}

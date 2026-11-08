import { useState } from "react";
import { CircleAlert, Compass, Download, Grid3X3, LoaderCircle, LocateFixed, Mountain, Plus, Trash2 } from "lucide-react";
import {
  analyzeFengshuiBazhai,
  analyzeFengshuiDirection,
  analyzeFengshuiMeasurements,
  analyzeFengshuiXuankong,
} from "../../lib/api";
import { downloadMarkdownFile } from "../../lib/export";
import { generateStandaloneReport } from "../../lib/moduleReport";
import { BazhaiView } from "../result/BazhaiView";
import { FengshuiView } from "../result/FengshuiView";
import { XuankongView } from "../result/XuankongView";
import { WorkspaceShell } from "../workspace/WorkspaceShell";

const MOUNTAINS = [
  "子", "癸", "丑", "艮", "寅", "甲", "卯", "乙", "辰", "巽", "巳", "丙",
  "午", "丁", "未", "坤", "申", "庚", "酉", "辛", "戌", "乾", "亥", "壬",
];

const TOOLS = [
  { id: "direction", label: "坐向测量", icon: Mountain },
  { id: "bazhai", label: "八宅", icon: Compass },
  { id: "xuankong", label: "玄空", icon: Grid3X3 },
];

function EmptyState({ icon: Icon = Mountain, title, body }) {
  return (
    <div className="standalone-empty" role="status">
      <Icon size={22} />
      <strong>{title}</strong>
      <p>{body}</p>
    </div>
  );
}

function parseNumber(value) {
  return String(value).trim() === "" ? Number.NaN : Number(value);
}

function ToolTabs({ active, onChange, disabled }) {
  return (
    <div className="standalone-tool-tabs" role="tablist" aria-label="阳宅风水功能">
      {TOOLS.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          type="button"
          role="tab"
          aria-selected={active === id}
          className={active === id ? "active" : ""}
          disabled={disabled}
          onClick={() => onChange(id)}
        >
          <Icon size={15} />
          <span>{label}</span>
        </button>
      ))}
    </div>
  );
}

function ResultBar({ label, onExport }) {
  return (
    <div className="standalone-result-bar">
      <span className="standalone-result-label">{label}</span>
      <button type="button" className="export-btn" onClick={onExport} title={`导出${label} Markdown 报告`}>
        <Download size={14} />
        <span>导出报告</span>
      </button>
    </div>
  );
}

export default function FengshuiPanel() {
  const [tool, setTool] = useState("direction");
  const [mode, setMode] = useState("single");
  const [facing, setFacing] = useState("180");
  const [measurements, setMeasurements] = useState(["179", "180", "181"]);
  const [reference, setReference] = useState("magnetic");
  const [declination, setDeclination] = useState("0");
  const [measurementError, setMeasurementError] = useState("1");
  const [result, setResult] = useState(null);

  const [bazhaiMountain, setBazhaiMountain] = useState("子");
  const [birthYear, setBirthYear] = useState("1984");
  const [bazhaiGender, setBazhaiGender] = useState("男");
  const [bazhaiResult, setBazhaiResult] = useState(null);

  const [xuankongMountain, setXuankongMountain] = useState("子");
  const [xuankongYear, setXuankongYear] = useState("2026");
  const [xuankongPeriod, setXuankongPeriod] = useState("");
  const [xuankongDegree, setXuankongDegree] = useState("");
  const [includeTihuaReference, setIncludeTihuaReference] = useState(false);
  const [includeTihuaChart, setIncludeTihuaChart] = useState(false);
  const [xuankongResult, setXuankongResult] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const switchTool = (id) => {
    if (loading) return;
    setTool(id);
    setError("");
  };

  const editDirection = (setter) => (value) => {
    setter(value);
    setResult(null);
    setError("");
  };

  const editBazhai = (setter) => (value) => {
    setter(value);
    setBazhaiResult(null);
    setError("");
  };

  const editXuankong = (setter) => (value) => {
    setter(value);
    setXuankongResult(null);
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

  const handleDirection = async (event) => {
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

  const handleBazhai = async (event) => {
    event.preventDefault();
    if (birthYear.trim()) {
      const year = parseNumber(birthYear);
      if (!Number.isInteger(year) || year < 1864 || year > 2100) {
        setError("出生年份需为 1864–2100 的整数");
        return;
      }
    }

    setLoading(true);
    setError("");
    try {
      const payload = { sitting_mountain: bazhaiMountain, gender: bazhaiGender };
      if (birthYear.trim()) payload.birth_year = Number(birthYear);
      const data = await analyzeFengshuiBazhai(payload);
      setBazhaiResult(data);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  const handleXuankong = async (event) => {
    event.preventDefault();
    if (!xuankongYear.trim() && !xuankongPeriod) {
      setError("年份或运至少填写一项");
      return;
    }
    if (xuankongYear.trim()) {
      const year = parseNumber(xuankongYear);
      if (!Number.isInteger(year) || year < 1864 || year > 2100) {
        setError("年份需为 1864–2100 的整数");
        return;
      }
    }
    if (xuankongDegree.trim()) {
      const degree = parseNumber(xuankongDegree);
      if (!Number.isFinite(degree) || degree < 0 || degree > 360) {
        setError("坐山实测角度需在 0–360° 之间");
        return;
      }
    }

    setLoading(true);
    setError("");
    try {
      const payload = {
        sitting_mountain: xuankongMountain,
        include_tihua_reference: includeTihuaReference,
        include_tihua_chart: includeTihuaChart,
      };
      if (xuankongPeriod) payload.period = Number(xuankongPeriod);
      if (xuankongYear.trim()) payload.year = Number(xuankongYear);
      if (xuankongDegree.trim()) payload.sitting_degree = Number(xuankongDegree);
      const data = await analyzeFengshuiXuankong(payload);
      setXuankongResult(data);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  const activeResult = tool === "direction" ? result : tool === "bazhai" ? bazhaiResult : xuankongResult;
  const activeLabel = TOOLS.find((item) => item.id === tool)?.label || "阳宅风水";
  const reportModule = tool === "direction"
    ? (result?.facts?.consensus ? "fengshui-measurements" : "fengshui-direction")
    : tool === "bazhai" ? "fengshui-bazhai" : "fengshui-xuankong";

  const handleExportReport = () => {
    if (!activeResult) return;
    const dateStr = new Date().toISOString().slice(0, 10);
    const markdown = generateStandaloneReport(activeResult, {
      module: reportModule,
      title: `阳宅风水 · ${activeLabel}`,
      calculatedAt: new Date().toLocaleString("zh-CN", { hour12: false }),
    });
    downloadMarkdownFile(markdown, `天机演象_阳宅${activeLabel}_${dateStr}.md`);
  };

  return (
    <WorkspaceShell
      kicker="FENGSHUI WORKSPACE"
      title="阳宅风水"
      description="独立录入坐向、八宅命卦或玄空运盘参数，计算真北坐向、二十四山、八宅九星与玄空挨星。"
      badge="坐向 · 八宅 · 玄空"
      tabs={<ToolTabs active={tool} onChange={switchTool} disabled={loading} />}
      sidebar={(
        <>
          {tool === "direction" && (
            <form className="form-section fengshui-entry-form" onSubmit={handleDirection} noValidate>
              <div className="section-title"><Mountain size={16} /><span>阳宅坐向测量</span></div>
              <p className="standalone-form-hint">正北为 0°，顺时针增加；读数应来自建筑向首的现场测量。</p>

              <div className="segmented method-switch" role="radiogroup" aria-label="坐向测量模式">
                <button type="button" className={mode === "single" ? "active" : ""} onClick={() => editDirection(setMode)("single")}>单次分析</button>
                <button type="button" className={mode === "multiple" ? "active" : ""} onClick={() => editDirection(setMode)("multiple")}>多次共识</button>
              </div>

              {mode === "single" ? (
                <label>
                  <span className="field-label">向首方位角</span>
                  <input
                    type="number"
                    step="0.01"
                    value={facing}
                    onChange={(event) => editDirection(setFacing)(event.target.value)}
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
                <button type="button" className={reference === "magnetic" ? "active" : ""} onClick={() => editDirection(setReference)("magnetic")}>磁北测量</button>
                <button type="button" className={reference === "true" ? "active" : ""} onClick={() => editDirection(setReference)("true")}>真北测量</button>
              </div>

              <div className="number-pair">
                <label>
                  <span className="field-label">磁偏角</span>
                  <input
                    type="number"
                    step="0.01"
                    value={declination}
                    onChange={(event) => editDirection(setDeclination)(event.target.value)}
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
                    onChange={(event) => editDirection(setMeasurementError)(event.target.value)}
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

          {tool === "bazhai" && (
            <form className="form-section fengshui-entry-form" onSubmit={handleBazhai} noValidate>
              <div className="section-title"><Compass size={16} /><span>八宅大游年</span></div>
              <p className="standalone-form-hint">按坐山定宅卦与东西四宅，出生年份用于宅命配法；不生成流年断语。</p>

              <label>
                <span className="field-label">坐山</span>
                <select value={bazhaiMountain} onChange={(event) => editBazhai(setBazhaiMountain)(event.target.value)}>
                  {MOUNTAINS.map((mountain) => <option key={mountain} value={mountain}>{mountain}山</option>)}
                </select>
              </label>

              <div className="number-pair">
                <label>
                  <span className="field-label">出生年份（选填）</span>
                  <input
                    type="number"
                    min="1864"
                    max="2100"
                    value={birthYear}
                    onChange={(event) => editBazhai(setBirthYear)(event.target.value)}
                  />
                </label>
                <label>
                  <span className="field-label">性别</span>
                  <select value={bazhaiGender} onChange={(event) => editBazhai(setBazhaiGender)(event.target.value)}>
                    <option value="男">男</option>
                    <option value="女">女</option>
                  </select>
                </label>
              </div>

              <div className="method-note">
                <Compass size={16} />
                <p>大游年歌按通行传本排八方九星；出生年留空时只排宅卦，不做宅命同组/异组判断。</p>
              </div>

              <button className="primary-button full-button" type="submit" disabled={loading}>
                {loading ? <LoaderCircle size={16} className="spin" /> : <Compass size={16} />}
                {bazhaiResult ? "重新排八宅" : "排八宅盘"}
              </button>
            </form>
          )}

          {tool === "xuankong" && (
            <form className="form-section fengshui-entry-form" onSubmit={handleXuankong} noValidate>
              <div className="section-title"><Grid3X3 size={16} /><span>玄空下卦挨星</span></div>
              <p className="standalone-form-hint">按坐山与运造排下卦挨星盘；运缺省用年份推运。替卦起星盘默认不请求。</p>

              <label>
                <span className="field-label">坐山</span>
                <select value={xuankongMountain} onChange={(event) => editXuankong(setXuankongMountain)(event.target.value)}>
                  {MOUNTAINS.map((mountain) => <option key={mountain} value={mountain}>{mountain}山</option>)}
                </select>
              </label>

              <div className="number-pair">
                <label>
                  <span className="field-label">年份（选填）</span>
                  <input
                    type="number"
                    min="1864"
                    max="2100"
                    value={xuankongYear}
                    onChange={(event) => editXuankong(setXuankongYear)(event.target.value)}
                  />
                </label>
                <label>
                  <span className="field-label">运（选填）</span>
                  <select value={xuankongPeriod} onChange={(event) => editXuankong(setXuankongPeriod)(event.target.value)}>
                    <option value="">按年份推运</option>
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((period) => <option key={period} value={period}>{period}运</option>)}
                  </select>
                </label>
              </div>

              <label>
                <span className="field-label">坐山实测角度（选填）</span>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="360"
                  placeholder="例如 7.4"
                  value={xuankongDegree}
                  onChange={(event) => editXuankong(setXuankongDegree)(event.target.value)}
                />
                <small className="field-hint">用于判定是否落替卦区间；留空则不做替卦判定。</small>
              </label>

              <div className="standalone-checkbox-row">
                <label>
                  <input
                    type="checkbox"
                    checked={includeTihuaReference}
                    onChange={(event) => editXuankong(setIncludeTihuaReference)(event.target.checked)}
                  />
                  <span>附替星表参考</span>
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={includeTihuaChart}
                    onChange={(event) => editXuankong(setIncludeTihuaChart)(event.target.checked)}
                  />
                  <span>附替卦起星盘</span>
                </label>
              </div>

              <div className="method-note">
                <Grid3X3 size={16} />
                <p>运星入中按坐山元龙阴阳顺逆飞布；山星、向星分列各宫。格局条件为确定性判定，不含吉凶断语。</p>
              </div>

              <button className="primary-button full-button" type="submit" disabled={loading}>
                {loading ? <LoaderCircle size={16} className="spin" /> : <Grid3X3 size={16} />}
                {xuankongResult ? "重新排玄空" : "排玄空盘"}
              </button>
            </form>
          )}
        </>
      )}
    >
      {error && (
        <div className="standalone-error" role="alert">
          <CircleAlert size={16} />
          <span>{error}</span>
        </div>
      )}

      {tool === "direction" && (result ? (
        <>
          <ResultBar label={`坐向测量 · ${result.facts?.consensus ? "多次共识" : "单次分析"}`} onExport={handleExportReport} />
          <FengshuiView result={result} />
        </>
      ) : (
        <EmptyState
          title="尚未生成阳宅坐向"
          body="在左侧录入向首读数、方位基准与测量误差，然后点击「生成阳宅坐向」。"
        />
      ))}

      {tool === "bazhai" && (bazhaiResult ? (
        <>
          <ResultBar label="八宅大游年" onExport={handleExportReport} />
          <BazhaiView result={bazhaiResult} />
        </>
      ) : (
        <EmptyState
          icon={Compass}
          title="尚未排八宅盘"
          body="在左侧选择坐山，可填写出生年份与性别做宅命配法，然后点击「排八宅盘」。"
        />
      ))}

      {tool === "xuankong" && (xuankongResult ? (
        <>
          <ResultBar label="玄空挨星" onExport={handleExportReport} />
          <XuankongView result={xuankongResult} />
        </>
      ) : (
        <EmptyState
          icon={Grid3X3}
          title="尚未排玄空盘"
          body="在左侧选择坐山与运，可选填年份和实测角度，然后点击「排玄空盘」。"
        />
      ))}
    </WorkspaceShell>
  );
}

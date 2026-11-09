import { useState } from "react";
import { CalendarDays, CircleAlert, Download, FileText, Layers3 } from "lucide-react";
import { analyzeCalendar, compareCalculations } from "../../lib/api";
import { buildCalculations, calendarPayload } from "../../lib/calculationPlan";
import { newCastNonce } from "../../lib/castingInput";
import { downloadMarkdownFile, generateMarkdownReport } from "../../lib/export";
import { systemForm } from "../../lib/formDefaults";
import { saveDeductionHistory } from "../../lib/storage";
import InputPanel from "../InputPanel";
import { CalendarView } from "../result/CalendarView";
import { ExplanationView } from "../result/ExplanationView";
import { Notice, findModule } from "../result/shared";
import { WorkspaceShell } from "../workspace/WorkspaceShell";

function Advisory({ advisory, question }) {
  if (!advisory?.conclusion) return null;
  const recommendations = advisory.recommendations || [];
  return (
    <section className="advisory-overview standalone-advisory">
      <div className="advisory-overview-head">
        <div>
          <span>结合所问：{question}</span>
          <strong>{advisory.conclusion.headline}</strong>
        </div>
      </div>
      <p>{advisory.conclusion.text}</p>
      {recommendations.length > 0 && (
        <div className="advisory-quick-actions">
          {recommendations.slice(0, 3).map((recommendation) => (
            <div key={recommendation.title}>
              <strong>{recommendation.title}</strong>
              <span>{recommendation.detail}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function EmptyState({ tab }) {
  const Icon = tab.icon;
  return (
    <div className="standalone-empty" role="status">
      <Icon size={22} />
      <strong>{tab.emptyTitle}</strong>
      <p>{tab.emptyDesc}</p>
    </div>
  );
}

export default function ConsultPanel({
  kicker,
  title,
  description,
  badge,
  tabs,
  views,
  panelKicker,
  panelTitle,
  submitLabel,
  submitLoadingLabel,
}) {
  const [activeTab, setActiveTab] = useState(tabs[0].id);
  const [form, setForm] = useState(() => systemForm(tabs[0].id));
  const [result, setResult] = useState(null);
  const [resultQuestion, setResultQuestion] = useState("");
  const [resultTab, setResultTab] = useState("board");
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [error, setError] = useState("");

  const active = tabs.find((tab) => tab.id === activeTab) || tabs[0];
  const activeResult = findModule(result, activeTab);
  const calendar = findModule(result, "calendar");
  const hasExplanation = Boolean(
    result?.explanation
    || result?.advisory
    || result?.literature
    || result?.imagery
    || result?.yuan_hui_yun_shi
    || result?.interpretation,
  );
  const resultTabs = [
    { id: "board", label: "盘面", icon: Layers3 },
    ...(hasExplanation ? [{ id: "explanation", label: "结论建议", icon: FileText }] : []),
    ...(calendar ? [{ id: "calendar", label: "历法", icon: CalendarDays }] : []),
  ];
  const View = views[activeTab];

  const changeTab = (id) => {
    if (loading) return;
    setActiveTab(id);
    setForm((current) => ({ ...current, scene: id }));
    setResult(null);
    setResultQuestion("");
    setResultTab("board");
    setPreview(null);
    setError("");
  };

  const handlePreview = async () => {
    setPreviewLoading(true);
    setError("");
    try {
      setPreview(await analyzeCalendar(calendarPayload(form)));
    } catch (requestError) {
      setError(requestError.message);
      setPreview(null);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    const activeForm = { ...form, scene: activeTab, castNonce: newCastNonce() };
    setForm(activeForm);
    try {
      const response = await compareCalculations(buildCalculations(activeForm), {
        category: activeForm.category,
        question_summary: activeForm.question,
      });
      setResult(response);
      setResultQuestion(activeForm.question);
      setResultTab("board");
      setPreview(null);

      // 各模块独立成页后，本地历史存档改由各模块提交时落盘，避免随「综合推演」一起消失
      const ctx = {
        scene: activeTab,
        category: activeForm.category,
        question: activeForm.question,
        input: {
          local_datetime: activeForm.localDatetime,
          timezone: activeForm.timezone,
          cast_nonce: activeForm.castNonce,
          use_true_solar: activeForm.trueSolar,
          longitude: activeForm.trueSolar ? Number(activeForm.longitude) : null,
        },
      };
      if (!saveDeductionHistory(response.task_id, ctx, response)) {
        setError("本地存档空间不足，本次结果未保存，请先导出或清理历史存档");
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setForm(systemForm(activeTab));
    setResult(null);
    setResultQuestion("");
    setResultTab("board");
    setPreview(null);
    setError("");
  };

  const handleRecast = () => {
    setForm((current) => ({ ...current, castNonce: newCastNonce() }));
    setResult(null);
    setResultQuestion("");
    setResultTab("board");
    setPreview(null);
    setError("");
  };

  const handleExportReport = () => {
    if (!result) return;
    const dateStr = new Date().toISOString().slice(0, 10);
    const question = resultQuestion || form.question || active.label;
    const markdown = generateMarkdownReport(result, {
      scene: activeTab,
      category: form.category,
      question,
    });
    downloadMarkdownFile(markdown, `天机演象_${active.label}_${question.slice(0, 10)}_${dateStr}.md`);
  };

  return (
    <WorkspaceShell
      kicker={kicker}
      title={title}
      description={description}
      badge={badge}
      sidebar={(
        <InputPanel
          form={form}
          setForm={setForm}
          onSubmit={handleSubmit}
          onPreview={handlePreview}
          onReset={handleReset}
          onRecast={handleRecast}
          loading={loading}
          previewLoading={previewLoading}
          preview={preview}
          error={error}
          panelKicker={panelKicker}
          panelTitle={panelTitle}
          submitLabel={submitLabel}
          submitLoadingLabel={submitLoadingLabel}
        />
      )}
    >
      <div className="standalone-tabs" role="tablist" aria-label={`${title}页签`}>
        {tabs.map(({ id, label, icon: Icon, desc }) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={activeTab === id}
            className={activeTab === id ? "active" : ""}
            onClick={() => changeTab(id)}
            title={desc}
            disabled={loading}
          >
            <Icon size={16} />
            <span>{label}</span>
          </button>
        ))}
      </div>

      <div className="standalone-tab-body" role="tabpanel" aria-label={active.label}>
        {result ? (
          <>
            <div className="standalone-result-bar">
              <div className="standalone-result-tabs" role="tablist" aria-label={`${active.label}结果视图`}>
                {resultTabs.map(({ id, label, icon: Icon }) => (
                  <button
                    key={id}
                    type="button"
                    role="tab"
                    aria-selected={resultTab === id}
                    className={resultTab === id ? "active" : ""}
                    onClick={() => setResultTab(id)}
                  >
                    <Icon size={15} />
                    <span>{label}</span>
                  </button>
                ))}
              </div>
              <button type="button" className="export-btn" onClick={handleExportReport} title="导出当前体系 Markdown 报告">
                <Download size={14} />
                <span>导出报告</span>
              </button>
            </div>

            {resultTab === "board" && (
              <>
                <Advisory advisory={result.advisory} question={resultQuestion || form.question} />
                {activeResult && View ? (
                  <View result={activeResult} />
                ) : (
                  <Notice tone="warning" icon={CircleAlert}>
                    后端返回中没有 {active.label} 模块结果，未渲染空盘。
                  </Notice>
                )}
              </>
            )}

            {resultTab === "explanation" && (
              <ExplanationView
                explanation={result.explanation}
                advisory={result.advisory}
                literature={result.literature}
                imagery={result.imagery}
                yuanHui={result.yuan_hui_yun_shi}
                interpretation={result.interpretation}
              />
            )}

            {resultTab === "calendar" && <CalendarView calendar={calendar} />}
          </>
        ) : (
          <EmptyState tab={active} />
        )}
      </div>
    </WorkspaceShell>
  );
}

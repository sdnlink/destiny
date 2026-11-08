import { useState } from "react";
import { CircleAlert } from "lucide-react";
import { analyzeCalendar, compareCalculations } from "../../lib/api";
import { buildCalculations, calendarPayload } from "../../lib/calculationPlan";
import { newCastNonce } from "../../lib/castingInput";
import { systemForm } from "../../lib/formDefaults";
import InputPanel from "../InputPanel";
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
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [error, setError] = useState("");

  const active = tabs.find((tab) => tab.id === activeTab) || tabs[0];
  const activeResult = findModule(result, activeTab);
  const View = views[activeTab];

  const changeTab = (id) => {
    if (loading) return;
    setActiveTab(id);
    setForm((current) => ({ ...current, scene: id }));
    setResult(null);
    setResultQuestion("");
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
      setPreview(null);
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
    setPreview(null);
    setError("");
  };

  const handleRecast = () => {
    setForm((current) => ({ ...current, castNonce: newCastNonce() }));
    setResult(null);
    setResultQuestion("");
    setPreview(null);
    setError("");
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
          showSceneSwitch={false}
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
            <Advisory advisory={result.advisory} question={resultQuestion || form.question} />
            {activeResult && View ? (
              <View result={activeResult} />
            ) : (
              <Notice tone="warning" icon={CircleAlert}>
                后端返回中没有 {active.label} 模块结果，未渲染空盘。
              </Notice>
            )}
          </>
        ) : (
          <EmptyState tab={active} />
        )}
      </div>
    </WorkspaceShell>
  );
}

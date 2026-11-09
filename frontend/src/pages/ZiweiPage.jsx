import { useState } from "react";
import { CircleAlert, Download, LoaderCircle, Orbit } from "lucide-react";
import { evaluateCalculation } from "../lib/api";
import { downloadMarkdownFile } from "../lib/export";
import { generateStandaloneReport } from "../lib/moduleReport";
import { saveDeductionHistory } from "../lib/storage";
import { ZiweiView } from "../components/result/ZiweiView";
import { BirthProfileSection, birthPayload } from "../components/destiny/BirthProfileSection";
import { WorkspaceShell } from "../components/workspace/WorkspaceShell";

function EmptyState({ title, desc }) {
  return (
    <div className="standalone-empty" role="status">
      <Orbit size={22} />
      <strong>{title}</strong>
      <p>{desc}</p>
    </div>
  );
}

export default function ZiweiPage() {
  const [profile, setProfile] = useState({
    localDatetime: "",
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Shanghai",
    gender: "男",
    trueSolar: false,
    longitude: "",
  });
  const [ziwei, setZiwei] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const payload = birthPayload(profile);
  const profileReady = Boolean(profile.localDatetime && profile.timezone.trim());

  const changeProfile = (key, value) => {
    setProfile((current) => ({ ...current, [key]: value }));
    setZiwei(null);
    setError("");
  };

  const validateProfile = () => {
    if (!profileReady) {
      setError("请先填写公历出生日期时间与时区");
      return false;
    }
    if (profile.trueSolar && profile.longitude === "") {
      setError("开启真太阳时后必须填写出生地经度");
      return false;
    }
    return true;
  };

  const handleZiwei = async () => {
    if (!validateProfile()) return;
    setLoading(true);
    setError("");
    try {
      const response = await evaluateCalculation("ziwei", "time", payload);
      setZiwei(response.result);
      if (response?.task_id) {
        saveDeductionHistory(response.task_id, {
          scene: "ziwei",
          category: "destiny",
          question: "紫微斗数",
          input: { evaluated_at: new Date().toISOString() },
        }, response);
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <WorkspaceShell
      kicker="DESTINY · 紫微斗数"
      title="紫微斗数"
      description="以出生时刻与性别为唯一输入，排十二宫、星曜、四化与命身主星；不混入流年与本命盘。"
      badge="紫微斗数"
      sidebar={<BirthProfileSection profile={profile} onChange={changeProfile} />}
    >
      <div className="standalone-tab-body" role="tabpanel" aria-label="紫微斗数">
        {error && (
          <div className="standalone-error" role="alert">
            <CircleAlert size={16} />
            <span>{error}</span>
          </div>
        )}

        <div className="destiny-action-row">
          <div>
            <h2>紫微斗数</h2>
            <p>十二宫、星曜、四化与命身主星；只用出生时刻与性别。</p>
          </div>
          <div className="destiny-action-buttons">
            {ziwei && (
              <button type="button" className="secondary-command" onClick={() => {
                const dateStr = new Date().toISOString().slice(0, 10);
                const markdown = generateStandaloneReport(ziwei, {
                  module: "ziwei",
                  title: "紫微斗数",
                  calculatedAt: new Date().toLocaleString("zh-Cn", { hour12: false }),
                });
                downloadMarkdownFile(markdown, `天机演象_紫微斗数_${dateStr}.md`);
              }}>
                <Download size={15} />
                导出报告
              </button>
            )}
            <button
              type="button"
              className="primary-button"
              onClick={handleZiwei}
              disabled={!profileReady || loading}
            >
              {loading ? <LoaderCircle size={16} className="spin" /> : <Orbit size={16} />}
              {ziwei ? "重新排盘" : "排紫微盘"}
            </button>
          </div>
        </div>

        {ziwei ? (
          <ZiweiView result={ziwei} />
        ) : (
          <EmptyState title="尚未排紫微盘" desc="填写出生信息后，点击「排紫微盘」。" />
        )}
      </div>
    </WorkspaceShell>
  );
}

import { useState } from "react";
import { BookOpen, CalendarDays, Check, CheckCircle2, Compass, Copy, Download, FileText, GitCompareArrows, Grid3X3, Layers3, Mountain, Printer, ShieldCheck, Sparkles, Workflow } from "lucide-react";
import { generateMarkdownReport, downloadMarkdownFile, copyToClipboard } from "../lib/export";
import { findModule } from "./result/shared";
import { Overview } from "./result/Overview";
import { CalendarView } from "./result/CalendarView";
import { ZhouyiView } from "./result/ZhouyiView";
import { MeihuaView } from "./result/MeihuaView";
import { LiuyaoView } from "./result/LiuyaoView";
import { LiurenView } from "./result/LiurenView";
import { QimenView } from "./result/QimenView";
import { BaziView } from "./result/BaziView";
import { ZiweiView } from "./result/ZiweiView";
import { FengshuiView } from "./result/FengshuiView";
import { ComparisonView } from "./result/ComparisonView";
import { ExplanationView } from "./result/ExplanationView";

const TABS = [
  { id: "overview", label: "总览", icon: Layers3 },
  { id: "calendar", label: "输入与历法", icon: CalendarDays },
  { id: "zhouyi", label: "周易", icon: BookOpen },
  { id: "meihua", label: "梅花易数", icon: Compass },
  { id: "liuyao", label: "六爻", icon: Grid3X3 },
  { id: "liuren", label: "大六壬", icon: Workflow },
  { id: "qimen", label: "奇门遁甲", icon: Compass },
  { id: "bazi", label: "八字命理", icon: Sparkles },
  { id: "ziwei", label: "紫微斗数", icon: Sparkles },
  { id: "fengshui", label: "阳宅风水", icon: Mountain },
  { id: "comparison", label: "对照分析", icon: GitCompareArrows },
  { id: "explanation", label: "结论建议", icon: FileText },
];

function EmptyWorkspace() {
  return (
    <div className="empty-workspace">
      <div className="empty-symbol" aria-hidden="true">
        <span>☰</span><i>易</i><span>☷</span>
      </div>
      <p className="section-kicker">CALCULATION WORKSPACE</p>
      <h2>从一次可复核的推演开始</h2>
      <p>填写左侧时间与起卦参数。结果将依次展示历法基准、卦盘事实、体用证据和对照限制。</p>
      <div className="empty-features">
        <span><CheckCircle2 size={15} />确定性计算</span>
        <span><ShieldCheck size={15} />规则可追溯</span>
        <span><GitCompareArrows size={15} />冲突不隐藏</span>
      </div>
    </div>
  );
}

export default function ResultWorkspace({ result, context, activeTab, setActiveTab }) {
  const [copied, setCopied] = useState(false);

  if (!result) return <main className="result-workspace"><EmptyWorkspace /></main>;
  const calendar = findModule(result, "calendar");
  const zhouyi = findModule(result, "zhouyi");
  const meihua = findModule(result, "meihua");
  const liuyao = findModule(result, "liuyao");
  const liuren = findModule(result, "liuren");
  const qimen = findModule(result, "qimen");
  const bazi = findModule(result, "bazi");
  const ziwei = findModule(result, "ziwei");
  const fengshui = findModule(result, "fengshui");

  const handleCopyReport = async () => {
    const md = generateMarkdownReport(result, context);
    await copyToClipboard(md);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadReport = () => {
    const md = generateMarkdownReport(result, context);
    const dateStr = new Date().toISOString().slice(0, 10);
    const filename = `天机演象推演报告_${context?.question?.slice(0, 10) || "事项"}_${dateStr}.md`;
    downloadMarkdownFile(md, filename);
  };

  return (
    <main className="result-workspace">
      <header className="result-header">
        <div className="task-identity">
          <div className="status-dot" />
          <div><strong>{context.question}</strong><span>{result.task_id}</span></div>
        </div>
        <div className="task-meta">
          <div className="export-action-group">
            <button className="export-btn" onClick={handleCopyReport} title="复制 Markdown 研判摘要">
              {copied ? <Check size={14} className="copied-icon" /> : <Copy size={14} />}
              <span>{copied ? "已复制" : "复制报告"}</span>
            </button>
            <button className="export-btn" onClick={handleDownloadReport} title="下载 Markdown 报告文件">
              <Download size={14} />
              <span>导出报告</span>
            </button>
            <button className="export-btn" onClick={() => window.print()} title="打印或导出为 PDF 文件">
              <Printer size={14} />
              <span>打印/PDF</span>
            </button>
          </div>
          <time>{new Date(result.calculated_at).toLocaleString("zh-CN", { hour12: false })}</time>
        </div>
      </header>
      <nav className="result-tabs" aria-label="结果视图">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button key={id} aria-label={label} className={activeTab === id ? "active" : ""} onClick={() => setActiveTab(id)}>
            <Icon size={16} /><span>{label}</span>
          </button>
        ))}
      </nav>
      <div className="result-content">
        {activeTab === "overview" && (
          <Overview
            result={result}
            context={context}
            calendar={calendar}
            zhouyi={zhouyi}
            meihua={meihua}
            liuyao={liuyao}
            liuren={liuren}
            qimen={qimen}
            bazi={bazi}
            ziwei={ziwei}
            fengshui={fengshui}
            onTab={setActiveTab}
          />
        )}
        {activeTab === "calendar" && <CalendarView calendar={calendar} />}
        {activeTab === "zhouyi" && <ZhouyiView result={zhouyi} />}
        {activeTab === "meihua" && <MeihuaView result={meihua} />}
        {activeTab === "liuyao" && <LiuyaoView result={liuyao} />}
        {activeTab === "liuren" && <LiurenView result={liuren} />}
        {activeTab === "qimen" && <QimenView result={qimen} />}
        {activeTab === "bazi" && <BaziView result={bazi} calendar={calendar} />}
        {activeTab === "ziwei" && <ZiweiView result={ziwei} />}
        {activeTab === "fengshui" && <FengshuiView result={fengshui} />}
        {activeTab === "comparison" && <ComparisonView comparison={result.comparison} />}
        {activeTab === "explanation" && (
          <ExplanationView
            explanation={result.explanation}
            advisory={result.advisory}
            literature={result.literature}
            imagery={result.imagery}
            yuanHui={result.yuan_hui_yun_shi}
            interpretation={result.interpretation}
          />
        )}
      </div>
    </main>
  );
}

import { useMemo } from "react";

// 八卦符号与属性
const TRIGRAMS = {
  乾: { symbol: "☰", element: "金", nature: "天", lines: [1, 1, 1] },
  兑: { symbol: "☱", element: "金", nature: "泽", lines: [1, 1, 0] },
  离: { symbol: "☲", element: "火", nature: "火", lines: [1, 0, 1] },
  震: { symbol: "☳", element: "木", nature: "雷", lines: [1, 0, 0] },
  巽: { symbol: "☴", element: "木", nature: "风", lines: [0, 1, 1] },
  坎: { symbol: "☵", element: "水", nature: "水", lines: [0, 1, 0] },
  艮: { symbol: "☶", element: "土", nature: "山", lines: [0, 0, 1] },
  坤: { symbol: "☷", element: "土", nature: "地", lines: [0, 0, 0] },
};

const ELEMENT_COLORS = {
  金: "#c9a227",
  木: "#2d8659",
  水: "#2a6f97",
  火: "#c1440e",
  土: "#8b6914",
};

const SIX_SPIRITS = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"];
const SIX_SPIRIT_COLORS = {
  青龙: "#2d8659",
  朱雀: "#c1440e",
  勾陈: "#8b6914",
  螣蛇: "#6b4c9a",
  白虎: "#555555",
  玄武: "#2a3a5a",
};

/**
 * 卦象可视化组件。
 * 渲染六爻卦象、上下卦、动爻标记、六神排列。
 */
export default function HexagramView({ plateData, compact = false }) {
  const { hexagramName, upperTrigram, lowerTrigram, movingLines, sixSpirits, liuqin } = useMemo(() => {
    const plates = plateData?.plates || {};

    // 从梅花或六爻结果提取卦象
    let hexName = "";
    let upper = "";
    let lower = "";
    let moving = [];
    let spirits = null;
    let qin = null;

    for (const key of ["meihua", "liuyao", "zhouyi"]) {
      const plate = plates[key] || {};
      const facts = plate.facts || plate.result?.facts || {};
      const orig = facts.original || facts.original_hexagram;
      if (orig) {
        if (typeof orig === "string") {
          hexName = orig;
        } else {
          hexName = orig.name || hexName;
          upper = orig.upper || upper;
          lower = orig.lower || lower;
        }
        if (facts.moving_line) moving = [facts.moving_line];
        if (facts.moving_lines) moving = facts.moving_lines;
        if (facts.six_spirits) spirits = facts.six_spirits;
        if (facts.liuqin) qin = facts.liuqin;
        break;
      }
    }

    return {
      hexagramName: hexName,
      upperTrigram: upper,
      lowerTrigram: lower,
      movingLines: moving,
      sixSpirits: spirits,
      liuqin: qin,
    };
  }, [plateData]);

  // 组合六爻（从下到上：下卦三爻 + 上卦三爻）
  const lines = useMemo(() => {
    const lowerLines = TRIGRAMS[lowerTrigram]?.lines || [0, 0, 0];
    const upperLines = TRIGRAMS[upperTrigram]?.lines || [0, 0, 0];
    return [...lowerLines, ...upperLines]; // index 0 = 初爻(bottom), index 5 = 上爻(top)
  }, [lowerTrigram, upperTrigram]);

  if (!hexagramName && !lowerTrigram && !upperTrigram) {
    return null;
  }

  const spirits = sixSpirits && sixSpirits.length === 6 ? sixSpirits : SIX_SPIRITS;

  return (
    <div className={`hexagram-view ${compact ? "compact" : ""}`}>
      <div className="hexagram-title">
        <span className="hexagram-name">{hexagramName || "卦象"}</span>
        {(upperTrigram || lowerTrigram) && (
          <span className="hexagram-trigrams">
            {upperTrigram && <span style={{ color: ELEMENT_COLORS[TRIGRAMS[upperTrigram]?.element] }}>{TRIGRAMS[upperTrigram]?.symbol}{upperTrigram}</span>}
            <span className="trigram-sep">上</span>
            {lowerTrigram && <span style={{ color: ELEMENT_COLORS[TRIGRAMS[lowerTrigram]?.element] }}>{TRIGRAMS[lowerTrigram]?.symbol}{lowerTrigram}</span>}
            <span className="trigram-sep">下</span>
          </span>
        )}
      </div>

      <div className="hexagram-lines">
        {/* 从上爻到初爻渲染（top to bottom） */}
        {[5, 4, 3, 2, 1, 0].map((lineIdx) => {
          const isYang = lines[lineIdx] === 1;
          const isMoving = movingLines.includes(lineIdx + 1);
          const spirit = spirits[5 - lineIdx]; // 六神从初爻起配
          const qinLabel = liuqin?.[5 - lineIdx];
          return (
            <div key={lineIdx} className={`hex-line ${isYang ? "yang" : "yin"} ${isMoving ? "moving" : ""}`}>
              <span className="line-position">{["初", "二", "三", "四", "五", "上"][lineIdx]}爻</span>
              <div className="line-visual">
                {isYang ? (
                  <div className="yao-solid" />
                ) : (
                  <div className="yao-broken">
                    <div className="yao-half" />
                    <div className="yao-gap" />
                    <div className="yao-half" />
                  </div>
                )}
                {isMoving && <span className="moving-mark">○</span>}
              </div>
              {spirit && <span className="line-spirit" style={{ color: SIX_SPIRIT_COLORS[spirit] }}>{spirit}</span>}
              {qinLabel && <span className="line-liuqin">{qinLabel}</span>}
            </div>
          );
        })}
      </div>

      {movingLines.length > 0 && (
        <div className="hexagram-moving-info">
          动爻：{movingLines.map((l) => `${["初", "二", "三", "四", "五", "上"][l - 1]}爻`).join("、")}
        </div>
      )}
    </div>
  );
}

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
  const { hexagramName, upperTrigram, lowerTrigram, movingLines, sixSpirits, liuqin, bits } = useMemo(() => {
    const plates = plateData?.plates || {};

    // 同时有梅花与六爻时（auto 默认就是两者），梅花那份没有六神/六亲。
    // 此前拿到第一个有卦象的体系就 break，于是六神永远回落到默认序列，
    // 而默认序列是按「青龙起」写死的，跟真实日干推出来的不一致。
    // 现在卦名取第一个体系，六神/六亲/动爻从任一体系补齐。
    let hexName = "";
    let upper = "";
    let lower = "";
    let moving = [];
    let spirits = null;
    let qin = null;
    // 后端卦象对象是 {lines:[6], lower_trigram:{name}, upper_trigram:{name}}；
    // 早期测试用的 {upper:"乾", lower:"乾"} 只是旧结构。只认后者会让上下卦留空，
    // 六爻全部按空卦处理（TRIGRAMS[""] 取不到，退化成六条阴爻），
    // 界面就会把任何卦都画成「坤为地」。
    let bits = null;

    for (const key of ["meihua", "liuyao", "zhouyi"]) {
      const plate = plates[key] || {};
      const facts = plate.facts || plate.result?.facts || {};
      const orig = facts.original || facts.original_hexagram;
      if (orig && !hexName) {
        if (typeof orig === "string") {
          hexName = orig;
        } else {
          hexName = orig.name || hexName;
          upper = orig.upper_trigram?.name || orig.upper || upper;
          lower = orig.lower_trigram?.name || orig.lower || lower;
          if (Array.isArray(orig.lines) && orig.lines.length === 6) {
            bits = orig.lines.map((value) => (Number(value) ? 1 : 0));
          }
        }
      }
      if (!moving.length) {
        if (facts.moving_line) moving = [facts.moving_line];
        if (facts.moving_lines) moving = facts.moving_lines;
      }
      if (!spirits && facts.six_spirits?.length === 6) spirits = facts.six_spirits;
      if (!qin && facts.liuqin?.length === 6) qin = facts.liuqin;
    }

    return {
      hexagramName: hexName,
      upperTrigram: upper,
      lowerTrigram: lower,
      movingLines: moving,
      sixSpirits: spirits,
      liuqin: qin,
      bits,
    };
  }, [plateData]);

  // 组合六爻（从下到上）：优先后端给出的 lines（初爻在下标 0），
  // 没有时才按上下卦名拼。
  const lines = useMemo(() => {
    if (bits) return bits;
    const lowerLines = TRIGRAMS[lowerTrigram]?.lines || [0, 0, 0];
    const upperLines = TRIGRAMS[upperTrigram]?.lines || [0, 0, 0];
    return [...lowerLines, ...upperLines]; // index 0 = 初爻(bottom), index 5 = 上爻(top)
  }, [bits, lowerTrigram, upperTrigram]);

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
          // 六神/六亲数组与 line_chart 同序（初→上），lineIdx 0 就是初爻。
          // 此前写成 5 - lineIdx，把六神整份上下颠倒了：初爻显示的是上爻的神。
          const spirit = spirits[lineIdx];
          const qinLabel = liuqin?.[lineIdx];
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

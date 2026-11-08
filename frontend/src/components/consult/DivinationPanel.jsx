import { BookOpen, Compass, Grid3X3 } from "lucide-react";
import { LiuyaoView } from "../result/LiuyaoView";
import { MeihuaView } from "../result/MeihuaView";
import { ZhouyiView } from "../result/ZhouyiView";
import ConsultPanel from "./ConsultPanel";

const TABS = [
  {
    id: "zhouyi",
    label: "周易",
    icon: BookOpen,
    desc: "手工六爻、时间或数字起卦，查看本卦、变卦、互卦、错卦与综卦",
    emptyTitle: "尚未起周易卦",
    emptyDesc: "填写所问事项与时间、选择起卦方式后，点击「开始起卦」。",
  },
  {
    id: "meihua",
    label: "梅花易数",
    icon: Compass,
    desc: "时间或数字取数，查看上下卦、动爻与体用五行生克",
    emptyTitle: "尚未起梅花卦",
    emptyDesc: "填写所问事项与时间、选择起卦方式后，点击「开始起卦」。",
  },
  {
    id: "liuyao",
    label: "六爻",
    icon: Grid3X3,
    desc: "纳甲装卦，查看八宫、世应、六亲、六神、旬空与动爻",
    emptyTitle: "尚未排六爻盘",
    emptyDesc: "填写所问事项与时间、选择起卦方式后，点击「开始起卦」。",
  },
];

const VIEWS = { zhouyi: ZhouyiView, meihua: MeihuaView, liuyao: LiuyaoView };

export default function DivinationPanel() {
  return (
    <ConsultPanel
      kicker="DIVINATION WORKSPACE"
      title="卜筮专项"
      description="把周易、梅花易数与六爻拆成独立页签；共用所问事项与时间基准，盘面结果仍由既有引擎计算。"
      badge="周易 · 梅花 · 六爻"
      tabs={TABS}
      views={VIEWS}
      panelKicker="新建起卦"
      panelTitle="起卦参数"
      submitLabel="开始起卦"
      submitLoadingLabel="正在起卦"
    />
  );
}

import { Compass, Workflow } from "lucide-react";
import { LiurenView } from "../result/LiurenView";
import { QimenView } from "../result/QimenView";
import ConsultPanel from "./ConsultPanel";

const TABS = [
  {
    id: "qimen",
    label: "奇门遁甲",
    icon: Compass,
    desc: "时家转盘奇门，查看阴阳遁局、九宫、八门、九星与八神",
    emptyTitle: "尚未起奇门局",
    emptyDesc: "填写所问事项与起局时间后，点击「开始排盘」。",
  },
  {
    id: "liuren",
    label: "大六壬",
    icon: Workflow,
    desc: "查看月将、天地盘、四课、三传与十二天将",
    emptyTitle: "尚未起六壬课",
    emptyDesc: "填写所问事项与占时、选择起课方式后，点击「开始排盘」。",
  },
];

const VIEWS = { qimen: QimenView, liuren: LiurenView };

export default function SpacetimePanel() {
  return (
    <ConsultPanel
      kicker="SPACETIME WORKSPACE · 三式"
      title="时空盘专项"
      description="把奇门遁甲与大六壬拆成独立页签；共用所问事项、起盘时刻与时区，盘面结果仍由既有引擎计算。"
      badge="奇门 · 大六壬"
      tabs={TABS}
      views={VIEWS}
      panelKicker="新建排盘"
      panelTitle="排盘参数"
      submitLabel="开始排盘"
      submitLoadingLabel="正在排盘"
    />
  );
}

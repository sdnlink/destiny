import {
  BookOpen,
  Compass,
  Grid3X3,
  Orbit,
  Workflow,
} from "lucide-react";
import { ZhouyiView } from "../components/result/ZhouyiView";
import { MeihuaView } from "../components/result/MeihuaView";
import { LiuyaoView } from "../components/result/LiuyaoView";
import { QimenView } from "../components/result/QimenView";
import { LiurenView } from "../components/result/LiurenView";
import ConsultPanel from "../components/consult/ConsultPanel";

/**
 * 每个术数独立成路由页面，但卜筮 / 时空类共享同一套「输入 + 结果」外壳，
 * 这里用一份配置把它们映射成各自独立的页面，避免在 App 里重复 5 份近乎相同的代码。
 */
const MODULE_CONFIG = {
  zhouyi: {
    title: "周易",
    kicker: "DIVINATION · 易占",
    description:
      "以所问事项与时间为基准，手工、时间或数字起卦，查看本卦、变卦、互卦、错卦与综卦。",
    badge: "周易",
    panelKicker: "新建起卦",
    panelTitle: "起卦参数",
    submitLabel: "开始起卦",
    submitLoadingLabel: "正在起卦",
    tab: {
      id: "zhouyi",
      label: "周易",
      icon: BookOpen,
      desc: "手工、时间或数字起卦，查看本卦、变卦、互卦、错卦与综卦",
      emptyTitle: "尚未起周易卦",
      emptyDesc: "填写所问事项与时间、选择起卦方式后，点击「开始起卦」。",
    },
    View: ZhouyiView,
  },
  meihua: {
    title: "梅花易数",
    kicker: "DIVINATION · 梅花",
    description:
      "以时间或数字取数，查看上下卦、动爻与体用五行生克，附卦象类象关联。",
    badge: "梅花易数",
    panelKicker: "新建起卦",
    panelTitle: "起卦参数",
    submitLabel: "开始起卦",
    submitLoadingLabel: "正在起卦",
    tab: {
      id: "meihua",
      label: "梅花易数",
      icon: Compass,
      desc: "时间或数字取数，查看上下卦、动爻与体用五行生克",
      emptyTitle: "尚未起梅花卦",
      emptyDesc: "填写所问事项与时间、选择起卦方式后，点击「开始起卦」。",
    },
    View: MeihuaView,
  },
  liuyao: {
    title: "六爻",
    kicker: "DIVINATION · 纳甲",
    description:
      "京房纳甲装卦，查看八宫、世应、六亲、六神、旬空与动爻，可选指定用神。",
    badge: "六爻",
    panelKicker: "新建起卦",
    panelTitle: "起卦参数",
    submitLabel: "开始起卦",
    submitLoadingLabel: "正在起卦",
    tab: {
      id: "liuyao",
      label: "六爻",
      icon: Grid3X3,
      desc: "纳甲装卦，查看八宫、世应、六亲、六神、旬空与动爻",
      emptyTitle: "尚未排六爻盘",
      emptyDesc: "填写所问事项与时间、选择起卦方式后，点击「开始起卦」。",
    },
    View: LiuyaoView,
  },
  qimen: {
    title: "奇门遁甲",
    kicker: "SPACETIME · 三式",
    description: "时家转盘奇门，查看阴阳遁局、九宫、八门、九星与八神格局。",
    badge: "奇门遁甲",
    panelKicker: "新建排盘",
    panelTitle: "排盘参数",
    submitLabel: "开始排盘",
    submitLoadingLabel: "正在排盘",
    tab: {
      id: "qimen",
      label: "奇门遁甲",
      icon: Compass,
      desc: "时家转盘奇门，查看阴阳遁局、九宫、八门、九星与八神",
      emptyTitle: "尚未起奇门局",
      emptyDesc: "填写所问事项与起局时间后，点击「开始排盘」。",
    },
    View: QimenView,
  },
  liuren: {
    title: "大六壬",
    kicker: "SPACETIME · 三式",
    description: "查看月将、天地盘、四课、三传与十二天将乘神。",
    badge: "大六壬",
    panelKicker: "新建起课",
    panelTitle: "起课参数",
    submitLabel: "开始排盘",
    submitLoadingLabel: "正在排盘",
    tab: {
      id: "liuren",
      label: "大六壬",
      icon: Workflow,
      desc: "查看月将、天地盘、四课、三传与十二天将",
      emptyTitle: "尚未起六壬课",
      emptyDesc: "填写所问事项与占时、选择起课方式后，点击「开始排盘」。",
    },
    View: LiurenView,
  },
};

export default function ConsultModulePage({ moduleKey }) {
  const config = MODULE_CONFIG[moduleKey];
  if (!config) {
    return null;
  }
  return (
    <ConsultPanel
      key={moduleKey}
      kicker={config.kicker}
      title={config.title}
      description={config.description}
      badge={config.badge}
      tabs={[config.tab]}
      views={{ [config.tab.id]: config.View }}
      panelKicker={config.panelKicker}
      panelTitle={config.panelTitle}
      submitLabel={config.submitLabel}
      submitLoadingLabel={config.submitLoadingLabel}
    />
  );
}

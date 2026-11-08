import { localDateTimeValue, newCastNonce } from "./castingInput";

/** 经典推演与独立工作区共用的表单初值，避免两套默认口径。 */
export function initialForm() {
  return {
    scene: "combined",
    category: "career",
    question: "近期事项推演",
    localDatetime: localDateTimeValue(),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Shanghai",
    trueSolar: false,
    longitude: "",
    castNonce: newCastNonce(),
    yiMethod: "auto",
    lines: [7, 8, 7, 8, 7, 8],
    yiLower: "8",
    yiUpper: "8",
    yiNumbers: ["1", "2", "3"],
    meihuaMethod: "auto",
    mhUpper: "8",
    mhLower: "8",
    mhNumbers: ["1", "2", "3"],
    liuyaoMethod: "auto",
    lyFocus: "",
    lyLower: "8",
    lyUpper: "8",
    lyLines: [7, 8, 7, 8, 7, 8],
    lyCoins: [
      [2, 2, 3],
      [2, 3, 3],
      [3, 2, 2],
      [2, 2, 2],
      [3, 3, 2],
      [2, 3, 2],
    ],
    liurenMethod: "auto",
    lrNumber: "8",
    qimenMethod: "time",
    baziMethod: "time",
    baziGender: "男",
    ziweiMethod: "time",
    ziweiGender: "男",
    fsFacing: "180",
    fsMode: "single",
    fsMeasurements: ["179", "180", "181"],
    fsReference: "magnetic",
    fsDeclination: "0",
    fsError: "1",
  };
}

/** 独立工作区以某个体系为唯一场景，其余字段仍沿用同一份默认值。 */
export function systemForm(system) {
  return { ...initialForm(), scene: system };
}

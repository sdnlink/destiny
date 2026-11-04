/**
 * 表单 → 计算请求列表。此前这段逻辑埋在 App.jsx 的 700 行组件里，
 * 与后端 workflow/scheduler.py 的体系选择规则各写一份、互不校对。
 * 抽成独立模块后可单测，改动前能先看到映射变化。
 *
 * 注意：这里只负责「前端表单怎么映射成 module/method」，
 * 体系选择策略（auto 默认梅花+六爻）仍以后端 workflow/scheduler.py 为准。
 */

export function calendarPayload(form) {
  const payload = {
    local_datetime: form.localDatetime,
    timezone: form.timezone,
    use_true_solar_time: form.trueSolar,
  };
  if (form.trueSolar) payload.longitude = Number(form.longitude);
  return payload;
}

export function buildCalculations(form) {
  const calendar = calendarPayload(form);
  const auto = { ...calendar, cast_nonce: form.castNonce };
  const calculations = [{ module: "calendar", method: "analyze", input: calendar }];
  const wants = (scene) => form.scene === "combined" || form.scene === scene;

  if (wants("zhouyi")) {
    calculations.push(
      form.yiMethod === "auto"
        ? { module: "zhouyi", method: "auto", input: auto }
        : form.yiMethod === "time"
        ? { module: "zhouyi", method: "time", input: calendar }
        : form.yiMethod === "manual"
        ? { module: "zhouyi", method: "manual", input: { lines: form.lines } }
        : {
            module: "zhouyi",
            method: "numbers",
            input: { lower_number: Number(form.yiLower), upper_number: Number(form.yiUpper) },
          },
    );
  }
  if (wants("meihua")) {
    calculations.push(
      form.meihuaMethod === "auto"
        ? { module: "meihua", method: "auto", input: auto }
        : form.meihuaMethod === "time"
        ? { module: "meihua", method: "time", input: calendar }
        : {
            module: "meihua",
            method: "numbers",
            input: { upper_number: Number(form.mhUpper), lower_number: Number(form.mhLower) },
          },
    );
  }
  if (wants("liuyao")) {
    calculations.push(
      form.liuyaoMethod === "auto"
        ? { module: "liuyao", method: "auto", input: auto }
        : form.liuyaoMethod === "time"
        ? { module: "liuyao", method: "time", input: calendar }
        : {
            module: "liuyao",
            method: "numbers",
            input: { ...calendar, lower_number: Number(form.lyLower), upper_number: Number(form.lyUpper) },
          },
    );
  }
  if (wants("liuren")) {
    calculations.push(
      form.liurenMethod === "auto"
        ? { module: "liuren", method: "auto", input: auto }
        : form.liurenMethod === "time"
        ? { module: "liuren", method: "time", input: calendar }
        : { module: "liuren", method: "numbers", input: { ...calendar, number: Number(form.lrNumber) } },
    );
  }
  if (wants("qimen")) {
    calculations.push(
      form.qimenMethod === "auto"
        ? { module: "qimen", method: "auto", input: auto }
        : { module: "qimen", method: "time", input: calendar },
    );
  }
  if (wants("bazi")) {
    const gender = form.baziGender || form.ziweiGender || "男";
    calculations.push(
      form.baziMethod === "auto"
        ? { module: "bazi", method: "auto", input: { ...auto, gender } }
        : { module: "bazi", method: "time", input: { ...calendar, gender } },
    );
  }
  if (wants("ziwei")) {
    calculations.push(
      form.ziweiMethod === "auto"
        ? { module: "ziwei", method: "auto", input: { ...auto, gender: form.ziweiGender } }
        : { module: "ziwei", method: "time", input: { ...calendar, gender: form.ziweiGender } },
    );
  }
  if (form.scene === "fengshui") {
    calculations.push({
      module: "fengshui",
      method: form.fsMode === "multiple" ? "measurements" : "direction",
      input:
        form.fsMode === "multiple"
          ? {
              measurements: form.fsMeasurements.map((degree) => ({
                facing_degree: Number(degree),
                input_reference: form.fsReference,
                magnetic_declination: Number(form.fsDeclination),
                measurement_error: Number(form.fsError),
                measurement_method: "web_multi_entry",
              })),
            }
          : {
              facing_degree: Number(form.fsFacing),
              input_reference: form.fsReference,
              magnetic_declination: Number(form.fsDeclination),
              measurement_error: Number(form.fsError),
              measurement_method: "web_manual_entry",
            },
    });
  }
  return calculations;
}

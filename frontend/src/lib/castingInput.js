/**
 * 起盘输入的本地时间与随机 nonce。
 *
 * 抽到 lib 是因为它们被 WorkflowPanel 的表单提交和「设为当前时间」按钮共用，
 * 留在组件里容易被后续重构连带删掉（曾经真的被删掉，界面第一次点「交互推演」
 * 就抛 ReferenceError：localDateTimeValue is not defined，而构建阶段发现不了）。
 */

export function localDateTimeValue(date = new Date()) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

export function newCastNonce() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID().replaceAll("-", "");
  const bytes = new Uint8Array(16);
  globalThis.crypto.getRandomValues(bytes);
  return Array.from(bytes, (v) => v.toString(16).padStart(2, "0")).join("");
}

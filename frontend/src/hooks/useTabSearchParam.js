import { useCallback } from "react";
import { useSearchParams } from "react-router-dom";

/**
 * 把模块内的子页签同步到 URL 查询参数：
 *   - 每个子页都有可分享的独立 URL（如 /bazi?tab=liunian）
 *   - 刷新后仍停留在同一子页
 *   - 浏览器前进/后退可以切换子页
 *   - 非法参数回落到默认子页，不留脏 URL 状态
 *
 * 组件本身不卸载，因此各子页已算出的结果在切换时会保留。
 */
export function useTabSearchParam(param, allowedIds, defaultId) {
  const [searchParams, setSearchParams] = useSearchParams();
  const raw = searchParams.get(param);
  const active = allowedIds.includes(raw) ? raw : defaultId;
  // 用字符串键稳定回调依赖，调用方可以直接传内联数组而不必自建模块级常量
  const idsKey = allowedIds.join("|");

  const setActive = useCallback((id) => {
    if (!idsKey.split("|").includes(id)) return;
    setSearchParams((previous) => {
      const next = new URLSearchParams(previous);
      if (id === defaultId) next.delete(param);
      else next.set(param, id);
      return next;
    });
  }, [idsKey, defaultId, param, setSearchParams]);

  return [active, setActive];
}

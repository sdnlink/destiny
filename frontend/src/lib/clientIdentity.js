/**
 * 客户端标识（审计 22：会话归属）。
 *
 * 后端会话接口要求每个请求带 `X-Client-Id`，并按这个 id 的哈希做归属校验；
 * 没有它就没法区分「同一部署里的两个浏览器」。这里不做账号，只保证：
 * 同一个浏览器配置稳定拿到同一个 id，换浏览器就是另一个 id。
 *
 * 存 localStorage 而不是 sessionStorage：关掉页面再打开，历史会话仍然属于自己。
 */

const STORAGE_KEY = "tianji_client_id_v1";
const CLIENT_ID_PATTERN = /^[A-Za-z0-9_-]{16,64}$/;

let cached = null;

function randomClientId() {
  const cryptoApi = globalThis.crypto;
  if (cryptoApi?.randomUUID) return cryptoApi.randomUUID().replaceAll("-", "");
  const bytes = new Uint8Array(16);
  cryptoApi.getRandomValues(bytes);
  return Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
}

/** 取（必要时生成并持久化）本浏览器的客户端 id。 */
export function getClientId() {
  if (cached) return cached;
  try {
    const stored = globalThis.localStorage?.getItem(STORAGE_KEY);
    if (stored && CLIENT_ID_PATTERN.test(stored)) {
      cached = stored;
      return cached;
    }
  } catch {
    // 隐私模式/禁用 localStorage：退化为本次进程内 id，不阻塞使用
  }
  const generated = randomClientId();
  try {
    globalThis.localStorage?.setItem(STORAGE_KEY, generated);
  } catch {
    // 写不进去就只在内存里用，下次刷新会换一个 id（会在后端表现为「别人的会话」）
  }
  cached = generated;
  return cached;
}

/** 测试用：清掉进程内缓存，强制重新读取 localStorage。 */
export function resetClientIdCache() {
  cached = null;
}

export const CLIENT_ID_STORAGE_KEY = STORAGE_KEY;

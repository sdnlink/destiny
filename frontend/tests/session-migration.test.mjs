// 纯模块测试：与 tests/*.test.mjs 其余文件一致，走 node --test，不依赖 vitest/jsdom。
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { buildMigrationPayload, resolveCastingSource, resolveCategory } from "../src/lib/sessionMigration.js";

const fixedNonce = () => "a".repeat(32);

function historyItem(overrides = {}) {
  return {
    id: "task-1",
    timestamp: 1_760_000_000_000,
    question: "这个月能否拿到项目款",
    category: "finance",
    scene: "combined",
    calculated_at: "2026-11-05T02:00:00.000Z",
    result: {
      module_results: [
        {
          module: "calendar",
          method: "analyze",
          result: {
            input: { local_datetime: "2026-11-05T10:00:00", timezone: "Asia/Shanghai", use_true_solar_time: false },
          },
        },
      ],
    },
    ...overrides,
  };
}

describe("本地存档 → 后端会话", () => {
  it("优先用新存档显式保存的起盘时刻", () => {
    const source = resolveCastingSource(
      historyItem({ input: { local_datetime: "2026-10-01T08:00", timezone: "Asia/Tokyo", use_true_solar_time: true } }),
    );
    assert.deepEqual(source, {
      local_datetime: "2026-10-01T08:00",
      timezone: "Asia/Tokyo",
      use_true_solar_time: true,
      longitude: null,
    });
  });

  it("旧存档退回历法结果里回显的 input", () => {
    const source = resolveCastingSource(historyItem());
    assert.equal(source.local_datetime, "2026-11-05T10:00:00");
    assert.equal(source.timezone, "Asia/Shanghai");
  });

  it("既无 input 也无历法回显时退回存档时间，不抛错", () => {
    const source = resolveCastingSource(historyItem({ result: { module_results: [] } }));
    assert.match(source.local_datetime, /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/);
    assert.ok(source.timezone);
  });

  it("旧分类别名归一到后端规范键", () => {
    assert.equal(resolveCategory(historyItem({ category: "wealth" })), "finance");
    assert.equal(resolveCategory(historyItem({ category: "job" })), "career");
  });

  it("无法识别的分类降级为 other，而不是把非法值发给后端", () => {
    assert.equal(resolveCategory(historyItem({ category: "mystery" })), "other");
    assert.equal(resolveCategory(historyItem({ category: "" })), "other");
  });

  it("请求体符合 POST /v1/sessions 的契约", () => {
    const payload = buildMigrationPayload(historyItem(), { nonceFactory: fixedNonce });
    assert.equal(payload.question, "这个月能否拿到项目款");
    assert.equal(payload.category, "finance");
    assert.equal(payload.system, "auto");
    assert.equal(payload.casting_method, "time");
    assert.deepEqual(payload.casting_source, {
      local_datetime: "2026-11-05T10:00:00",
      timezone: "Asia/Shanghai",
      use_true_solar_time: false,
      longitude: null,
      cast_nonce: fixedNonce(),
    });
    assert.deepEqual(payload.user_profile, {});
  });

  it("cast_nonce 每次重建都会重新生成，不复用存档里的值", () => {
    const first = buildMigrationPayload(historyItem());
    const second = buildMigrationPayload(historyItem());
    assert.notEqual(first.casting_source.cast_nonce, second.casting_source.cast_nonce);
    assert.ok(first.casting_source.cast_nonce.length >= 16);
    assert.match(first.casting_source.cast_nonce, /^[A-Za-z0-9_-]+$/);
  });

  it("没有事由的存档明确报错，不提交空问题", () => {
    assert.throws(() => buildMigrationPayload(historyItem({ question: "   " })), /求测事由/);
  });

  it("真太阳时的经度从存档里还原，迁移后不丢修正", () => {
    const item = historyItem({
      result: {
        module_results: [
          {
            module: "calendar",
            method: "analyze",
            result: {
              input: {
                local_datetime: "2026-11-05T10:00:00",
                timezone: "Asia/Shanghai",
                use_true_solar_time: true,
                longitude: 116.4074,
              },
            },
          },
        ],
      },
    });
    const payload = buildMigrationPayload(item, { nonceFactory: fixedNonce });
    assert.equal(payload.casting_source.use_true_solar_time, true);
    assert.equal(payload.casting_source.longitude, 116.4074);
  });

  it("新存档 input 里的经度优先于历法回显", () => {
    const source = resolveCastingSource(
      historyItem({
        input: { local_datetime: "2026-11-05T10:00", timezone: "Asia/Shanghai", use_true_solar_time: true, longitude: 121.5 },
      }),
    );
    assert.equal(source.longitude, 121.5);
  });

  it("真太阳时却找不到经度时明确报错，不静默降级成标准时", () => {
    assert.throws(
      () => buildMigrationPayload(historyItem({ input: { local_datetime: "2026-11-05T10:00", use_true_solar_time: true } })),
      /缺少经度/,
    );
  });
});

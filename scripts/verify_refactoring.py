import sys, os, json, tempfile, importlib.util
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.session import create_session, freeze_snapshot, append_interaction, SessionStore
from app.interaction import generate_completion_prompt, process_reality_response, analyze_multi_party, analyze_branches, review_outcome, deep_question, angle_shift

# 直接加载 scheduler 模块，绕过 workflow/__init__.py 的级联导入
_sched_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'workflow', 'scheduler.py')
_spec = importlib.util.spec_from_file_location('workflow_scheduler', _sched_path)
_sched = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sched)
select_systems = _sched.select_systems
build_calculation_requests = _sched.build_calculation_requests

print('=== 1. 会话创建 ===')
s = create_session(question='测试事业发展')
print(f'  session_id={s.session_id}, status={s.status}')
assert s.status == 'draft'

print('=== 2. 冻结快照（铁律） ===')
s = freeze_snapshot(s, {'hexagram': '乾为天', 'moving_line': 3}, [{'module': 'meihua'}], {'q': '1'})
print(f'  status={s.status}, frozen={s.snapshot.frozen}, hash={s.snapshot.input_hash[:20]}...')
assert s.snapshot.frozen == True
assert s.status == 'casted'

print('=== 3. 铁律：重复冻结应抛异常 ===')
try:
    freeze_snapshot(s, {'hexagram': '坤为地'}, [], {'q': '2'})
    print('  FAIL: 未抛异常')
except RuntimeError as e:
    print(f'  OK: {e}')

print('=== 4. 交互后快照不变 ===')
orig_hash = s.snapshot.input_hash
orig_plate = json.dumps(s.snapshot.raw_plate, sort_keys=True)
s = append_interaction(s, 'reality_check', {'response': '符合'}, {'action': 'enter_extended'})
assert s.snapshot.input_hash == orig_hash
assert json.dumps(s.snapshot.raw_plate, sort_keys=True) == orig_plate
print(f'  OK: 交互后快照不变, interactions={len(s.interactions)}')

print('=== 5. 现实校验 ===')
r = process_reality_response(s, '部分符合', details='事业部分符合')
rt = r['response_type']
act = r['action']
has_shift = 'interpretation_shift' in r
print(f'  response_type={rt}, action={act}, shift={has_shift}')
assert r['snapshot_unchanged'] == True

r2 = process_reality_response(s, '不符合')
print(f'  不符合: options={len(r2["options"])}')
assert len(r2['options']) == 2

print('=== 6. 多方取象 ===')
mp = analyze_multi_party(s, parties=['求测人', '对方', '领导'])
print(f'  parties={len(mp["parties"])}, unchanged={mp["snapshot_unchanged"]}')
assert len(mp['parties']) == 3

print('=== 7. 分支推演 ===')
mc = analyze_branches(s, choices=['方案A继续', '方案B转型'])
print(f'  choices={len(mc["choices"])}, has_rec={"recommendation" in mc}')
assert len(mc['choices']) == 2

print('=== 8. 事后复盘 ===')
rv = review_outcome(s, '事业发展顺利，成功晋升')
print(f'  verified={len(rv["verified"])}, unverified={len(rv["unverified"])}, lessons={len(rv["lessons"])}')
assert rv['snapshot_unchanged'] == True
assert s.status == 'reviewed'

print('=== 9. 术数调度 ===')
sys1, note1 = select_systems('auto')
print(f'  auto: {sys1}')
assert 'meihua' in sys1 and 'liuyao' in sys1
sys2, _ = select_systems('qimen')
print(f'  qimen: {sys2}')
assert sys2 == ['qimen']

print('=== 10. 会话存储 ===')
with tempfile.TemporaryDirectory() as td:
    store = SessionStore(storage_dir=td)
    store.save(s)
    loaded = store.load(s.session_id)
    assert loaded is not None
    assert loaded.question == s.question
    print(f'  save/load OK, list={len(store.list_sessions())}')

print('=== 11. 深度追问 ===')
dq = deep_question(s, "动爻代表什么？用神旺衰如何？")
print(f'  detected={dq["detected_symbols"]}, has_analysis={"analysis" in dq}, unchanged={dq["snapshot_unchanged"]}')
assert dq["snapshot_unchanged"] == True
assert "analysis" in dq
assert len(dq["analysis"]) > 50

dq2 = deep_question(s, "六神青龙代表什么？")
print(f'  六神追问 detected={dq2["detected_symbols"]}')
assert "liushen" in dq2["detected_symbols"]

print('=== 12. 换角度解读 ===')
as1 = angle_shift(s, "从对方立场重新解读")
print(f'  matched={as1["matched_preset"]}, has_reinterpretation={"reinterpretation" in as1}, suggested={len(as1["suggested_angles"])}')
assert as1["snapshot_unchanged"] == True
assert as1["matched_preset"] == "对方立场"
assert "reinterpretation" in as1

as2 = angle_shift(s, "财务角度")
print(f'  财务角度 matched={as2["matched_preset"]}')
assert as2["matched_preset"] == "财务角度"

as3 = angle_shift(s, "一个自定义的特殊角度")
print(f'  自定义角度 matched={as3["matched_preset"]} (None表示未匹配预设)')

print()
print('=== 全部 12 项测试通过 ===')

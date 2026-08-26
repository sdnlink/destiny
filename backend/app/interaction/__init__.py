"""交互模块A-G。

A: 起盘前信息补全
B: 排盘后现实校验交互
C: 拓展参考资料库（内置于 workflow engine）
D: 后续交互入口（内置于 workflow engine）
E: 多方人物取象
F: 多抉择分支推演
G: 事后复盘

铁律：所有交互模块均不得修改已冻结的 session.snapshot（原始盘面）。
解读视角调整记录在 interaction.interpretation_shift 中，与原始盘面分离。
"""

from .info_completion import (
    generate_completion_prompt,
    apply_completion_answers,
    detect_missing,
)
from .reality_check import process_reality_response
from .multi_party import analyze_multi_party, detect_parties
from .multi_choice import analyze_branches
from .review import review_outcome
from .deep_question import deep_question
from .angle_shift import angle_shift

__all__ = [
    # 模块A
    "generate_completion_prompt",
    "apply_completion_answers",
    "detect_missing",
    # 模块B
    "process_reality_response",
    # 模块D
    "deep_question",
    "angle_shift",
    # 模块E
    "analyze_multi_party",
    "detect_parties",
    # 模块F
    "analyze_branches",
    # 模块G
    "review_outcome",
]

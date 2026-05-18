"""Pine → Python conversion pipeline.

v0.2.0 ships a rule-based translator for SMA crossover strategies only.
v0.2.1+ will add an LLM-backed translator (Ollama + Qwen2.5-Coder-7B)
behind the same parser/translator/runner/differ interface.
"""

from survival_alpha.converter.parser import (
    ParseError,
    SmaCrossSpec,
    parse_sma_crossover,
)
from survival_alpha.converter.translator import translate
from survival_alpha.converter.runner import DEFAULT_TV_CONFIG, run_strategy
from survival_alpha.converter.differ import TradeDiff, diff_trades

__all__ = [
    "ParseError", "SmaCrossSpec", "parse_sma_crossover",
    "translate", "run_strategy", "DEFAULT_TV_CONFIG",
    "TradeDiff", "diff_trades",
]

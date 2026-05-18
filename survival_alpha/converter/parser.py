"""Pine Script v6 pre-flight parser for SMA crossover strategies.

Only the exact pattern is accepted in v0.2.0:

    //@version=6
    strategy("<name>", ...)

    <var1> = ta.sma(close, <int>)
    <var2> = ta.sma(close, <int>)

    if ta.crossover(<fast_var>, <slow_var>)
        strategy.entry("...", strategy.long)

    if ta.crossunder(<fast_var>, <slow_var>)
        strategy.close("...")

Anything else fails with a clear ParseError. This is intentional --
v0.2.0 is a tracer bullet, not a general Pine translator.
"""

import re
from dataclasses import dataclass


class ParseError(ValueError):
    """Raised when a Pine source can't be parsed by the v0.2 gate."""


@dataclass
class SmaCrossSpec:
    """The parsed shape of a Pine SMA-crossover strategy."""
    strategy_name: str
    fast_length: int
    slow_length: int
    fast_var: str
    slow_var: str
    long_only: bool = True


# Identifiers we recognize. Anything outside this set raises an error.
_ALLOWED_TA = {"ta.sma", "ta.crossover", "ta.crossunder"}

# Pine features we explicitly reject for v0.2.0 with a friendly message.
_FORBIDDEN_KEYWORDS = (
    "request.security", "varip", "ta.atr", "ta.rsi", "ta.ema", "ta.macd",
    "ta.bb", "ta.stoch", "ta.cci", "ta.adx", "ta.obv",
    "line.new", "label.new", "box.new", "table.new",
    "array.", "matrix.", "map.",
    "strategy.short", "strategy.exit",
    "alertcondition", "alert(",
)


def parse_sma_crossover(source: str) -> SmaCrossSpec:
    """Parse Pine v6 source. Returns a SmaCrossSpec or raises ParseError."""
    if "//@version=6" not in source:
        raise ParseError(
            "Source must declare //@version=6 on its first line. "
            "Earlier Pine versions are not supported."
        )

    # Strip line comments for the rest of the analysis.
    src = re.sub(r"//.*?$", "", source, flags=re.MULTILINE)

    # Must contain a strategy(...) declaration.
    strat_match = re.search(r"strategy\s*\(", src)
    if not strat_match:
        raise ParseError(
            "Source must contain `strategy(...)`. Indicator scripts "
            "are not supported in v0.2.0."
        )
    # Extract the parenthesized args block by paren-counting (handles
    # multi-line declarations and nested parens).
    pos, depth = strat_match.end(), 1
    while pos < len(src) and depth:
        if src[pos] == "(":
            depth += 1
        elif src[pos] == ")":
            depth -= 1
        pos += 1
    if depth:
        raise ParseError("Unterminated strategy(...) call.")
    strat_args = src[strat_match.end():pos - 1]

    # Find strategy name: first quoted string anywhere in the args block.
    # Handles both `strategy("name", ...)` and `strategy(title = "name", ...)`.
    name_m = re.search(r'"([^"]*)"', strat_args)
    if not name_m:
        raise ParseError(
            "Couldn\u2019t find the strategy name. Use `strategy(\"name\", ...)` "
            "or `strategy(title=\"name\", ...)`."
        )
    strategy_name = name_m.group(1)

    # Reject forbidden constructs before deeper parsing -- gives the user
    # the most useful error message.
    _reject_forbidden(src)

    # Find exactly two ta.sma(close, N) assignments.
    sma_calls = re.findall(
        r"(\w+)\s*=\s*ta\.sma\s*\(\s*close\s*,\s*(\d+)\s*\)", src
    )
    if len(sma_calls) != 2:
        raise ParseError(
            f"Expected exactly 2 `ta.sma(close, N)` calls; found "
            f"{len(sma_calls)}. v0.2.0 supports only dual-SMA crossover."
        )

    # Order by length: smaller = fast, larger = slow.
    sma_by_len = sorted(sma_calls, key=lambda x: int(x[1]))
    if int(sma_by_len[0][1]) == int(sma_by_len[1][1]):
        raise ParseError("The two SMA lengths are identical -- not a crossover.")
    fast_var, fast_len = sma_by_len[0]
    slow_var, slow_len = sma_by_len[1]

    # Must reference ta.crossover and ta.crossunder of these exact vars.
    co_re = rf"ta\.crossover\s*\(\s*{re.escape(fast_var)}\s*,\s*{re.escape(slow_var)}\s*\)"
    cu_re = rf"ta\.crossunder\s*\(\s*{re.escape(fast_var)}\s*,\s*{re.escape(slow_var)}\s*\)"
    if not re.search(co_re, src):
        raise ParseError(
            f"Expected `ta.crossover({fast_var}, {slow_var})` (fast over slow)."
        )
    if not re.search(cu_re, src):
        raise ParseError(
            f"Expected `ta.crossunder({fast_var}, {slow_var})` (fast under slow)."
        )

    # Must have strategy.entry(..., strategy.long) and strategy.close(...).
    if not re.search(r"strategy\.entry\s*\([^)]*strategy\.long", src):
        raise ParseError(
            "Expected `strategy.entry(\"...\", strategy.long)`."
        )
    if not re.search(r"strategy\.close\s*\(", src):
        raise ParseError("Expected `strategy.close(\"...\")` to flatten on exit.")

    # Any ta.* not in the allow list?
    for m in re.finditer(r"ta\.[a-zA-Z_]\w*", src):
        if m.group() not in _ALLOWED_TA:
            raise ParseError(
                f"Unsupported Pine call '{m.group()}'. v0.2.0 allows only "
                f"{sorted(_ALLOWED_TA)}. Coming in v0.2.1+."
            )

    return SmaCrossSpec(
        strategy_name=strategy_name,
        fast_length=int(fast_len),
        slow_length=int(slow_len),
        fast_var=fast_var,
        slow_var=slow_var,
    )


def _reject_forbidden(src: str) -> None:
    for kw in _FORBIDDEN_KEYWORDS:
        if kw in src:
            raise ParseError(
                f"Unsupported Pine feature '{kw}'. "
                f"v0.2.0 ships SMA crossover only. See docs/TODO.md "
                f"for the v0.2.1+ roadmap."
            )

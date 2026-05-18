"""Rich-formatted output for `sa convert`. Brand-consistent with the tearsheet."""

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from survival_alpha.branding import AMBER, GREEN, PINK, RED, TEAL


def _kv(rows):
    t = Table.grid(padding=(0, 2))
    t.add_column(style="bold white")
    t.add_column()
    for label, value, value_style in rows:
        t.add_row(label, Text(str(value), style=value_style))
    return t


def render_parse_panel(console, spec, pine_path):
    rows = [
        ("Pine source", str(pine_path), f"bold {TEAL}"),
        ("Strategy", spec.strategy_name, "bold white"),
        ("Fast SMA", spec.fast_length, f"bold {GREEN}"),
        ("Slow SMA", spec.slow_length, f"bold {GREEN}"),
    ]
    console.print(Panel(_kv(rows), title="[bold]🔄 Pine source[/bold]",
                        title_align="left", box=box.ROUNDED,
                        border_style=TEAL, padding=(1, 2)))


def render_translation_panel(console, generated_path, n_lines):
    body = Text()
    body.append("Wrote ", style=f"dim {TEAL}")
    body.append(str(generated_path), style="bold white")
    body.append(f"  ({n_lines} lines)\n", style="dim")
    body.append("Conforms to ", style="dim")
    body.append("def strategy(data) -> pd.Series", style="bold white")
    body.append(" — drop-in ready for the survival-alpha runner.", style="dim")
    console.print(Panel(body, title="[bold]🧰 Generated Python[/bold]",
                        title_align="left", box=box.ROUNDED,
                        border_style=PINK, padding=(1, 2)))


def render_backtest_panel(console, data_path, trades, n_bars, start, end):
    total_pnl = float(trades["pnl_usd"].sum()) if len(trades) else 0.0
    win_rate = float((trades["pnl_usd"] > 0).mean() * 100) if len(trades) else 0.0
    avg_dur = float(
        (trades["exit_date"] - trades["entry_date"]).dt.days.mean()
    ) if len(trades) else 0.0
    rows = [
        ("Data", str(data_path), "bold white"),
        ("Bars", f"{n_bars:,}", "white"),
        ("Period", f"{start.date()} → {end.date()}", "white"),
        ("Trades", f"{len(trades):,}", "bold white"),
        ("Total P&L", f"${total_pnl:,.2f}",
            f"bold {GREEN}" if total_pnl >= 0 else f"bold {RED}"),
        ("Win rate", f"{win_rate:.1f}%",
            f"bold {GREEN}" if win_rate >= 50 else "bold white"),
        ("Avg duration", f"{avg_dur:.0f} days", "white"),
    ]
    console.print(Panel(_kv(rows), title="[bold]🧪 Backtest[/bold]",
                        title_align="left", box=box.ROUNDED,
                        border_style=TEAL, padding=(1, 2)))


def render_diff_panel(console, diff):
    tol_note = f" (±{diff.tolerance_days}d tolerance)" if diff.tolerance_days else ""
    if diff.is_perfect_match:
        body = Text()
        body.append("✅  ", style=GREEN)
        body.append(f"{diff.matched} / {diff.matched} trades match{tol_note}.",
                    style=f"bold {GREEN}")
        if diff.fuzzy_matched:
            body.append(
                f"\n   {len(diff.fuzzy_matched)} of those matched within tolerance, not exactly.",
                style="dim",
            )
        body.append("\n\nTranslation verified against the reference TradingView log.",
                    style="dim")
        border = GREEN
    else:
        body = Text()
        glyph = "⚠️" if diff.matched > 0 else "❌"
        color = AMBER if diff.matched > 0 else RED
        body.append(f"{glyph}  ", style=color)
        body.append(
            f"Matched {diff.matched}{tol_note}  ·  generated={diff.total_generated}  ·  reference={diff.total_reference}\n",
            style=f"bold {color}",
        )
        body.append(f"   match rate: {diff.match_pct:.1f}%\n\n", style="dim")
        if diff.gen_only:
            body.append("Python-only trades (in generated, not in reference):\n",
                        style="dim white")
            for e, x in diff.gen_only[:10]:
                body.append(f"  • {e} → {x}\n", style=RED)
            if len(diff.gen_only) > 10:
                body.append(f"  • ...and {len(diff.gen_only)-10} more\n", style="dim")
        if diff.ref_only:
            body.append("\nReference-only trades (in TV, not in generated):\n",
                        style="dim white")
            for e, x in diff.ref_only[:10]:
                body.append(f"  • {e} → {x}\n", style=AMBER)
            if len(diff.ref_only) > 10:
                body.append(f"  • ...and {len(diff.ref_only)-10} more\n", style="dim")
        body.append("\nHint: a systematic 1-bar offset usually means a fill-mode mismatch ",
                    style="dim italic")
        body.append("(TradingView's 'On bar close' vs 'Next bar open').", style="dim italic")
        border = RED if diff.matched == 0 else AMBER
    console.print(Panel(body, title="[bold]🧮 Trade diff vs reference[/bold]",
                        title_align="left", box=box.ROUNDED,
                        border_style=border, padding=(1, 2)))

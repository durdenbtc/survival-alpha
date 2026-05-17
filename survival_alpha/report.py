"""Rich-formatted CLI tearsheet output."""

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from survival_alpha.branding import (
    AMBER, GREEN, LOGO, PINK, PINK_DIM, RED, TAGLINE_LONG, TEAL, TEAL_DIM, subtitle,
)


STATUS_GLYPHS = {
    "pass": ("✅", GREEN),
    "warn": ("⚠️", AMBER),
    "fail": ("❌", RED),
}


def _fmt_pct(x, places=2):
    return f"{x*100:,.{places}f}%"


def _fmt_usd(x):
    if abs(x) >= 1_000_000:
        return f"${x/1_000_000:,.2f}M"
    if abs(x) >= 1_000:
        return f"${x/1_000:,.2f}K"
    return f"${x:,.0f}"


def _fmt_int(x):
    return f"{x:,}"


def print_brand_header(console):
    console.print(Text(LOGO, style=f"bold {TEAL}"))
    console.print(Align.center(Text(subtitle(), style=f"italic {PINK}")))
    console.print(Align.center(Text(TAGLINE_LONG, style=f"dim italic {TEAL_DIM}")))
    console.print()


def _info_panel(filename, m):
    h = Text()
    h.append("File    ", style=f"dim {TEAL}"); h.append(f"{filename}\n", style="bold white")
    h.append("Period  ", style=f"dim {TEAL}")
    h.append(f"{m['start_date'].date()} → {m['end_date'].date()}  ", style="white")
    h.append(f"({m['years']:.1f} years)\n", style="dim")
    h.append("Trades  ", style=f"dim {TEAL}")
    h.append(_fmt_int(m["n_trades"]), style="bold white")
    return Panel(h, title="[bold]📊 Tearsheet[/bold]", title_align="left",
                 box=box.ROUNDED, border_style=TEAL, padding=(1, 2))


def _kv_table(rows):
    t = Table.grid(padding=(0, 2))
    t.add_column(style="bold white")
    t.add_column(justify="right")
    for label, value, value_style in rows:
        t.add_row(label, Text(value, style=value_style))
    return t


def _perf_panel(m):
    rows = [
        ("Total return",       _fmt_pct(m["total_return"], 1), f"bold {GREEN}"),
        ("CAGR",               _fmt_pct(m["cagr"]),            f"bold {GREEN}"),
        ("Sharpe",             f"{m['sharpe']:,.2f}",          "bold white"),
        ("Sortino",            f"{m['sortino']:,.2f}",         "bold white"),
        ("Calmar",             f"{m['calmar']:,.2f}",          "bold white"),
        ("Max drawdown",       _fmt_pct(m["max_dd"]),          f"bold {RED}"),
        ("Max intra-trade DD", _fmt_pct(m["max_intra_trade_dd"]), f"bold {RED}"),
        ("Annual volatility",  _fmt_pct(m["annual_vol"]),         "white"),
        ("Time in market",     _fmt_pct(m["time_in_market"], 1), "white"),
    ]
    return Panel(_kv_table(rows), title="[bold]📈 Performance[/bold]",
                 title_align="left", box=box.ROUNDED, border_style=TEAL,
                 padding=(1, 2))


def _trade_panel(m):
    pf = m["profit_factor"]
    pf_str = "∞" if pf == float("inf") else f"{pf:,.2f}"
    rows = [
        ("Number of trades",  _fmt_int(m["n_trades"]),                  "bold white"),
        ("Win rate",          _fmt_pct(m["win_rate"], 1),               f"bold {GREEN}"),
        ("Expectancy / trade", _fmt_usd(m["expectancy_usd"]),           f"bold {GREEN}"),
        ("Profit factor",     pf_str,                                   "bold white"),
        ("Avg win",           _fmt_usd(m["avg_win_usd"]),               GREEN),
        ("Avg loss",          _fmt_usd(m["avg_loss_usd"]),              RED),
        ("Largest win",       _fmt_usd(m["largest_win_usd"]),           GREEN),
        ("Largest loss",      _fmt_usd(m["largest_loss_usd"]),          RED),
        ("Avg duration",      f"{m['avg_duration_days']:,.1f} days",    "white"),
    ]
    return Panel(_kv_table(rows), title="[bold]🎯 Trade stats[/bold]",
                 title_align="left", box=box.ROUNDED, border_style=PINK,
                 padding=(1, 2))


def _hygiene_panel(checks):
    t = Table.grid(padding=(0, 1))
    t.add_column(width=3)
    t.add_column(style="bold white", no_wrap=True)
    t.add_column(overflow="fold")
    for c in checks:
        glyph, color = STATUS_GLYPHS[c.status]
        t.add_row(glyph, c.name, Text(c.message, style=color))
    # Border color reflects worst status
    worst = "pass"
    statuses = {c.status for c in checks}
    if "fail" in statuses:
        worst = "fail"
    elif "warn" in statuses:
        worst = "warn"
    border = {"pass": GREEN, "warn": AMBER, "fail": RED}[worst]
    return Panel(t, title="[bold]🔍 Hygiene checks[/bold]",
                 title_align="left", box=box.ROUNDED, border_style=border,
                 padding=(1, 2))


def _footer(console):
    console.print()
    note = Text()
    note.append("Note  ", style=f"dim {TEAL}")
    note.append(
        "Sharpe/Sortino derived from a pro-rata daily equity curve. "
        "Upgrade to Mode 2 (signal + price series) for higher-fidelity "
        "metrics including true repaint detection.\n",
        style="dim italic",
    )
    console.print(note)
    console.print(Rule(style=f"dim {TEAL_DIM}"))
    links = Text(justify="center")
    links.append("durdenbtc.com", style=f"bold {TEAL}")
    links.append("   ·   ", style="dim")
    links.append("durdenbtc.substack.com", style=f"bold {PINK}")
    links.append("   ·   ", style="dim")
    links.append("@DurdenBTC", style=f"bold {TEAL}")
    console.print(links)


def _side_by_side(left, right):
    g = Table.grid(expand=True, padding=(0, 1))
    g.add_column(ratio=1)
    g.add_column(ratio=1)
    g.add_row(left, right)
    return g


def print_tearsheet(filename, trades, metrics, checks):
    console = Console()
    print_brand_header(console)
    console.print(_info_panel(filename, metrics))
    console.print(_side_by_side(_perf_panel(metrics), _trade_panel(metrics)))
    console.print(_hygiene_panel(checks))
    _footer(console)

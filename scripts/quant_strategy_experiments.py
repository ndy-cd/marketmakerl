#!/usr/bin/env python3
import argparse
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

import pandas as pd

from src.backtesting.backtest_engine import BacktestEngine
from src.data.real_market_data import RealMarketDataClient
from src.models.avellaneda_stoikov import AvellanedaStoikovModel


@dataclass
class StrategySpec:
    name: str
    family: str
    backtest_mode: str
    risk_aversion: float
    time_horizon: float
    max_inventory: int
    spread_constraint_bps: float
    transaction_fee: float
    min_edge_bps: float
    cooldown_steps: int
    inventory_soft_limit_ratio: float
    target_volatility: float
    vol_spread_scale: float
    soft_drawdown_risk_pct: float
    hard_drawdown_stop_pct: float
    adverse_return_bps: float
    risk_off_inventory_scale: float


@dataclass
class ExperimentResult:
    strategy: str
    family: str
    variant: str
    budget: float
    total_pnl: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    cvar_95_pct: float
    ulcer_index: float
    profit_factor: float
    positive_return_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    n_trades: float
    pass_rate: float
    hard_fail_windows: int
    robustness_score: float
    gate_pass: bool


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Quant strategy experiments with robust risk ranking")
    p.add_argument("--exchange", default="binance")
    p.add_argument("--symbol", default="BTC/USDT")
    p.add_argument("--timeframe", default="15m")
    p.add_argument("--days", type=int, default=60)
    p.add_argument("--batch-limit", type=int, default=1000)
    p.add_argument("--window-days", type=int, default=7)
    p.add_argument("--max-windows", type=int, default=6)
    p.add_argument("--budgets", default="5000,10000,15000")
    p.add_argument("--variants", default="conservative,balanced,adaptive")
    p.add_argument("--seeds", default="42,99")
    p.add_argument("--drawdown-fail-pct", type=float, default=0.40)
    p.add_argument("--min-pass-rate", type=float, default=0.65)
    p.add_argument("--min-sortino", type=float, default=0.20)
    p.add_argument("--max-cvar95-pct", type=float, default=0.03)
    p.add_argument("--tail-quantile", type=float, default=0.05)
    p.add_argument("--output-dir", default="artifacts/quant_experiments")
    return p.parse_args()


def parse_floats(raw: str) -> List[float]:
    out = []
    for t in raw.split(","):
        t = t.strip()
        if not t:
            continue
        v = float(t)
        if v > 0:
            out.append(v)
    return sorted(set(out))


def parse_ints(raw: str) -> List[int]:
    out = []
    for t in raw.split(","):
        t = t.strip()
        if not t:
            continue
        out.append(int(t))
    return sorted(set(out))


def parse_variants(raw: str) -> List[str]:
    return [v.strip() for v in raw.split(",") if v.strip()]


def fetch_klines(exchange: str, symbol: str, timeframe: str, days: int, batch_limit: int) -> pd.DataFrame:
    client = RealMarketDataClient(exchange_id=exchange, market_type="spot")
    now = datetime.now(timezone.utc)
    since_dt = now - timedelta(days=days)
    since_ms = int(since_dt.timestamp() * 1000)
    until_ms = int(now.timestamp() * 1000)

    frames: List[pd.DataFrame] = []
    cursor = since_ms
    while cursor < until_ms:
        batch = client.fetch_klines(symbol=symbol, timeframe=timeframe, since=cursor, limit=batch_limit)
        if batch.empty:
            break
        frames.append(batch)
        last_ts_ms = int(batch["timestamp"].iloc[-1].timestamp() * 1000)
        nxt = last_ts_ms + 1
        if nxt <= cursor:
            break
        cursor = nxt
        if len(batch) < batch_limit:
            break

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["timestamp"]).sort_values("timestamp")
    return df.reset_index(drop=True)


def split_windows(df: pd.DataFrame, window_days: int, max_windows: int) -> List[pd.DataFrame]:
    if df.empty:
        return []
    start = df["timestamp"].min()
    end = df["timestamp"].max()
    out = []
    cursor = start
    while cursor < end:
        right = cursor + pd.Timedelta(days=window_days)
        w = df[(df["timestamp"] >= cursor) & (df["timestamp"] < right)].copy()
        if len(w) >= 200:
            out.append(w)
        cursor = right
    if max_windows > 0:
        out = out[-max_windows:]
    return out


def build_base_specs() -> List[StrategySpec]:
    return [
        StrategySpec("defensive_core", "inventory_defensive", "standard", 1.8, 0.5, 4, 40.0, 0.0002, 2.5, 4, 0.40, 0.0032, 1.5, 0.14, 0.40, 12.0, 0.35),
        StrategySpec("inventory_tight", "inventory_tight", "standard", 2.0, 0.5, 3, 42.0, 0.0002, 2.8, 5, 0.35, 0.0030, 1.6, 0.13, 0.40, 10.0, 0.30),
        StrategySpec("spread_capture", "spread_capture", "standard", 1.4, 0.75, 5, 34.0, 0.0002, 2.2, 3, 0.45, 0.0038, 1.3, 0.16, 0.40, 14.0, 0.40),
        StrategySpec("trend_shield", "trend_shield", "standard", 1.6, 0.75, 4, 39.0, 0.0002, 2.4, 4, 0.40, 0.0034, 1.5, 0.15, 0.40, 11.0, 0.33),
        StrategySpec("volatility_brake", "volatility_brake", "standard", 1.9, 0.50, 3, 45.0, 0.0002, 3.0, 5, 0.35, 0.0029, 1.8, 0.12, 0.40, 9.0, 0.28),
        StrategySpec("enhanced_signal_guarded", "enhanced_signal_guarded", "enhanced", 0.9, 0.75, 5, 36.0, 0.0002, 2.3, 4, 0.45, 0.0035, 1.4, 0.15, 0.40, 13.0, 0.38),
    ]


def apply_variant(spec: StrategySpec, variant: str) -> StrategySpec:
    if variant == "conservative":
        return StrategySpec(
            name=f"{spec.name}__{variant}",
            family=spec.family,
            backtest_mode=spec.backtest_mode,
            risk_aversion=spec.risk_aversion + 0.2,
            time_horizon=spec.time_horizon,
            max_inventory=max(2, spec.max_inventory - 1),
            spread_constraint_bps=spec.spread_constraint_bps + 4.0,
            transaction_fee=spec.transaction_fee,
            min_edge_bps=spec.min_edge_bps + 0.4,
            cooldown_steps=spec.cooldown_steps + 1,
            inventory_soft_limit_ratio=max(0.25, spec.inventory_soft_limit_ratio - 0.05),
            target_volatility=spec.target_volatility,
            vol_spread_scale=spec.vol_spread_scale + 0.2,
            soft_drawdown_risk_pct=max(0.08, spec.soft_drawdown_risk_pct - 0.01),
            hard_drawdown_stop_pct=spec.hard_drawdown_stop_pct,
            adverse_return_bps=max(6.0, spec.adverse_return_bps - 1.0),
            risk_off_inventory_scale=max(0.2, spec.risk_off_inventory_scale - 0.05),
        )
    if variant == "adaptive":
        return StrategySpec(
            name=f"{spec.name}__{variant}",
            family=spec.family,
            backtest_mode=spec.backtest_mode,
            risk_aversion=max(0.6, spec.risk_aversion - 0.15),
            time_horizon=spec.time_horizon,
            max_inventory=spec.max_inventory + 1,
            spread_constraint_bps=max(18.0, spec.spread_constraint_bps - 2.0),
            transaction_fee=spec.transaction_fee,
            min_edge_bps=max(1.2, spec.min_edge_bps - 0.2),
            cooldown_steps=max(1, spec.cooldown_steps - 1),
            inventory_soft_limit_ratio=min(0.6, spec.inventory_soft_limit_ratio + 0.05),
            target_volatility=spec.target_volatility,
            vol_spread_scale=max(1.0, spec.vol_spread_scale - 0.1),
            soft_drawdown_risk_pct=min(0.20, spec.soft_drawdown_risk_pct + 0.01),
            hard_drawdown_stop_pct=spec.hard_drawdown_stop_pct,
            adverse_return_bps=spec.adverse_return_bps + 1.0,
            risk_off_inventory_scale=min(0.6, spec.risk_off_inventory_scale + 0.04),
        )

    return StrategySpec(
        name=f"{spec.name}__balanced",
        family=spec.family,
        backtest_mode=spec.backtest_mode,
        risk_aversion=spec.risk_aversion,
        time_horizon=spec.time_horizon,
        max_inventory=spec.max_inventory,
        spread_constraint_bps=spec.spread_constraint_bps,
        transaction_fee=spec.transaction_fee,
        min_edge_bps=spec.min_edge_bps,
        cooldown_steps=spec.cooldown_steps,
        inventory_soft_limit_ratio=spec.inventory_soft_limit_ratio,
        target_volatility=spec.target_volatility,
        vol_spread_scale=spec.vol_spread_scale,
        soft_drawdown_risk_pct=spec.soft_drawdown_risk_pct,
        hard_drawdown_stop_pct=spec.hard_drawdown_stop_pct,
        adverse_return_bps=spec.adverse_return_bps,
        risk_off_inventory_scale=spec.risk_off_inventory_scale,
    )


def build_specs(variants: List[str]) -> List[StrategySpec]:
    specs = []
    for base in build_base_specs():
        for variant in variants:
            specs.append(apply_variant(base, variant))
    return specs


def prep_data(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["returns"] = data["mid_price"].pct_change()
    data["volatility"] = data["returns"].rolling(window=20).std().fillna(0.01)
    return data.set_index("timestamp")


def run_single(data: pd.DataFrame, spec: StrategySpec, budget: float, seed: int) -> Dict:
    model = AvellanedaStoikovModel(risk_aversion=spec.risk_aversion, time_horizon=spec.time_horizon)
    engine = BacktestEngine(
        market_data=data,
        initial_capital=budget,
        transaction_fee=spec.transaction_fee,
        random_seed=seed,
        min_edge_bps=spec.min_edge_bps,
        cooldown_steps=spec.cooldown_steps,
    )
    params = {
        "spread_constraint_bps": spec.spread_constraint_bps,
        "min_edge_bps": spec.min_edge_bps,
        "cooldown_steps": spec.cooldown_steps,
        "inventory_soft_limit_ratio": spec.inventory_soft_limit_ratio,
        "target_volatility": spec.target_volatility,
        "vol_spread_scale": spec.vol_spread_scale,
        "soft_drawdown_risk_pct": spec.soft_drawdown_risk_pct,
        "hard_drawdown_stop_pct": spec.hard_drawdown_stop_pct,
        "adverse_return_bps": spec.adverse_return_bps,
        "risk_off_inventory_scale": spec.risk_off_inventory_scale,
    }
    if spec.backtest_mode == "enhanced":
        return engine.run_backtest_enhanced(
            model=model,
            params=params,
            max_inventory=spec.max_inventory,
            volatility_window=20,
            use_signals=True,
        )
    return engine.run_backtest(
        model=model,
        params=params,
        max_inventory=spec.max_inventory,
        volatility_window=20,
    )


def _safe_float(value: float) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        if math.isnan(value) or math.isinf(value):
            return 0.0
    return float(value)


def compute_risk_stats(run: Dict, budget: float, tail_q: float) -> Dict[str, float]:
    positions = pd.DataFrame(run.get("positions", []))
    if positions.empty or "total_value" not in positions.columns:
        return {
            "sortino_ratio": 0.0,
            "calmar_ratio": 0.0,
            "cvar_95_pct": 0.0,
            "ulcer_index": 0.0,
            "profit_factor": 0.0,
            "positive_return_ratio": 0.0,
        }

    equity = positions["total_value"].astype(float)
    returns = equity.pct_change().replace([float("inf"), float("-inf")], 0.0).fillna(0.0)

    mean_ret = _safe_float(returns.mean())
    downside = returns[returns < 0]
    downside_std = _safe_float(downside.std(ddof=0))
    sortino = (mean_ret / downside_std) * math.sqrt(252.0) if downside_std > 1e-12 else 0.0

    peak = equity.cummax().replace(0, 1e-9)
    dd_pct_series = (peak - equity) / peak
    max_dd_pct = _safe_float(dd_pct_series.max())
    ulcer = math.sqrt(_safe_float((dd_pct_series.pow(2)).mean()))

    total_pnl = _safe_float(run.get("metrics", {}).get("total_pnl", 0.0))
    total_return = total_pnl / max(1e-9, budget)
    calmar = total_return / max(1e-9, max_dd_pct) if max_dd_pct > 1e-9 else 0.0

    q = max(0.001, min(0.20, tail_q))
    left_tail = returns[returns <= returns.quantile(q)]
    cvar95 = -_safe_float(left_tail.mean()) if not left_tail.empty else 0.0

    pnl_steps = equity.diff().fillna(0.0)
    gross_profit = _safe_float(pnl_steps[pnl_steps > 0].sum())
    gross_loss = -_safe_float(pnl_steps[pnl_steps < 0].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 1e-9 else 0.0

    positive_return_ratio = _safe_float((returns > 0).mean())

    return {
        "sortino_ratio": _safe_float(sortino),
        "calmar_ratio": _safe_float(calmar),
        "cvar_95_pct": _safe_float(max(0.0, cvar95)),
        "ulcer_index": _safe_float(max(0.0, ulcer)),
        "profit_factor": _safe_float(max(0.0, profit_factor)),
        "positive_return_ratio": _safe_float(max(0.0, positive_return_ratio)),
    }


def evaluate(args: argparse.Namespace, df_raw: pd.DataFrame) -> List[ExperimentResult]:
    variants = parse_variants(args.variants)
    specs = build_specs(variants)
    budgets = parse_floats(args.budgets)
    seeds = parse_ints(args.seeds)
    windows = split_windows(df_raw, args.window_days, args.max_windows)

    results: List[ExperimentResult] = []

    for budget in budgets:
        for spec in specs:
            print(f"[quant] strategy={spec.name} budget={budget:.0f} seeds={seeds}", flush=True)

            full_runs = [run_single(prep_data(df_raw), spec, budget, seed) for seed in seeds]
            full_metrics = [r.get("metrics", {}) for r in full_runs]
            full_risk = [compute_risk_stats(r, budget, args.tail_quantile) for r in full_runs]

            pass_windows = 0
            hard_fails = 0
            for w in windows:
                m = run_single(prep_data(w), spec, budget, seeds[0])
                wm = m.get("metrics", {})
                wr = compute_risk_stats(m, budget, args.tail_quantile)
                dd_pct = _safe_float(wm.get("max_drawdown", 0.0)) / max(1e-9, budget)
                pnl = _safe_float(wm.get("total_pnl", 0.0))
                sortino = wr["sortino_ratio"]
                cvar95 = wr["cvar_95_pct"]
                if dd_pct <= args.drawdown_fail_pct and pnl >= 0 and sortino >= args.min_sortino and cvar95 <= args.max_cvar95_pct:
                    pass_windows += 1
                if dd_pct > args.drawdown_fail_pct:
                    hard_fails += 1

            pass_rate = (pass_windows / len(windows)) if windows else 0.0

            total_pnl = _safe_float(sum(_safe_float(m.get("total_pnl", 0.0)) for m in full_metrics) / max(1, len(full_metrics)))
            sharpe = _safe_float(sum(_safe_float(m.get("sharpe_ratio", 0.0)) for m in full_metrics) / max(1, len(full_metrics)))
            max_dd = _safe_float(sum(_safe_float(m.get("max_drawdown", 0.0)) for m in full_metrics) / max(1, len(full_metrics)))
            dd_pct = max_dd / max(1e-9, budget)
            n_trades = _safe_float(sum(_safe_float(m.get("n_trades", 0.0)) for m in full_metrics) / max(1, len(full_metrics)))

            sortino = _safe_float(sum(r["sortino_ratio"] for r in full_risk) / max(1, len(full_risk)))
            calmar = _safe_float(sum(r["calmar_ratio"] for r in full_risk) / max(1, len(full_risk)))
            cvar95 = _safe_float(sum(r["cvar_95_pct"] for r in full_risk) / max(1, len(full_risk)))
            ulcer = _safe_float(sum(r["ulcer_index"] for r in full_risk) / max(1, len(full_risk)))
            profit_factor = _safe_float(sum(r["profit_factor"] for r in full_risk) / max(1, len(full_risk)))
            pos_ratio = _safe_float(sum(r["positive_return_ratio"] for r in full_risk) / max(1, len(full_risk)))

            gate_pass = bool(
                total_pnl > 0
                and pass_rate >= args.min_pass_rate
                and hard_fails == 0
                and dd_pct <= args.drawdown_fail_pct
                and sortino >= args.min_sortino
                and cvar95 <= args.max_cvar95_pct
            )

            calmar_capped = max(-2.0, min(8.0, calmar))
            sharpe_capped = max(-2.0, min(8.0, sharpe))
            sortino_capped = max(-2.0, min(10.0, sortino))
            profit_factor_capped = max(0.0, min(4.0, profit_factor))

            robustness = (
                (1.2 * sharpe_capped)
                + (1.8 * sortino_capped)
                + (1.0 * calmar_capped)
                + (1.8 * pass_rate)
                + (0.8 * pos_ratio)
                + (0.6 * profit_factor_capped)
                + (total_pnl / max(1.0, budget))
                - (4.0 * dd_pct)
                - (8.0 * cvar95)
                - (3.0 * ulcer)
                - (2.5 * hard_fails)
            )

            base_name, _, variant = spec.name.partition("__")
            results.append(
                ExperimentResult(
                    strategy=spec.name,
                    family=spec.family,
                    variant=variant or "balanced",
                    budget=budget,
                    total_pnl=total_pnl,
                    sharpe_ratio=sharpe,
                    sortino_ratio=sortino,
                    calmar_ratio=calmar,
                    cvar_95_pct=cvar95,
                    ulcer_index=ulcer,
                    profit_factor=profit_factor,
                    positive_return_ratio=pos_ratio,
                    max_drawdown=max_dd,
                    max_drawdown_pct=dd_pct,
                    n_trades=n_trades,
                    pass_rate=pass_rate,
                    hard_fail_windows=hard_fails,
                    robustness_score=_safe_float(robustness),
                    gate_pass=gate_pass,
                )
            )
    return results


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    raw = fetch_klines(args.exchange, args.symbol, args.timeframe, args.days, args.batch_limit)
    if raw.empty:
        raise SystemExit("No data fetched")

    results = evaluate(args, raw)
    df = pd.DataFrame([asdict(r) for r in results]).sort_values("robustness_score", ascending=False)

    passed = df[df["gate_pass"] == True].copy()  # noqa: E712
    recommended = (passed.iloc[0] if not passed.empty else df.iloc[0]).to_dict()

    known_strategy_families = [
        "inventory_defensive",
        "trend_shield",
        "volatility_brake",
        "spread_capture",
        "enhanced_signal_guarded",
        "inventory_tight",
        "conservative_mm",
        "balanced_mm",
        "cross_exchange_arb",
        "latency_arb",
        "options_hedged_mm",
        "funding_basis_mm",
    ]
    tested_families = sorted(set(df["family"].tolist()))
    untested_families = [x for x in known_strategy_families if x not in tested_families]

    report = {
        "meta": {
            "exchange": args.exchange,
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "days": args.days,
            "window_days": args.window_days,
            "max_windows": args.max_windows,
            "budgets": parse_floats(args.budgets),
            "variants": parse_variants(args.variants),
            "seeds": parse_ints(args.seeds),
            "rows": int(len(raw)),
            "strategies": sorted(set(df["strategy"].tolist())),
            "experiment_cases": int(len(df)),
        },
        "recommendation": recommended,
        "coverage": {
            "known_families_total": len(known_strategy_families),
            "tested_families_count": len(tested_families),
            "coverage_pct": (len(tested_families) / len(known_strategy_families)) * 100.0,
            "tested_families": tested_families,
            "untested_families": untested_families,
            "note": "MVP paper phase focuses on market-making families; non-MM families remain future work.",
        },
        "gates": {
            "drawdown_fail_pct": args.drawdown_fail_pct,
            "min_pass_rate": args.min_pass_rate,
            "min_sortino": args.min_sortino,
            "max_cvar95_pct": args.max_cvar95_pct,
        },
        "gate_pass_count": int(df["gate_pass"].sum()),
        "total_cases": int(len(df)),
        "top_10": df.head(10).to_dict(orient="records"),
    }

    csv_path = out_dir / f"{stamp}_quant_experiments.csv"
    json_path = out_dir / f"{stamp}_quant_experiments.json"
    df.to_csv(csv_path, index=False)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps({**report, "files": {"csv": str(csv_path), "report": str(json_path)}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

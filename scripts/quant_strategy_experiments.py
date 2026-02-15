#!/usr/bin/env python3
import argparse
import json
import math
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Set

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
    total_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    cvar_95_pct: float
    ulcer_index: float
    profit_factor: float
    positive_return_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    max_drawdown_pct_min: float
    max_drawdown_pct_mean: float
    max_drawdown_pct_full_max: float
    max_drawdown_pct_window_max: float
    worst_seed_return_pct: float
    best_seed_return_pct: float
    seed_return_std_pct: float
    worst_seed_drawdown_pct: float
    seed_drawdown_std_pct: float
    n_trades: float
    fill_ratio: float
    execution_cost: float
    execution_cost_bps: float
    slippage_cost: float
    latency_cost: float
    impact_cost: float
    adverse_selection_cost: float
    realized_edge_bps: float
    execution_quality_score: float
    pass_rate: float
    hard_fail_windows: int
    robustness_score: float
    gate_pass: bool


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Quant strategy experiments with robust risk ranking")
    p.add_argument("--exchange", default="binance")
    p.add_argument("--symbol", default="BTC/USDT")
    p.add_argument("--timeframe", default="1m")
    p.add_argument("--days", type=int, default=60)
    p.add_argument("--batch-limit", type=int, default=1000)
    p.add_argument("--window-days", type=int, default=7)
    p.add_argument("--max-windows", type=int, default=6)
    p.add_argument("--budgets", default="5000,10000,15000")
    p.add_argument("--variants", default="conservative,balanced,adaptive")
    p.add_argument("--variant-mode", choices=["basic", "expanded"], default="basic")
    p.add_argument("--profiles-per-family", type=int, default=3)
    p.add_argument("--profile-seed", type=int, default=42)
    p.add_argument("--include-families", default="")
    p.add_argument("--include-strategies", default="")
    p.add_argument("--include-strategies-file", default="")
    p.add_argument("--seeds", default="42,99")
    p.add_argument("--drawdown-fail-pct", type=float, default=0.10)
    p.add_argument("--min-pass-rate", type=float, default=0.65)
    p.add_argument("--min-sortino", type=float, default=0.20)
    p.add_argument("--max-cvar95-pct", type=float, default=0.03)
    p.add_argument("--max-total-return-pct", type=float, default=1.0)
    p.add_argument("--min-worst-seed-return-pct", type=float, default=-0.10)
    p.add_argument("--max-worst-seed-drawdown-pct", type=float, default=0.05)
    p.add_argument("--min-fill-ratio", type=float, default=0.10)
    p.add_argument("--max-execution-cost-bps", type=float, default=12.0)
    p.add_argument("--base-slippage-bps", type=float, default=1.2)
    p.add_argument("--slippage-volatility-scale", type=float, default=0.025)
    p.add_argument("--market-impact-bps", type=float, default=0.8)
    p.add_argument("--latency-ms", type=float, default=80.0)
    p.add_argument("--latency-penalty-bps-per-100ms", type=float, default=0.12)
    p.add_argument("--adverse-selection-bps", type=float, default=0.4)
    p.add_argument("--fill-probability-floor", type=float, default=0.01)
    p.add_argument("--fill-probability-ceiling", type=float, default=0.95)
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


def parse_tokens(raw: str) -> List[str]:
    return [t.strip() for t in raw.split(",") if t.strip()]


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


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def filter_base_specs(base_specs: List[StrategySpec], include_families: List[str]) -> List[StrategySpec]:
    if not include_families:
        return base_specs
    keep: Set[str] = set(include_families)
    return [spec for spec in base_specs if spec.name in keep or spec.family in keep]


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


def build_expanded_specs(base_specs: List[StrategySpec], profiles_per_family: int, seed: int) -> List[StrategySpec]:
    profiles = max(1, profiles_per_family)
    rng = random.Random(seed)
    specs: List[StrategySpec] = []

    for base in base_specs:
        for idx in range(profiles):
            risk_aversion = _clamp(base.risk_aversion * rng.uniform(0.75, 1.35), 0.5, 3.5)
            time_horizon = _clamp(base.time_horizon * rng.uniform(0.8, 1.2), 0.3, 1.2)
            max_inventory = int(_clamp(round(base.max_inventory + rng.randint(-2, 2)), 2, 8))
            spread_constraint_bps = _clamp(base.spread_constraint_bps * rng.uniform(0.75, 1.25), 18.0, 60.0)
            min_edge_bps = _clamp(base.min_edge_bps * rng.uniform(0.7, 1.4), 1.0, 6.0)
            cooldown_steps = int(_clamp(round(base.cooldown_steps + rng.randint(-2, 2)), 1, 8))
            inventory_soft_limit_ratio = _clamp(base.inventory_soft_limit_ratio + rng.uniform(-0.12, 0.12), 0.2, 0.7)
            target_volatility = _clamp(base.target_volatility * rng.uniform(0.75, 1.25), 0.0015, 0.0080)
            vol_spread_scale = _clamp(base.vol_spread_scale * rng.uniform(0.75, 1.35), 0.8, 2.4)
            soft_drawdown_risk_pct = _clamp(base.soft_drawdown_risk_pct * rng.uniform(0.8, 1.2), 0.08, 0.22)
            adverse_return_bps = _clamp(base.adverse_return_bps * rng.uniform(0.7, 1.4), 6.0, 20.0)
            risk_off_inventory_scale = _clamp(base.risk_off_inventory_scale * rng.uniform(0.7, 1.3), 0.2, 0.7)

            specs.append(
                StrategySpec(
                    name=f"{base.name}__grid{idx:03d}",
                    family=base.family,
                    backtest_mode=base.backtest_mode,
                    risk_aversion=risk_aversion,
                    time_horizon=time_horizon,
                    max_inventory=max_inventory,
                    spread_constraint_bps=spread_constraint_bps,
                    transaction_fee=base.transaction_fee,
                    min_edge_bps=min_edge_bps,
                    cooldown_steps=cooldown_steps,
                    inventory_soft_limit_ratio=inventory_soft_limit_ratio,
                    target_volatility=target_volatility,
                    vol_spread_scale=vol_spread_scale,
                    soft_drawdown_risk_pct=soft_drawdown_risk_pct,
                    hard_drawdown_stop_pct=base.hard_drawdown_stop_pct,
                    adverse_return_bps=adverse_return_bps,
                    risk_off_inventory_scale=risk_off_inventory_scale,
                )
            )
    return specs


def load_include_strategies(args: argparse.Namespace) -> Set[str]:
    include: Set[str] = set(parse_tokens(args.include_strategies))
    if args.include_strategies_file:
        p = Path(args.include_strategies_file)
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                token = line.strip()
                if token:
                    include.add(token)
    return include


def prep_data(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["returns"] = data["mid_price"].pct_change()
    data["volatility"] = data["returns"].rolling(window=20).std().fillna(0.01)
    return data.set_index("timestamp")


def summarize_data_profile(df: pd.DataFrame) -> Dict[str, float]:
    if df.empty or "timestamp" not in df.columns:
        return {
            "rows": 0,
            "start_utc": "",
            "end_utc": "",
            "interval_seconds_median": 0.0,
            "interval_seconds_p05": 0.0,
            "interval_seconds_p95": 0.0,
        }

    ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce").dropna().sort_values()
    if ts.empty:
        return {
            "rows": 0,
            "start_utc": "",
            "end_utc": "",
            "interval_seconds_median": 0.0,
            "interval_seconds_p05": 0.0,
            "interval_seconds_p95": 0.0,
        }

    deltas = ts.diff().dt.total_seconds().dropna()
    if deltas.empty:
        med = p05 = p95 = 0.0
    else:
        med = _safe_float(deltas.median())
        p05 = _safe_float(deltas.quantile(0.05))
        p95 = _safe_float(deltas.quantile(0.95))

    return {
        "rows": int(len(ts)),
        "start_utc": ts.iloc[0].isoformat(),
        "end_utc": ts.iloc[-1].isoformat(),
        "interval_seconds_median": med,
        "interval_seconds_p05": p05,
        "interval_seconds_p95": p95,
    }


def run_single(
    data: pd.DataFrame,
    spec: StrategySpec,
    budget: float,
    seed: int,
    execution_cfg: Dict[str, float],
) -> Dict:
    model = AvellanedaStoikovModel(risk_aversion=spec.risk_aversion, time_horizon=spec.time_horizon)
    engine = BacktestEngine(
        market_data=data,
        initial_capital=budget,
        transaction_fee=spec.transaction_fee,
        random_seed=seed,
        min_edge_bps=spec.min_edge_bps,
        cooldown_steps=spec.cooldown_steps,
        base_slippage_bps=execution_cfg["base_slippage_bps"],
        slippage_volatility_scale=execution_cfg["slippage_volatility_scale"],
        market_impact_bps=execution_cfg["market_impact_bps"],
        latency_ms=execution_cfg["latency_ms"],
        latency_penalty_bps_per_100ms=execution_cfg["latency_penalty_bps_per_100ms"],
        adverse_selection_bps=execution_cfg["adverse_selection_bps"],
        fill_probability_floor=execution_cfg["fill_probability_floor"],
        fill_probability_ceiling=execution_cfg["fill_probability_ceiling"],
    )
    median_mid = float(data["mid_price"].median()) if "mid_price" in data.columns else 1.0
    median_mid = max(1e-9, median_mid)
    min_order_qty = max(1e-6, (budget * 0.005) / median_mid)
    max_order_qty = max(min_order_qty, (budget * 0.03) / median_mid)

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
        "order_notional_pct": 0.015,
        "min_order_qty": min_order_qty,
        "max_order_qty": max_order_qty,
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
    base_specs = filter_base_specs(build_base_specs(), parse_tokens(args.include_families))
    if args.variant_mode == "expanded":
        specs = build_expanded_specs(
            base_specs=base_specs,
            profiles_per_family=args.profiles_per_family,
            seed=args.profile_seed,
        )
    else:
        variants = parse_variants(args.variants)
        specs = []
        for base in base_specs:
            for variant in variants:
                specs.append(apply_variant(base, variant))

    include_strategies = load_include_strategies(args)
    if include_strategies:
        specs = [s for s in specs if s.name in include_strategies]
        if not specs:
            raise SystemExit("No strategies selected after include-strategies filtering")

    budgets = parse_floats(args.budgets)
    seeds = parse_ints(args.seeds)
    windows = split_windows(df_raw, args.window_days, args.max_windows)
    execution_cfg = {
        "base_slippage_bps": float(args.base_slippage_bps),
        "slippage_volatility_scale": float(args.slippage_volatility_scale),
        "market_impact_bps": float(args.market_impact_bps),
        "latency_ms": float(args.latency_ms),
        "latency_penalty_bps_per_100ms": float(args.latency_penalty_bps_per_100ms),
        "adverse_selection_bps": float(args.adverse_selection_bps),
        "fill_probability_floor": float(args.fill_probability_floor),
        "fill_probability_ceiling": float(args.fill_probability_ceiling),
    }

    results: List[ExperimentResult] = []

    for budget in budgets:
        for spec in specs:
            print(f"[quant] strategy={spec.name} budget={budget:.0f} seeds={seeds}", flush=True)

            full_runs = [run_single(prep_data(df_raw), spec, budget, seed, execution_cfg) for seed in seeds]
            full_metrics = [r.get("metrics", {}) for r in full_runs]
            full_risk = [compute_risk_stats(r, budget, args.tail_quantile) for r in full_runs]
            seed_returns = [_safe_float(m.get("total_pnl", 0.0)) / max(1e-9, budget) for m in full_metrics]
            seed_drawdowns = [_safe_float(m.get("max_drawdown", 0.0)) / max(1e-9, budget) for m in full_metrics]

            pass_windows = 0
            hard_fails = 0
            window_dd_pcts: List[float] = []
            for w in windows:
                m = run_single(prep_data(w), spec, budget, seeds[0], execution_cfg)
                wm = m.get("metrics", {})
                wr = compute_risk_stats(m, budget, args.tail_quantile)
                dd_pct = _safe_float(wm.get("max_drawdown", 0.0)) / max(1e-9, budget)
                window_dd_pcts.append(dd_pct)
                pnl = _safe_float(wm.get("total_pnl", 0.0))
                total_return_pct = pnl / max(1e-9, budget)
                sortino = wr["sortino_ratio"]
                cvar95 = wr["cvar_95_pct"]
                if (
                    dd_pct <= args.drawdown_fail_pct
                    and pnl >= 0
                    and sortino >= args.min_sortino
                    and cvar95 <= args.max_cvar95_pct
                    and total_return_pct <= args.max_total_return_pct
                ):
                    pass_windows += 1
                if dd_pct > args.drawdown_fail_pct:
                    hard_fails += 1

            pass_rate = (pass_windows / len(windows)) if windows else 0.0

            total_pnl = _safe_float(sum(_safe_float(m.get("total_pnl", 0.0)) for m in full_metrics) / max(1, len(full_metrics)))
            total_return_pct = total_pnl / max(1e-9, budget)
            sharpe = _safe_float(sum(_safe_float(m.get("sharpe_ratio", 0.0)) for m in full_metrics) / max(1, len(full_metrics)))
            max_dd_values = [_safe_float(m.get("max_drawdown", 0.0)) for m in full_metrics]
            full_dd_pcts = [v / max(1e-9, budget) for v in max_dd_values]
            dd_pct_min = _safe_float(min(full_dd_pcts) if full_dd_pcts else 0.0)
            dd_pct_mean = _safe_float(sum(full_dd_pcts) / max(1, len(full_dd_pcts)))
            dd_pct_full_max = _safe_float(max(full_dd_pcts) if full_dd_pcts else 0.0)
            dd_pct_window_max = _safe_float(max(window_dd_pcts) if window_dd_pcts else 0.0)
            dd_pct = _safe_float(max(dd_pct_full_max, dd_pct_window_max))
            max_dd = _safe_float(dd_pct * budget)
            worst_seed_return_pct = _safe_float(min(seed_returns) if seed_returns else 0.0)
            best_seed_return_pct = _safe_float(max(seed_returns) if seed_returns else 0.0)
            seed_return_mean = _safe_float(sum(seed_returns) / max(1, len(seed_returns)))
            seed_return_std_pct = _safe_float(
                math.sqrt(sum((x - seed_return_mean) ** 2 for x in seed_returns) / max(1, len(seed_returns)))
            )
            worst_seed_drawdown_pct = _safe_float(max(seed_drawdowns) if seed_drawdowns else 0.0)
            seed_drawdown_mean = _safe_float(sum(seed_drawdowns) / max(1, len(seed_drawdowns)))
            seed_drawdown_std_pct = _safe_float(
                math.sqrt(sum((x - seed_drawdown_mean) ** 2 for x in seed_drawdowns) / max(1, len(seed_drawdowns)))
            )
            n_trades = _safe_float(sum(_safe_float(m.get("n_trades", 0.0)) for m in full_metrics) / max(1, len(full_metrics)))
            fill_ratio = _safe_float(sum(_safe_float(m.get("fill_ratio", 0.0)) for m in full_metrics) / max(1, len(full_metrics)))
            execution_cost = _safe_float(sum(_safe_float(m.get("execution_cost", 0.0)) for m in full_metrics) / max(1, len(full_metrics)))
            execution_cost_bps = _safe_float(sum(_safe_float(m.get("execution_cost_bps", 0.0)) for m in full_metrics) / max(1, len(full_metrics)))
            slippage_cost = _safe_float(sum(_safe_float(m.get("slippage_cost", 0.0)) for m in full_metrics) / max(1, len(full_metrics)))
            latency_cost = _safe_float(sum(_safe_float(m.get("latency_cost", 0.0)) for m in full_metrics) / max(1, len(full_metrics)))
            impact_cost = _safe_float(sum(_safe_float(m.get("impact_cost", 0.0)) for m in full_metrics) / max(1, len(full_metrics)))
            adverse_selection_cost = _safe_float(
                sum(_safe_float(m.get("adverse_selection_cost", 0.0)) for m in full_metrics) / max(1, len(full_metrics))
            )
            realized_edge_bps = _safe_float(sum(_safe_float(m.get("realized_edge_bps", 0.0)) for m in full_metrics) / max(1, len(full_metrics)))
            execution_quality_score = _safe_float(
                sum(_safe_float(m.get("execution_quality_score", 0.0)) for m in full_metrics) / max(1, len(full_metrics))
            )

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
                and total_return_pct <= args.max_total_return_pct
                and worst_seed_return_pct >= args.min_worst_seed_return_pct
                and worst_seed_drawdown_pct <= args.max_worst_seed_drawdown_pct
                and fill_ratio >= args.min_fill_ratio
                and execution_cost_bps <= args.max_execution_cost_bps
            )

            calmar_capped = max(-2.0, min(8.0, calmar))
            sharpe_capped = max(-2.0, min(8.0, sharpe))
            sortino_capped = max(-2.0, min(10.0, sortino))
            profit_factor_capped = max(0.0, min(4.0, profit_factor))
            plausibility_penalty = max(0.0, total_return_pct - args.max_total_return_pct)
            execution_quality_norm = (execution_quality_score - 50.0) / 25.0

            robustness = (
                (1.2 * sharpe_capped)
                + (1.8 * sortino_capped)
                + (1.0 * calmar_capped)
                + (1.8 * pass_rate)
                + (0.8 * pos_ratio)
                + (0.6 * profit_factor_capped)
                + total_return_pct
                - (4.0 * dd_pct)
                - (1.5 * worst_seed_drawdown_pct)
                + (1.0 * worst_seed_return_pct)
                - (2.0 * seed_return_std_pct)
                - (2.5 * seed_drawdown_std_pct)
                - (8.0 * cvar95)
                - (3.0 * ulcer)
                - (2.5 * hard_fails)
                - (12.0 * plausibility_penalty)
                + (1.0 * fill_ratio)
                + (0.4 * realized_edge_bps)
                + (0.5 * execution_quality_norm)
                - (0.4 * execution_cost_bps)
            )

            _, _, variant = spec.name.partition("__")
            results.append(
                ExperimentResult(
                    strategy=spec.name,
                    family=spec.family,
                    variant=variant or "balanced",
                    budget=budget,
                    total_pnl=total_pnl,
                    total_return_pct=total_return_pct,
                    sharpe_ratio=sharpe,
                    sortino_ratio=sortino,
                    calmar_ratio=calmar,
                    cvar_95_pct=cvar95,
                    ulcer_index=ulcer,
                    profit_factor=profit_factor,
                    positive_return_ratio=pos_ratio,
                    max_drawdown=max_dd,
                    max_drawdown_pct=dd_pct,
                    max_drawdown_pct_min=dd_pct_min,
                    max_drawdown_pct_mean=dd_pct_mean,
                    max_drawdown_pct_full_max=dd_pct_full_max,
                    max_drawdown_pct_window_max=dd_pct_window_max,
                    worst_seed_return_pct=worst_seed_return_pct,
                    best_seed_return_pct=best_seed_return_pct,
                    seed_return_std_pct=seed_return_std_pct,
                    worst_seed_drawdown_pct=worst_seed_drawdown_pct,
                    seed_drawdown_std_pct=seed_drawdown_std_pct,
                    n_trades=n_trades,
                    fill_ratio=fill_ratio,
                    execution_cost=execution_cost,
                    execution_cost_bps=execution_cost_bps,
                    slippage_cost=slippage_cost,
                    latency_cost=latency_cost,
                    impact_cost=impact_cost,
                    adverse_selection_cost=adverse_selection_cost,
                    realized_edge_bps=realized_edge_bps,
                    execution_quality_score=execution_quality_score,
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
    data_profile = summarize_data_profile(raw)

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
            "variant_mode": args.variant_mode,
            "profiles_per_family": args.profiles_per_family,
            "profile_seed": args.profile_seed,
            "included_families": parse_tokens(args.include_families),
            "included_strategies_count": len(load_include_strategies(args)),
            "budgets": parse_floats(args.budgets),
            "variants": parse_variants(args.variants),
            "seeds": parse_ints(args.seeds),
            "rows": int(len(raw)),
            "data_profile": data_profile,
            "strategies": sorted(set(df["strategy"].tolist())),
            "experiment_cases": int(len(df)),
            "execution_model": {
                "base_slippage_bps": args.base_slippage_bps,
                "slippage_volatility_scale": args.slippage_volatility_scale,
                "market_impact_bps": args.market_impact_bps,
                "latency_ms": args.latency_ms,
                "latency_penalty_bps_per_100ms": args.latency_penalty_bps_per_100ms,
                "adverse_selection_bps": args.adverse_selection_bps,
                "fill_probability_floor": args.fill_probability_floor,
                "fill_probability_ceiling": args.fill_probability_ceiling,
            },
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
            "max_total_return_pct": args.max_total_return_pct,
            "min_worst_seed_return_pct": args.min_worst_seed_return_pct,
            "max_worst_seed_drawdown_pct": args.max_worst_seed_drawdown_pct,
            "min_fill_ratio": args.min_fill_ratio,
            "max_execution_cost_bps": args.max_execution_cost_bps,
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

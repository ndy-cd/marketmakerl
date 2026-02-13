import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml

from src.data.data_processor import DataProcessor
from src.models.avellaneda_stoikov import AvellanedaStoikovModel
from src.utils.market_data import calculate_signals

ALLOWED_MODES = {"backtest", "paper", "live"}


def _to_builtin(value: Any) -> Any:
    """Convert numpy/pandas scalar values to plain Python values for json output."""
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:  # noqa: BLE001
            return value
    return value


class StructuredAdapter(logging.LoggerAdapter):
    """Logger adapter that injects stable runtime fields."""

    def process(self, msg, kwargs):
        extra = kwargs.setdefault("extra", {})
        combined = dict(self.extra)
        combined.update(extra)
        kwargs["extra"] = combined
        return msg, kwargs


@dataclass
class AgentSpec:
    name: str
    role: str
    params: Dict[str, Any]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_runtime_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}

    mode = cfg.get("mode", "backtest")
    _require(mode in ALLOWED_MODES, f"Invalid mode={mode}. Allowed: {sorted(ALLOWED_MODES)}")

    _require("agents" in cfg and isinstance(cfg["agents"], list) and cfg["agents"], "config.agents is required")
    for idx, agent in enumerate(cfg["agents"]):
        _require("name" in agent, f"config.agents[{idx}].name is required")
        _require("role" in agent, f"config.agents[{idx}].role is required")
        if "params" not in agent:
            agent["params"] = {}
        _require(isinstance(agent["params"], dict), f"config.agents[{idx}].params must be a mapping")

    cfg.setdefault("paths", {})
    cfg["paths"].setdefault("artifacts_dir", "./artifacts")
    cfg["paths"].setdefault("data_dir", "./data")
    cfg.setdefault("logging", {"level": "INFO", "format": "jsonl"})
    cfg.setdefault("market", {"symbol": "BTC/USDT"})
    cfg.setdefault("run_id", datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ"))
    return cfg


class AgentRuntime:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.run_id = config["run_id"]
        self.mode = config["mode"]
        self.artifacts_dir = Path(config["paths"]["artifacts_dir"]).resolve()
        self.data_dir = Path(config["paths"]["data_dir"]).resolve()
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._build_logger()

    def _build_logger(self) -> StructuredAdapter:
        logger = logging.getLogger("agent_runtime")
        logger.handlers = []
        logger.setLevel(getattr(logging, str(self.config["logging"].get("level", "INFO")).upper(), logging.INFO))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        logger.addHandler(handler)
        return StructuredAdapter(logger, {"run_id": self.run_id, "mode": self.mode})

    def _log_event(self, level: int, event: str, **payload: Any) -> None:
        fmt = self.config["logging"].get("format", "jsonl")
        if fmt == "jsonl":
            body = {"event": event, "run_id": self.run_id, "mode": self.mode}
            body.update(payload)
            self.logger.log(level, json.dumps(body, default=str))
            return
        self.logger.log(level, f"{event} | {payload}")

    def _ensure_live_secrets(self) -> None:
        paper_only = str(os.getenv("PAPER_ONLY", "0")).lower() in {"1", "true", "yes"}
        if paper_only:
            raise ValueError("mode=live is disabled while PAPER_ONLY=1")
        required = ["EXCHANGE_API_KEY", "EXCHANGE_API_SECRET"]
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            raise ValueError(f"mode=live requires env vars: {', '.join(missing)}")

    def run_all(self, max_workers: int = 4) -> List[Dict[str, Any]]:
        if self.mode == "live":
            self._ensure_live_secrets()

        agents = [
            AgentSpec(name=a["name"], role=a["role"], params=a.get("params", {}))
            for a in self.config["agents"]
        ]
        max_workers = max(1, min(max_workers, len(agents)))
        self._log_event(logging.INFO, "runtime_start", agents=len(agents), workers=max_workers)

        results: List[Dict[str, Any]] = []
        failures = 0
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(self._run_agent, spec): spec for spec in agents}
            for fut in as_completed(futures):
                spec = futures[fut]
                try:
                    result = fut.result()
                    results.append(result)
                    self._log_event(logging.INFO, "agent_completed", agent=spec.name, role=spec.role)
                except Exception as exc:  # noqa: BLE001
                    failures += 1
                    self._log_event(
                        logging.ERROR,
                        "agent_failed",
                        agent=spec.name,
                        role=spec.role,
                        error=str(exc),
                    )

        summary = {"failures": failures, "successes": len(agents) - failures, "total": len(agents)}
        self._log_event(logging.INFO, "runtime_complete", **summary)
        if failures > 0:
            raise RuntimeError(f"{failures} agent(s) failed")
        return results

    def _run_agent(self, spec: AgentSpec) -> Dict[str, Any]:
        role = spec.role.lower()
        if role == "data":
            return self._run_data_agent(spec)
        if role == "ml":
            return self._run_ml_agent(spec)
        if role == "execution":
            return self._run_execution_agent(spec)
        if role == "risk":
            return self._run_risk_agent(spec)
        raise ValueError(f"Unsupported agent role={spec.role}")

    def _run_data_agent(self, spec: AgentSpec) -> Dict[str, Any]:
        processor = DataProcessor(data_dir=str(self.data_dir))
        np_seed = int(spec.params.get("seed", 42))
        # Seed once per worker for deterministic simulated data generation.
        import numpy as np

        np.random.seed(np_seed)
        frame = processor.simulate_market_data(
            n_periods=int(spec.params.get("n_periods", 500)),
            initial_price=float(spec.params.get("initial_price", 2000)),
            volatility=float(spec.params.get("volatility", 0.01)),
            mean_reversion=float(spec.params.get("mean_reversion", 0.1)),
        )
        out_file = self.artifacts_dir / f"{self.run_id}_{spec.name}_market_data.csv"
        frame.to_csv(out_file)
        return {"agent": spec.name, "role": spec.role, "rows": len(frame), "output": str(out_file)}

    def _run_ml_agent(self, spec: AgentSpec) -> Dict[str, Any]:
        processor = DataProcessor(data_dir=str(self.data_dir))
        frame = processor.simulate_market_data(n_periods=int(spec.params.get("n_periods", 300)))
        signals = calculate_signals(frame, lookback=min(100, len(frame) - 1))
        model = AvellanedaStoikovModel(
            risk_aversion=float(spec.params.get("risk_aversion", 1.0)),
            volatility=float(max(1e-8, signals.get("volatility", 0.01))),
        )
        mid_price = float(frame["mid_price"].iloc[-1])
        model.set_parameters(market_features=signals)
        bid, ask = model.calculate_optimal_quotes(mid_price)
        return {
            "agent": spec.name,
            "role": spec.role,
            "mid_price": round(mid_price, 6),
            "bid": round(float(bid), 6),
            "ask": round(float(ask), 6),
        }

    def _run_execution_agent(self, spec: AgentSpec) -> Dict[str, Any]:
        processor = DataProcessor(data_dir=str(self.data_dir))
        frame = processor.simulate_market_data(
            n_periods=int(spec.params.get("n_periods", 500)),
            initial_price=float(spec.params.get("initial_price", 2000)),
        )
        model = AvellanedaStoikovModel(
            risk_aversion=float(spec.params.get("risk_aversion", 1.0)),
            time_horizon=float(spec.params.get("time_horizon", 1.0)),
            volatility=float(spec.params.get("volatility", 0.01)),
        )
        try:
            from src.backtesting.backtest_engine import BacktestEngine

            engine = BacktestEngine(
                market_data=frame,
                initial_capital=float(spec.params.get("initial_capital", 10000.0)),
                transaction_fee=float(spec.params.get("transaction_fee", 0.001)),
                random_seed=int(spec.params.get("random_seed", 42)),
                min_edge_bps=float(spec.params.get("min_edge_bps", 0.0)),
                cooldown_steps=int(spec.params.get("cooldown_steps", 1)),
            )
            execution_params = {
                "spread_constraint": spec.params.get("spread_constraint"),
                "spread_constraint_bps": spec.params.get("spread_constraint_bps"),
                "min_edge_bps": float(spec.params.get("min_edge_bps", 0.0)),
                "cooldown_steps": int(spec.params.get("cooldown_steps", 1)),
                "inventory_soft_limit_ratio": float(spec.params.get("inventory_soft_limit_ratio", 0.8)),
                "target_volatility": float(spec.params.get("target_volatility", 0.0)),
                "vol_spread_scale": float(spec.params.get("vol_spread_scale", 0.0)),
                "soft_drawdown_risk_pct": float(spec.params.get("soft_drawdown_risk_pct", 1.0)),
                "hard_drawdown_stop_pct": float(spec.params.get("hard_drawdown_stop_pct", 1.0)),
                "adverse_return_bps": float(spec.params.get("adverse_return_bps", 0.0)),
                "risk_off_inventory_scale": float(spec.params.get("risk_off_inventory_scale", 0.5)),
            }
            execution_params = {k: v for k, v in execution_params.items() if v is not None}

            backtest_mode = str(spec.params.get("backtest_mode", "standard")).lower()
            if backtest_mode == "standard":
                result = engine.run_backtest(
                    model=model,
                    params=execution_params,
                    max_inventory=int(spec.params.get("max_inventory", 20)),
                    volatility_window=int(spec.params.get("volatility_window", 20)),
                )
            else:
                result = engine.run_backtest_enhanced(
                    model=model,
                    params=execution_params,
                    max_inventory=int(spec.params.get("max_inventory", 20)),
                    volatility_window=int(spec.params.get("volatility_window", 20)),
                    use_signals=bool(spec.params.get("use_signals", True)),
                )
            metrics = result["metrics"]
            metrics["execution_mode"] = "backtest_engine"
        except ModuleNotFoundError:
            # Fallback path keeps orchestration runnable when optional RL deps are absent.
            returns = frame["mid_price"].pct_change().fillna(0.0)
            avg_spread = float(frame["spread"].mean()) if "spread" in frame.columns else 0.001
            inventory = int(spec.params.get("max_inventory", 20))
            initial_capital = float(spec.params.get("initial_capital", 10000.0))
            gross = float(returns.abs().sum() * initial_capital * 0.05)
            risk_penalty = float(avg_spread * initial_capital * max(1, inventory / 10))
            metrics = {
                "total_pnl": gross - risk_penalty,
                "realized_pnl": gross - risk_penalty,
                "unrealized_pnl": 0.0,
                "max_drawdown": float((returns.cumsum().max() - returns.cumsum().min()) * initial_capital),
                "n_trades": int(len(frame) // 5),
                "sharpe_ratio": float(returns.mean() / returns.std() * (252**0.5)) if returns.std() > 0 else 0.0,
                "execution_mode": "fallback_no_rl_runtime",
            }
        metrics_path = self.artifacts_dir / f"{self.run_id}_{spec.name}_metrics.json"
        with open(metrics_path, "w", encoding="utf-8") as fh:
            json.dump(metrics, fh, indent=2, default=_to_builtin)
        return {"agent": spec.name, "role": spec.role, "metrics_path": str(metrics_path)}

    def _run_risk_agent(self, spec: AgentSpec) -> Dict[str, Any]:
        max_drawdown_limit = float(spec.params.get("max_drawdown_limit", 3000.0))
        risk_report = {
            "max_drawdown_limit": max_drawdown_limit,
            "status": "ok",
            "note": "Standalone risk agent scaffolding; wire to live execution metrics before production.",
        }
        out_file = self.artifacts_dir / f"{self.run_id}_{spec.name}_risk_report.json"
        with open(out_file, "w", encoding="utf-8") as fh:
            json.dump(risk_report, fh, indent=2)
        return {"agent": spec.name, "role": spec.role, "output": str(out_file)}

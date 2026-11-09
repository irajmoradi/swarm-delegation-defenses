"""Thin OpenRouter chat client: jsonl cache keyed by prompt hash, per-call cost log, hard spend cap.

- Key (release): env var OPENROUTER_API_KEY, else the file named by OPENROUTER_KEY_FILE; read in-process only (whitespace and a leading NAME= prefix stripped). It is never
  printed, logged, cached or written anywhere; it lives only in the Authorization header.
- Cache: cache/llm_cache.jsonl, key = sha256(model, messages, max_tokens, reasoning_effort).
- Log: results/run_log.jsonl, one line per call (cached or paid): tag, model, tokens, cost, cache hit.
- Ledger: results/spend_ledger.jsonl, one line per PAID call; the cap is checked against its total plus
  in-flight worst-case reservations before each call.
- Stub mode (stub=True): no network; returns a deterministic fake reply via `stub_fn` and records an
  ESTIMATED cost (chars/4 tokens in, `stub_out_tokens` out) into results/dryrun_log.jsonl.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
KEY_FILE = Path(os.environ["OPENROUTER_KEY_FILE"]) if os.environ.get("OPENROUTER_KEY_FILE") else None  # release: env var
CACHE_PATH = ROOT / "cache" / "llm_cache.jsonl"
RUN_LOG = ROOT / "results" / "run_log.jsonl"
LEDGER = ROOT / "results" / "spend_ledger.jsonl"
DRYRUN_LOG = ROOT / "results" / "dryrun_log.jsonl"
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
CAP_USD = 17.80  # round 6: +$4 approved by team lead (Mario approved continuing)

# USD per token, from https://openrouter.ai/api/v1/models (checked 2026-11-07)
PRICES = {
    "openai/gpt-5-nano": (0.05e-6, 0.40e-6),
    "openai/gpt-5-mini": (0.25e-6, 2.00e-6),
    "openai/gpt-5.4-mini": (0.75e-6, 4.50e-6),  # round 7 stronger-monitor control (checked 2026-11-08)
}


class BudgetExceeded(RuntimeError):
    pass


def _load_key() -> str:
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"].strip()
    if KEY_FILE is None:
        raise RuntimeError("set OPENROUTER_API_KEY or OPENROUTER_KEY_FILE (see .env.example)")
    raw = KEY_FILE.read_text().strip()
    m = re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s*=\s*(.*)$", raw, re.S)
    if m:
        raw = m.group(1).strip().strip('"').strip("'")
    if not raw:
        raise RuntimeError("key file empty")
    return raw


class LLM:
    def __init__(self, stub: bool = False, stub_fn=None, stub_out_tokens: int = 300, cap_usd: float = CAP_USD):
        self.stub = stub
        self.stub_fn = stub_fn
        self.stub_out_tokens = stub_out_tokens
        self.cap = cap_usd
        self.lock = threading.Lock()
        self.reserved = 0.0
        self.cache: dict[str, dict] = {}
        for p in (CACHE_PATH, RUN_LOG, LEDGER):
            p.parent.mkdir(parents=True, exist_ok=True)
        if CACHE_PATH.exists():
            for line in CACHE_PATH.read_text().splitlines():
                if line.strip():
                    d = json.loads(line)
                    self.cache[d["key"]] = d
        self.spent = 0.0
        if LEDGER.exists():
            for line in LEDGER.read_text().splitlines():
                if line.strip():
                    self.spent += float(json.loads(line)["cost_usd"])
        self.dry_cost = 0.0
        self.dry_calls = 0
        self._client = None
        if not stub:
            self._client = httpx.Client(timeout=120.0, headers={
                "Authorization": "Bearer " + _load_key(),
                "Content-Type": "application/json",
                "X-Title": "linking-problem-pilot"})

    @staticmethod
    def key_of(model, messages, max_tokens, effort) -> str:
        blob = json.dumps({"m": model, "msg": messages, "mt": max_tokens, "e": effort}, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()

    def _log(self, path: Path, rec: dict) -> None:
        with self.lock:
            with open(path, "a") as f:
                f.write(json.dumps(rec) + "\n")

    def chat(self, model: str, messages: list[dict], *, max_tokens: int = 800, effort: str = "minimal",
             tag: str = "") -> str:
        key = self.key_of(model, messages, max_tokens, effort)
        pin, pout = PRICES[model]
        if key in self.cache:
            d = self.cache[key]
            self._log(RUN_LOG, {"ts": time.time(), "tag": tag, "model": model, "key": key, "cached": True,
                                "in_tok": d["in_tok"], "out_tok": d["out_tok"], "cost_usd": 0.0,
                                "orig_cost_usd": d["cost_usd"]})
            return d["text"]
        chars = sum(len(m["content"]) for m in messages)
        if self.stub:
            text = self.stub_fn(model, messages, tag) if self.stub_fn else "SCORE: 10"
            est = chars / 4 * pin + self.stub_out_tokens * pout
            with self.lock:
                self.dry_cost += est
                self.dry_calls += 1
            self._log(DRYRUN_LOG, {"tag": tag, "model": model, "in_tok_est": chars / 4,
                                   "out_tok_est": self.stub_out_tokens, "est_usd": est})
            return text
        worst = chars / 3.0 * pin + max_tokens * pout
        with self.lock:
            if self.spent + self.reserved + worst > self.cap:
                raise BudgetExceeded(f"cap ${self.cap:.2f}: spent {self.spent:.4f} + reserved {self.reserved:.4f}")
            self.reserved += worst
        try:
            body = {"model": model, "messages": messages, "max_tokens": max_tokens,
                    "reasoning": {"effort": effort}, "usage": {"include": True}}
            data = None
            for attempt in range(5):
                try:
                    r = self._client.post(BASE_URL, json=body)
                except httpx.HTTPError as e:
                    err = type(e).__name__
                    time.sleep(2 ** attempt)
                    continue
                if r.status_code in (429, 500, 502, 503, 504):
                    err = f"http {r.status_code}"
                    time.sleep(2 ** attempt + 1)
                    continue
                if r.status_code != 200:
                    raise RuntimeError(f"http {r.status_code}: {r.text[:300]}")
                data = r.json()
                if "choices" not in data:
                    err = str(data.get("error", ""))[:200]
                    time.sleep(2 ** attempt)
                    data = None
                    continue
                break
            if data is None:
                raise RuntimeError(f"failed after retries: {err}")
            text = data["choices"][0]["message"].get("content") or ""
            u = data.get("usage", {}) or {}
            in_tok, out_tok = int(u.get("prompt_tokens", 0)), int(u.get("completion_tokens", 0))
            cost = u.get("cost")
            cost = float(cost) if cost is not None else in_tok * pin + out_tok * pout
            rtok = (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
        finally:
            with self.lock:
                self.reserved = max(0.0, self.reserved - worst)
        rec = {"key": key, "model": model, "text": text, "in_tok": in_tok, "out_tok": out_tok,
               "reasoning_tok": rtok, "cost_usd": cost, "provider": data.get("provider", "")}
        with self.lock:
            self.spent += cost
            self.cache[key] = rec
            with open(CACHE_PATH, "a") as f:
                f.write(json.dumps(rec) + "\n")
            with open(LEDGER, "a") as f:
                f.write(json.dumps({"ts": time.time(), "tag": tag, "model": model, "cost_usd": cost}) + "\n")
        self._log(RUN_LOG, {"ts": time.time(), "tag": tag, "model": model, "key": key, "cached": False,
                            "in_tok": in_tok, "out_tok": out_tok, "reasoning_tok": rtok, "cost_usd": cost,
                            "provider": data.get("provider", "")})
        return text

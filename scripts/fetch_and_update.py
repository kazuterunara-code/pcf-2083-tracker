#!/usr/bin/env python3
"""
東証PCF（ポートフォリオ構成ファイル）を取得し、data/history.json に
日付ごとのスナップショットとして追記するスクリプト。

GitHub Actions から毎営業日呼び出されることを想定しています。

使い方:
    python scripts/fetch_and_update.py [ETFコード]

環境変数 ETF_CODE でも指定可能（デフォルト: 2083）。
"""
import json
import os
import sys
from datetime import datetime, timezone

import requests

ETF_CODE = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("ETF_CODE", "2083")
PCF_URL = f"https://inav.ice.com/pcf-download/{ETF_CODE}.csv"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_PATH = os.path.join(SCRIPT_DIR, "..", "data", "history.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://inav.ice.com/tse/iopv/table?language=jp",
    "Connection": "keep-alive",
}


def split_csv_line(line: str):
    """ごく簡易的なCSV1行パーサー（ダブルクオート対応）。"""
    out, cur, in_q = [], "", False
    for ch in line:
        if ch == '"':
            in_q = not in_q
            continue
        if ch == "," and not in_q:
            out.append(cur)
            cur = ""
            continue
        cur += ch
    out.append(cur)
    return out


def parse_pcf(text: str) -> dict:
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) < 4:
        raise ValueError(f"PCFの形式が想定と異なります（行数={len(lines)}）")

    fund_row = split_csv_line(lines[1])
    cash = float(fund_row[2])
    shares_outstanding = int(float(fund_row[3]))
    fund_date = fund_row[4].strip()

    holdings = {}
    total_stock_value = 0.0
    for line in lines[3:]:
        r = split_csv_line(line)
        if len(r) < 7:
            continue
        code, name = r[0].strip(), r[1].strip()
        try:
            shares = float(r[5])
            price = float(r[6])
        except ValueError:
            continue
        value = shares * price
        total_stock_value += value
        holdings[code] = {
            "name": name,
            "shares": shares,
            "price": price,
            "value": value,
        }

    total_fund_value = total_stock_value + cash
    if total_fund_value <= 0:
        raise ValueError("ファンド総額の計算結果が0以下です")

    for h in holdings.values():
        h["weight_pct"] = h["value"] / total_fund_value * 100

    return {
        "fund_date": fund_date,
        "cash": cash,
        "shares_outstanding": shares_outstanding,
        "total_fund_value": total_fund_value,
        "cash_weight_pct": cash / total_fund_value * 100,
        "holdings": holdings,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def load_history() -> list:
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(history: list):
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def main():
    print(f"[fetch] GET {PCF_URL}")
    resp = requests.get(PCF_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    text = resp.content.decode("utf-8-sig", errors="replace")

    first_line = text.splitlines()[0] if text.splitlines() else ""
    print(f"[fetch] first line: {first_line[:120]}")

    snapshot = parse_pcf(text)
    print(
        f"[parse] fund_date={snapshot['fund_date']} "
        f"holdings={len(snapshot['holdings'])} "
        f"cash%={snapshot['cash_weight_pct']:.2f}"
    )

    history = load_history()
    before = len(history)
    history = [h for h in history if h["fund_date"] != snapshot["fund_date"]]
    history.append(snapshot)
    history.sort(key=lambda h: h["fund_date"])
    save_history(history)

    print(f"[save] history: {before} -> {len(history)} snapshot(s) at {HISTORY_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[error] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)

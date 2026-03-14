#!/usr/bin/env python3
"""Save 1-minute history for one or more securities to CSV files.

This script fetches historical 1-minute bars per trading day using
`AlfeHq_API.get_history_minute_time_data` and concatenates them into a
single CSV per code.

Features:
- host rotation using `config/hosts.py` list
- simple retry on connection failure
- saves CSV files under output directory

Usage:
    cd /d/WorkSpace/Python/alfe/scripts
    # 抓取 000001 在 2023-01 的 1分钟和5分钟数据
    python save_history_period_all.py -c 000001 -p -1 -5 -s 2023-01-01 -e 2023-01-31 --outdir ../data
    # 抓取所有周期
    python save_history_period_all.py -c 000001 -p all --outdir ../data
    
    python save_history_period_all.py -c 300420 -p all -s 2000-01-01 -e 2025-12-31 --outdir ../data
"""
import argparse
import os
import sys

# 设置 alfe 模块路径
sys.path.insert(0, "/workspace/alfe")
import sys
import time
from datetime import datetime, timedelta

# ensure project root on path when running as script
HERE = os.path.dirname(__file__)
# parent of package directory (one level above the alfe package)
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# import alfe modules lazily (avoid hard import at script load time so -h works without pandas)
AlfeHq_API = None
ALFEParams = None
hq_hosts = None


def parse_args():
    p = argparse.ArgumentParser(
        description="Save historical bars for multiple periods to CSV"
    )
    p.add_argument(
        "-c", "--codes", nargs="+", required=True, help="list of codes (eg 000001)"
    )
    p.add_argument(
        "-p",
        "--periods",
        nargs="+",
        default=["-1"],
        help="periods to fetch. values: -1 -5 -15 -30 -60 -d -w -m or 'all' for all periods",
    )
    p.add_argument(
        "-s", "--start", default=None, help="start date YYYY-MM-DD (inclusive)"
    )
    p.add_argument("-e", "--end", default=None, help="end date YYYY-MM-DD (inclusive)")
    p.add_argument("--outdir", default="../data", help="output directory")
    p.add_argument(
        "--market",
        type=int,
        choices=[0, 1],
        default=None,
        help="market code (0:SZ,1:SH) — auto-detected from code if omitted",
    )
    p.add_argument("--retries", type=int, default=3, help="retries per host")
    p.add_argument("--sleep", type=float, default=0.5, help="sleep between retries (s)")
    p.add_argument("--timeout", type=float, default=5.0, help="connect timeout seconds")
    p.add_argument(
        "--no-validate-host",
        action="store_true",
        help="skip validating host by calling get_security_bars",
    )
    return p.parse_args()


def try_connect_hosts(api, retries=1):
    """Try hosts in hq_hosts sequentially. Returns connected api or None."""
    for name, ip, port in hq_hosts:
        for attempt in range(retries):
            try:
                obj = api.connect(ip, port)
                if obj:
                    return api
            except Exception:
                time.sleep(0.1)
        # try next host
    return None


def period_to_category(period):
    mapping = {
        "-1": (ALFEParams.KLINE_TYPE_1MIN, "1m"),
        "-5": (ALFEParams.KLINE_TYPE_5MIN, "5m"),
        "-15": (ALFEParams.KLINE_TYPE_15MIN, "15m"),
        "-30": (ALFEParams.KLINE_TYPE_30MIN, "30m"),
        "-60": (ALFEParams.KLINE_TYPE_1HOUR, "60m"),
        "-d": (ALFEParams.KLINE_TYPE_DAILY, "D"),
        "-w": (ALFEParams.KLINE_TYPE_WEEKLY, "W"),
        "-m": (ALFEParams.KLINE_TYPE_MONTHLY, "M"),
    }
    return mapping.get(period)


def save_code_for_category(
    api, code, category, period_label, outdir, start=None, end=None, market_arg=None
):
    try:

        def _detect_market(c):
            return 1 if str(c).startswith("6") else 0

        market = market_arg if market_arg is not None else _detect_market(code)

        offset = 0
        batch = 800
        frames = []
        while True:
            try:
                data = api.get_security_bars(category, market, code, offset, batch)
            except Exception as e:
                print(
                    f"Warning: get_security_bars failed for {code} offset {offset}: {e}"
                )
                break
            if not data:
                # no more data
                break
            try:
                df = api.to_df(data)
            except Exception:
                import pandas as pd

                df = pd.DataFrame(data)
            frames.append(df)
            print(f"Fetched {len(data)} bars for {code} {period_label} offset {offset}")
            if len(data) < batch:
                break
            offset += batch

        if not frames:
            print("No data fetched for", code, period_label)
            return False

        import pandas as pd

        full = pd.concat(frames, axis=0, ignore_index=True)

        # normalize datetime
        if "datetime" in full.columns:
            full["__dt"] = pd.to_datetime(full["datetime"], errors="coerce")
        else:
            # try year/month/day columns
            if set(["year", "month", "day"]).issubset(full.columns):
                full["__dt"] = pd.to_datetime(full[["year", "month", "day"]])
            else:
                full["__dt"] = pd.NaT

        if start:
            start_dt = pd.to_datetime(start)
            full = full[full["__dt"] >= start_dt]
        if end:
            end_dt = (
                pd.to_datetime(end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            )
            full = full[full["__dt"] <= end_dt]

        # ----- debug prints for date filtering check only -----
        print(f"Total bars before filter: {len(full)}")
        print(
            f"Bars after filter: {len(full[full['__dt'] >= start_dt])}"
        )  # 临时，只 start
        print(full["year"].min(), full["year"].max())  # 检查年份范围

        # drop helper
        full = full.drop(columns=["__dt"])

        fname = os.path.join(
            outdir, f"{code}_Candlestick_{period_label}_BID_{start or 'all'}_{end or 'all'}.csv"
        )
        full.to_csv(fname, index=False)
        print("Saved", fname)
        return True
    except Exception as e:
        print("Failed to fetch or save for", code, period_label, "error:", e)
        return False


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    # lazy imports
    global AlfeHq_API, ALFEParams, hq_hosts
    from alfe.hq import AlfeHq_API as _AlfeHq
    from alfe.params import ALFEParams as _ALFEParams
    from alfe.config.hosts import hq_hosts as _hq_hosts

    AlfeHq_API = _AlfeHq
    ALFEParams = _ALFEParams
    hq_hosts = _hq_hosts

    api = AlfeHq_API()
    connected = try_connect_hosts(api, retries=args.retries)
    if not connected:
        print("Unable to connect to any host")
        return 1

    # determine periods to run
    periods = args.periods
    if "all" in periods:
        periods = ["-1", "-5", "-15", "-30", "-60", "-d", "-w", "-m"]

    for code in args.codes:
        for p in periods:
            mapped = period_to_category(p)
            if not mapped:
                print("Unknown period:", p)
                continue
            category, label = mapped
            print(f"Processing {code} period {p} ({label})")
            ok = save_code_for_category(
                api,
                code,
                category,
                label,
                args.outdir,
                start=args.start,
                end=args.end,
                market_arg=args.market,
            )
            if not ok:
                print("Retrying once for", code, p)
                try:
                    save_code_for_category(
                        api,
                        code,
                        category,
                        label,
                        args.outdir,
                        start=args.start,
                        end=args.end,
                        market_arg=args.market,
                    )
                except Exception:
                    print("Still failed for", code, p)

    api.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())

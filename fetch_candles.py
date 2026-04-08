import requests
import pandas as pd

from analysis.structure_engine import apply_structure
from analysis.bos_engine import apply_bos_choch
from analysis.liquidity_engine import apply_liquidity
from analysis.fvg_engine import apply_fvg
from analysis.orderblock_engine import apply_orderblocks
from analysis.entry_engine import apply_entries


def get_candles(symbol="BTCUSDT", interval="15m", limit=500):
    url = "https://api.binance.us/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    response = requests.get(url, params=params)
    data = response.json()

    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    return df


if __name__ == "__main__":
    df = get_candles()

    # STEP 1 — MARKET STRUCTURE ENGINE
    df = apply_structure(df)

    # STEP 2 — BOS + CHoCH ENGINE
    df = apply_bos_choch(df)

    # STEP 3 — LIQUIDITY ENGINE
    df = apply_liquidity(df)

    # STEP 4 — PRO-LEVEL ICT FVG ENGINE
    df = apply_fvg(df)

    # STEP 5 — ICT PRO-LEVEL ORDER BLOCK ENGINE
    df = apply_orderblocks(df)

    # STEP 6 — HYBRID TRADE ENTRY ENGINE (OB first, then FVG)
    df = apply_entries(df)

    print(df[[
        "high",
        "low",
        "structure",
        "BOS",
        "CHoCH",
        "equal_high",
        "equal_low",
        "liquidity_sweep",
        "fvg_basic_bullish",
        "fvg_basic_bearish",
        "fvg_displacement_bullish",
        "fvg_displacement_bearish",
        "fvg_gap_start",
        "fvg_gap_end",
        "fvg_gap_midpoint",
        "fvg_gap_size",
        "fvg_valid",
        "fvg_mitigated",
        "fvg_unmitigated",
        "fvg_direction",
        "fvg_combo_signal",
        "ob_bullish",
        "ob_bearish",
        "ob_open",
        "ob_close",
        "ob_high",
        "ob_low",
        "ob_midpoint",
        "ob_valid",
        "ob_invalidated",
        "ob_mitigated",
        "ob_unmitigated",
        "ob_type",
        "ob_strength_score",
        "ob_combo_signal",
        "trade_direction",
        "setup_type",
        "entry_price",
        "stop_loss",
        "tp1_price",
        "tp2_price",
        "tp3_price",
        "rr_tp1",
        "rr_tp2",
        "rr_tp3",
        "trade_confidence_score"
    ]].tail(60))
    # STEP 7 — TRADE FILTERING + EXPORT ENGINE
    from analysis.filter_engine import filter_trades, summarize_trades
    from analysis.export_engine import export_to_json, export_to_csv, export_to_dict

    # Example: filter trades with confidence >= 5 and R:R >= 2
    filtered = filter_trades(
        df,
        min_confidence=5,
        min_rr=2.0,
        setup_types=None,
        directions=None
    )

    summary = summarize_trades(filtered)

    print("\n=== FILTERED TRADES ===")
    print(filtered.tail(20))

    print("\n=== TRADE SUMMARY ===")
    print(summary)

    # Export all formats
    export_to_json(filtered, "signals.json")
    export_to_csv(filtered, "signals.csv")
    signals_dict = export_to_dict(filtered)

    print("\nSignals exported to JSON, CSV, and dict.")

import asyncio
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone


MIN_MARKET_CAP = 1_000
MAX_MARKET_CAP = 500_000

SUPPORTED_CHAINS = {
    "solana",
    "base",
    "bsc",
    "ethereum",
    "monad",
    "arbitrum",
    "polygon",
    "avalanche",
}


def fetch_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "FOMO-Discord-Bot/1.0"
        },
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def get_token_profiles():
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    return fetch_json(url)


def get_token_pairs(chain_id, token_address):
    encoded = urllib.parse.quote(token_address, safe="")
    url = f"https://api.dexscreener.com/latest/dex/tokens/{encoded}"

    data = fetch_json(url)
    pairs = data.get("pairs") or []

    return [
        pair
        for pair in pairs
        if pair.get("chainId") == chain_id
    ]


def calculate_age(timestamp):
    if not timestamp:
        return "Unknown"

    try:
        launch_time = datetime.fromtimestamp(
            timestamp / 1000,
            tz=timezone.utc
        )

        now = datetime.now(timezone.utc)
        seconds = int((now - launch_time).total_seconds())

        if seconds < 0:
            return "Unknown"

        minutes = seconds // 60

        if minutes < 1:
            return "Less than 1 minute"

        if minutes < 60:
            return f"{minutes} minute(s)"

        hours = minutes // 60

        if hours < 24:
            return f"{hours} hour(s)"

        days = hours // 24

        return f"{days} day(s)"

    except Exception:
        return "Unknown"


def make_bubblemaps_url(chain, address):
    chain_map = {
        "solana": "solana",
        "ethereum": "ethereum",
        "bsc": "bsc",
        "base": "base",
        "monad": "monad",
        "arbitrum": "arbitrum",
        "polygon": "polygon",
        "avalanche": "avalanche",
    }

    bubble_chain = chain_map.get(chain)

    if not bubble_chain:
        return "https://bubblemaps.io/"

    return (
        f"https://bubblemaps.io/"
        f"{bubble_chain}/map/{address}"
    )


def scan_new_coins():
    profiles = get_token_profiles()

    if not isinstance(profiles, list):
        return []

    results = []

    for profile in profiles:

        chain = profile.get("chainId")
        address = profile.get("tokenAddress")

        if not chain or not address:
            continue

        if chain not in SUPPORTED_CHAINS:
            continue

        try:
            pairs = get_token_pairs(chain, address)
        except Exception:
            continue

        for pair in pairs:

            market_cap = pair.get("marketCap")

            if market_cap is None:
                market_cap = pair.get("fdv")

            if market_cap is None:
                continue

            try:
                market_cap = float(market_cap)
            except (TypeError, ValueError):
                continue

            if not (
                MIN_MARKET_CAP
                <= market_cap
                <= MAX_MARKET_CAP
            ):
                continue

            liquidity_data = pair.get("liquidity") or {}
            volume_data = pair.get("volume") or {}

            liquidity = liquidity_data.get("usd", 0)
            volume = volume_data.get("h24", 0)

            created_at = pair.get("pairCreatedAt")

            token = pair.get("baseToken") or {}

            name = token.get("name") or "Unknown"
            symbol = token.get("symbol") or "???"

            results.append({
                "name": name,
                "symbol": symbol,
                "chain": chain,
                "market_cap": market_cap,
                "liquidity": liquidity,
                "volume_24h": volume,
                "address": address,
                "pair_address": pair.get("pairAddress"),
                "created_at": created_at,
                "age": calculate_age(created_at),
                "url": pair.get("url"),
                "bubblemaps": make_bubblemaps_url(
                    chain,
                    address
                ),
            })

    results.sort(
        key=lambda coin: coin["created_at"] or 0,
        reverse=True
    )

    return results[:10]


async def snipe_scan():
    return await asyncio.to_thread(scan_new_coins)

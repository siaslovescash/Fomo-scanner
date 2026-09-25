import asyncio
import json
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone


MIN_MARKET_CAP = 1_000
MAX_MARKET_CAP = 500_000

# We do NOT limit this to a fixed chain list.
# Any chain returned by DEX Screener can be scanned.


CHAIN_NAMES = {
    "solana": "Solana",
    "ethereum": "Ethereum",
    "bsc": "BNB Chain",
    "base": "Base",
    "arbitrum": "Arbitrum",
    "polygon": "Polygon",
    "avalanche": "Avalanche",
    "optimism": "Optimism",
    "linea": "Linea",
    "mantle": "Mantle",
    "blast": "Blast",
    "zksync": "zkSync",
    "scroll": "Scroll",
    "fantom": "Fantom",
    "cronos": "Cronos",
    "celo": "Celo",
    "gnosis": "Gnosis",
    "moonbeam": "Moonbeam",
    "moonriver": "Moonriver",
    "aurora": "Aurora",
    "metis": "Metis",
    "opbnb": "opBNB",
    "mode": "Mode",
    "manta": "Manta",
    "taiko": "Taiko",
    "polygon_zkevm": "Polygon zkEVM",
    "ronin": "Ronin",
    "beam": "Beam",
    "sonic": "Sonic",
    "monad": "Monad",
    "hyperevm": "HyperEVM",
    "hyperliquid": "Hyperliquid",
    "tron": "Tron",
    "ton": "TON",
    "aptos": "Aptos",
    "sui": "Sui",
    "cardano": "Cardano",
    "injective": "Injective",
    "near": "NEAR",
    "sei": "Sei",
    "osmosis": "Osmosis",
    "starknet": "Starknet",
    "flow": "Flow",
    "hedera": "Hedera",
    "apechain": "ApeChain",
    "berachain": "Berachain",
    "zora": "Zora",
    "immutable-zkevm": "Immutable zkEVM",

    # Robinhood Chain
    "robinhood": "Robinhood Chain",
}


# Chains known to have a direct Bubblemaps V2 page.
BUBBLEMAPS_CHAINS = {
    "solana": "solana",
    "ethereum": "ethereum",
    "eth": "ethereum",
    "bsc": "bnb",
    "base": "base",
    "arbitrum": "arbitrum",
    "polygon": "polygon",
    "avalanche": "avalanche",
    "monad": "monad",
    "sonic": "sonic",
    "ton": "ton",
    "tron": "tron",
    "aptos": "aptos",
    "hyperevm": "hyperevm",
    "robinhood": "robinhood",
}


def fetch_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "FOMO-Discord-Bot/1.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(
            response.read().decode("utf-8")
        )


def get_token_profiles():
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    return fetch_json(url)


def get_token_pairs(chain_id, token_address):
    encoded = urllib.parse.quote(
        token_address,
        safe=""
    )

    url = (
        "https://api.dexscreener.com/"
        f"latest/dex/tokens/{encoded}"
    )

    data = fetch_json(url)

    pairs = data.get("pairs") or []

    # Only keep pairs belonging to the profile's chain.
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

        seconds = int(
            (now - launch_time).total_seconds()
        )

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


def get_chain_name(chain_id):
    if not chain_id:
        return "Unknown"

    return CHAIN_NAMES.get(
        chain_id,
        chain_id.replace("-", " ").title()
    )


def make_bubblemaps_url(chain, address):
    bubble_chain = BUBBLEMAPS_CHAINS.get(chain)

    if not bubble_chain:
        return None

    return (
        "https://v2.bubblemaps.io/map"
        f"?chain={bubble_chain}"
        f"&address={urllib.parse.quote(address)}"
        "&partnerId=regular"
    )


def scan_token_profile(profile):
    chain = profile.get("chainId")
    address = profile.get("tokenAddress")

    if not chain or not address:
        return []

    try:
        pairs = get_token_pairs(
            chain,
            address
        )
    except Exception:
        return []

    matches = []

    for pair in pairs:

        market_cap = pair.get("marketCap")

        if market_cap is None:
            market_cap = pair.get("fdv")

        if market_cap is None:
            continue

        try:
            market_cap = float(market_cap)
        except (
            TypeError,
            ValueError
        ):
            continue

        if not (
            MIN_MARKET_CAP
            <= market_cap
            <= MAX_MARKET_CAP
        ):
            continue

        liquidity_data = (
            pair.get("liquidity")
            or {}
        )

        volume_data = (
            pair.get("volume")
            or {}
        )

        liquidity = liquidity_data.get(
            "usd",
            0
        )

        volume = volume_data.get(
            "h24",
            0
        )

        created_at = pair.get(
            "pairCreatedAt"
        )

        token = (
            pair.get("baseToken")
            or {}
        )

        name = (
            token.get("name")
            or "Unknown"
        )

        symbol = (
            token.get("symbol")
            or "???"
        )

        matches.append({
            "name": name,
            "symbol": symbol,

            "chain": chain,

            "chain_name": get_chain_name(
                chain
            ),

            "market_cap": market_cap,

            "liquidity": liquidity,

            "volume_24h": volume,

            "address": (
                token.get("address")
                or address
            ),

            "pair_address": (
                pair.get("pairAddress")
            ),

            "created_at": created_at,

            "age": calculate_age(
                created_at
            ),

            "url": pair.get("url"),

            "bubblemaps": (
                make_bubblemaps_url(
                    chain,
                    token.get("address")
                    or address
                )
            ),
        })

    return matches


def scan_new_coins():
    profiles = get_token_profiles()

    if not isinstance(
        profiles,
        list
    ):
        return []

    results = []

    # Scan multiple tokens at the same time.
    # This makes /snipe much faster.
    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:

        futures = [
            executor.submit(
                scan_token_profile,
                profile
            )
            for profile in profiles
        ]

        for future in as_completed(
            futures
        ):
            try:
                results.extend(
                    future.result()
                )
            except Exception:
                continue

    # Remove duplicate pairs.
    unique = {}

    for coin in results:

        key = (
            coin.get("chain"),
            coin.get("pair_address"),
            coin.get("address")
        )

        unique[key] = coin

    results = list(
        unique.values()
    )

    # Newest pairs first.
    results.sort(
        key=lambda coin: (
            coin.get("created_at")
            or 0
        ),
        reverse=True
    )

    # Return the newest 20 matches.
    return results[:20]


async def snipe_scan():
    return await asyncio.to_thread(
        scan_new_coins
    )

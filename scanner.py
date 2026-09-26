import asyncio
import json
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
# ============================================================
# SETTINGS
# ============================================================
MIN_MARKET_CAP = 1_000
MAX_MARKET_CAP = 500_000
COINS_PER_CHAIN = 10
TARGET_CHAINS = {
    "solana": "Solana",
    "robinhood": "Robinhood Chain",
}
# ============================================================
# FOMO CHAIN MAPPING
# ============================================================
FOMO_CHAINS = {
    "solana": "solana",
    "robinhood": "robinhood",
}
# ============================================================
# BUBBLEMAPS CHAIN MAPPING
# ============================================================
BUBBLEMAPS_CHAINS = {
    "solana": "solana",
    "robinhood": "robinhood",
}
# ============================================================
# HTTP REQUEST
# ============================================================
def fetch_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "FOMO-Discord-Bot/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(
        request,
        timeout=15
    ) as response:
        return json.loads(
            response.read().decode("utf-8")
        )
# ============================================================
# DEXSCREENER TOKEN PROFILES
# ============================================================
def get_token_profiles():
    url = (
        "https://api.dexscreener.com/"
        "token-profiles/latest/v1"
    )
    return fetch_json(url)
# ============================================================
# DEXSCREENER TOKEN PAIRS
# ============================================================
def get_token_pairs(
    chain_id,
    token_address
):
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
    return [
        pair
        for pair in pairs
        if pair.get("chainId") == chain_id
    ]
# ============================================================
# CHAIN NAME
# ============================================================
def get_chain_name(chain_id):
    return TARGET_CHAINS.get(
        chain_id,
        chain_id or "Unknown"
    )
# ============================================================
# CREATION TIME
# ============================================================
def format_created_time(timestamp):
    if not timestamp:
        return "Unknown"
    try:
        created = datetime.fromtimestamp(
            timestamp / 1000,
            tz=timezone.utc
        )
        eastern = ZoneInfo(
            "America/New_York"
        )
        created = created.astimezone(
            eastern
        )
        try:
            return created.strftime(
                "%b %d, %Y at %-I:%M %p ET"
            )
        except ValueError:
            return created.strftime(
                "%b %d, %Y at %I:%M %p ET"
            ).lstrip("0")
    except Exception:
        return "Unknown"
# ============================================================
# RUNNING TIME / AGE
# ============================================================
def calculate_age(timestamp):
    if not timestamp:
        return "Unknown"
    try:
        created = datetime.fromtimestamp(
            timestamp / 1000,
            tz=timezone.utc
        )
        now = datetime.now(
            timezone.utc
        )
        seconds = int(
            (now - created).total_seconds()
        )
        if seconds < 0:
            return "Unknown"
        minutes = seconds // 60
        if minutes < 1:
            return "Less than 1 minute"
        if minutes < 60:
            return (
                f"{minutes} minute(s)"
            )
        hours = minutes // 60
        if hours < 24:
            remaining_minutes = (
                minutes % 60
            )
            if remaining_minutes:
                return (
                    f"{hours} hour(s), "
                    f"{remaining_minutes} minute(s)"
                )
            return f"{hours} hour(s)"
        days = hours // 24
        remaining_hours = (
            hours % 24
        )
        if remaining_hours:
            return (
                f"{days} day(s), "
                f"{remaining_hours} hour(s)"
            )
        return f"{days} day(s)"
    except Exception:
        return "Unknown"
# ============================================================
# FOMO URL
# ============================================================
def make_fomo_url(
    chain,
    address
):
    fomo_chain = FOMO_CHAINS.get(
        chain
    )
    if not fomo_chain or not address:
        return None
    encoded_address = urllib.parse.quote(
        str(address),
        safe=""
    )
    return (
        "https://fomo.family/tokens/"
        f"{fomo_chain}/{encoded_address}"
    )
# ============================================================
# BUBBLEMAPS URL
# ============================================================
def make_bubblemaps_url(
    chain,
    address
):
    bubble_chain = (
        BUBBLEMAPS_CHAINS.get(
            chain
        )
    )
    if not bubble_chain or not address:
        return None
    encoded_address = urllib.parse.quote(
        str(address),
        safe=""
    )
    return (
        "https://v2.bubblemaps.io/map"
        f"?chain={bubble_chain}"
        f"&address={encoded_address}"
        "&partnerId=regular"
    )
# ============================================================
# WEBSITE EXTRACTION
# ============================================================
def extract_website(
    profile,
    pair,
    token
):
    possible_objects = [
        profile,
        pair,
        token,
        profile.get("info")
        if isinstance(profile, dict)
        else None,
        pair.get("info")
        if isinstance(pair, dict)
        else None,
        token.get("info")
        if isinstance(token, dict)
        else None,
    ]
    for obj in possible_objects:
        if not isinstance(
            obj,
            dict
        ):
            continue
        websites = obj.get(
            "websites"
        )
        if isinstance(
            websites,
            list
        ):
            for website in websites:
                if isinstance(
                    website,
                    str
                ):
                    url = website.strip()
                    if url.startswith(
                        "http://"
                    ) or url.startswith(
                        "https://"
                    ):
                        return url
                elif isinstance(
                    website,
                    dict
                ):
                    url = (
                        website.get("url")
                        or website.get("link")
                    )
                    if url:
                        url = str(
                            url
                        ).strip()
                        if url.startswith(
                            "http://"
                        ) or url.startswith(
                            "https://"
                        ):
                            return url
        direct_website = (
            obj.get("website")
            or obj.get("websiteUrl")
            or obj.get("websiteURL")
        )
        if direct_website:
            direct_website = str(
                direct_website
            ).strip()
            if direct_website.startswith(
                "http://"
            ) or direct_website.startswith(
                "https://"
            ):
                return direct_website
    return None
# ============================================================
# SCAN ONE TOKEN PROFILE
# ============================================================
def scan_token_profile(
    profile,
    website_only=False
):
    if not isinstance(
        profile,
        dict
    ):
        return []
    chain = profile.get(
        "chainId"
    )
    address = profile.get(
        "tokenAddress"
    )
    # ONLY Solana and Robinhood Chain.
    if chain not in TARGET_CHAINS:
        return []
    if not address:
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
        if not isinstance(
            pair,
            dict
        ):
            continue
        if pair.get(
            "chainId"
        ) != chain:
            continue
        market_cap = pair.get(
            "marketCap"
        )
        if market_cap is None:
            market_cap = pair.get(
                "fdv"
            )
        if market_cap is None:
            continue
        try:
            market_cap = float(
                market_cap
            )
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
        token = (
            pair.get("baseToken")
            or {}
        )
        token_address = (
            token.get("address")
            or address
        )
        name = (
            token.get("name")
            or "Unknown"
        )
        symbol = (
            token.get("symbol")
            or "???"
        )
        liquidity_data = (
            pair.get("liquidity")
            or {}
        )
        liquidity = (
            liquidity_data.get(
                "usd",
                0
            )
        )
        volume_data = (
            pair.get("volume")
            or {}
        )
        volume = (
            volume_data.get(
                "h24",
                0
            )
        )
        created_at = pair.get(
            "pairCreatedAt"
        )
        website = extract_website(
            profile,
            pair,
            token
        )
        if website_only and not website:
            continue
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
            "address": token_address,
            "pair_address": pair.get(
                "pairAddress"
            ),
            "created_at": created_at,
            "created_time": format_created_time(
                created_at
            ),
            "age": calculate_age(
                created_at
            ),
            "url": pair.get(
                "url"
            ),
            "fomo_url": make_fomo_url(
                chain,
                token_address
            ),
            "bubblemaps": make_bubblemaps_url(
                chain,
                token_address
            ),
            "website": website,
        })
    return matches
# ============================================================
# SCAN COINS
# ============================================================
def scan_new_coins(
    website_only=False
):
    try:
        profiles = get_token_profiles()
    except Exception as error:
        print(
            "DEXSCREENER PROFILE ERROR | "
            f"{type(error).__name__} | "
            f"{error}",
            flush=True
        )
        return []
    if not isinstance(
        profiles,
        list
    ):
        return []
    target_profiles = []
    for profile in profiles:
        if not isinstance(
            profile,
            dict
        ):
            continue
        chain = profile.get(
            "chainId"
        )
        if chain in TARGET_CHAINS:
            target_profiles.append(
                profile
            )
    print(
        "SCANNER PROFILES | "
        f"TOTAL={len(profiles)} | "
        f"TARGET={len(target_profiles)} | "
        f"WEBSITE_ONLY={website_only}",
        flush=True
    )
    results = []
    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:
        futures = [
            executor.submit(
                scan_token_profile,
                profile,
                website_only
            )
            for profile
            in target_profiles
        ]
        for future in as_completed(
            futures
        ):
            try:
                matches = future.result()
                if matches:
                    results.extend(
                        matches
                    )
            except Exception as error:
                print(
                    "TOKEN SCAN ERROR | "
                    f"{type(error).__name__} | "
                    f"{error}",
                    flush=True
                )
    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================
    unique = {}
    for coin in results:
        key = (
            coin.get("chain"),
            coin.get("pair_address"),
            coin.get("address"),
        )
        unique[key] = coin
    results = list(
        unique.values()
    )
    # ========================================================
    # NEWEST FIRST
    # ========================================================
    results.sort(
        key=lambda coin: (
            coin.get("created_at")
            or 0
        ),
        reverse=True
    )
    # ========================================================
    # 10 SOLANA + 10 ROBINHOOD
    # ========================================================
    solana = [
        coin
        for coin in results
        if coin.get("chain") == "solana"
    ]
    robinhood = [
        coin
        for coin in results
        if coin.get("chain") == "robinhood"
    ]
    solana = solana[
        :COINS_PER_CHAIN
    ]
    robinhood = robinhood[
        :COINS_PER_CHAIN
    ]
    # ========================================================
    # INTERLEAVE THE TWO CHAINS
    # ========================================================
    final_results = []
    for index in range(
        COINS_PER_CHAIN
    ):
        if index < len(solana):
            final_results.append(
                solana[index]
            )
        if index < len(robinhood):
            final_results.append(
                robinhood[index]
            )
    print(
        "SCANNER RESULTS | "
        f"SOLANA={len(solana)} | "
        f"ROBINHOOD={len(robinhood)} | "
        f"TOTAL={len(final_results)}",
        flush=True
    )
    return final_results
# ============================================================
# /SNIPE SCANNER
# ============================================================
async def snipe_scan():
    return await asyncio.to_thread(
        scan_new_coins,
        False
    )
# ============================================================
# /WEBSITECOINS SCANNER
# ============================================================
async def websitecoins_scan():
    return await asyncio.to_thread(
        scan_new_coins,
        True
    )

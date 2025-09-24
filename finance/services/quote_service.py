from __future__ import annotations

import os
import time
from typing import Dict, Optional

import requests


class QuoteService:
    """
    Fetches FX IRR prices from Alanchand API and caches briefly.

    Exposes conservative side-aware pricing helpers for our conversion rules.
    """

    API_URL = 'https://api.alanchand.com/?type=currencies'
    ENV_TOKEN_KEY = 'ALANCHAND_TOKEN'
    DEFAULT_TOKEN = 'eKrXTBlJdgHBhdaHpYeS'

    _cache: Dict[str, Dict] = {}
    _cache_ts: float = 0.0
    _ttl_seconds: int = 90

    @classmethod
    def _get_token(cls) -> str:
        return os.environ.get(cls.ENV_TOKEN_KEY, cls.DEFAULT_TOKEN)

    @classmethod
    def _fetch_prices(cls) -> Dict[str, Dict]:
        token = cls._get_token()
        url = f"{cls.API_URL}&token={token}"
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json() or {}
        # Normalize keys to lower-case
        return {str(k).lower(): v for k, v in data.items()}

    @classmethod
    def _ensure_cache(cls) -> None:
        now = time.time()
        if not cls._cache or (now - cls._cache_ts) > cls._ttl_seconds:
            cls._cache = cls._fetch_prices()
            cls._cache_ts = now

    @classmethod
    def get_price(cls, symbol: str, side: str) -> Optional[float]:
        """
        Return IRR price for given symbol and side.
        side: 'buy' (we buy from user; user sells), 'sell' (we sell to user; user buys)
        """
        if not symbol:
            return None
        sym = symbol.lower()
        if sym in ('rial', 'irr'):
            return 1.0
        cls._ensure_cache()
        entry = cls._cache.get(sym)
        if not entry:
            return None
        # API provides integers; ensure float
        if side == 'buy':
            return float(entry.get('buy') or 0) or None
        if side == 'sell':
            return float(entry.get('sell') or 0) or None
        return None

    @staticmethod
    def map_account_type_to_symbol(account_type: str) -> str:
        mapping = {
            'rial': 'irr',
            'usd': 'usd',
            'eur': 'eur',
            'gbp': 'gbp',
            # Gold not provided by this API; return empty to signal unsupported
            'gold': '',
        }
        return mapping.get((account_type or '').lower(), '')

    @classmethod
    def compute_destination_amount(
        cls,
        amount: float,
        source_account_type: str,
        destination_account_type: str,
    ) -> Dict[str, Optional[float]]:
        """
        Compute destination amount based on IRR prices using conservative sides:
        - rial -> FX: dest = amount / sell(dest)
        - FX -> rial: dest = amount * buy(source)
        - FX -> FX: dest = amount * buy(source) / sell(dest)
        Returns dict with keys: destination_amount, exchange_rate, source_price_irr, dest_price_irr
        exchange_rate is set for rial<->fx as the single used price.
        """
        src_sym = cls.map_account_type_to_symbol(source_account_type)
        dst_sym = cls.map_account_type_to_symbol(destination_account_type)

        result = {
            'destination_amount': None,
            'exchange_rate': None,
            'source_price_irr': None,
            'dest_price_irr': None,
        }

        if not source_account_type or not destination_account_type:
            return result

        # Same currency
        if (source_account_type or '').lower() == (destination_account_type or '').lower():
            result['destination_amount'] = float(amount)
            return result

        # Rial <-> FX
        if src_sym in ('irr',) and dst_sym not in ('', 'irr'):
            sell_price = cls.get_price(dst_sym, side='sell')
            if not sell_price or sell_price <= 0:
                return result
            result['exchange_rate'] = sell_price
            result['destination_amount'] = float(amount) / sell_price
            return result

        if dst_sym in ('irr',) and src_sym not in ('', 'irr'):
            buy_price = cls.get_price(src_sym, side='buy')
            if not buy_price or buy_price <= 0:
                return result
            result['exchange_rate'] = buy_price
            result['destination_amount'] = float(amount) * buy_price
            return result

        # FX <-> FX (via IRR): use buy on source, sell on dest
        if src_sym not in ('', 'irr') and dst_sym not in ('', 'irr'):
            buy_src = cls.get_price(src_sym, side='buy')
            sell_dst = cls.get_price(dst_sym, side='sell')
            if not buy_src or buy_src <= 0 or not sell_dst or sell_dst <= 0:
                return result
            result['source_price_irr'] = buy_src
            result['dest_price_irr'] = sell_dst
            result['destination_amount'] = float(amount) * (buy_src / sell_dst)
            return result

        # Unsupported (e.g., gold)
        return result



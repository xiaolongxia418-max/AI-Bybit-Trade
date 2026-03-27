#!/usr/bin/env python3
"""
AI Bybit Trade - Ultimate Edition
Complete Bybit API wrapper for AI Agents.
Covers: Trading, Lending, Flash Loan, Transfer, Margin, and more.
"""
from __future__ import annotations

import os
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import ccxt
import requests


# ============================================================
# Exceptions
# ============================================================

class BybitAPIError(Exception):
    """Bybit API error."""
    pass


class InsufficientBalanceError(Exception):
    """Insufficient balance."""
    pass


# ============================================================
# Main Class
# ============================================================

class AIBybit:
    """
    Complete Bybit API wrapper for AI Agents.
    
    Organized into modules:
    - trading: Spot, Futures, Perpetual, Options
    - lending: Earn, Savings, Dual Currency
    - loan: Crypto-backed loans
    - transfer: Flash, Internal, Deposit, Withdraw
    - margin: Cross/Isolated margin
    - info: Balance, Positions, Prices
    """
    
    def __init__(
        self,
        api_key: str = None,
        api_secret: str = None,
        testnet: bool = False
    ):
        self.api_key = api_key or os.getenv("BYBIT_API_KEY", "")
        self.api_secret = api_secret or os.getenv("BYBIT_API_SECRET", "")
        self.testnet = testnet
        
        if not self.api_key or not self.api_secret:
            raise ValueError(
                "API keys required. Set BYBIT_API_KEY and BYBIT_API_SECRET "
                "as environment variables, or pass them to constructor."
            )
        
        self.exchange = self._create_exchange()
        self.exchange.load_markets()
    
    def _create_exchange(self) -> ccxt.Exchange:
        config = {
            "enableRateLimit": True,
            "apiKey": self.api_key,
            "secret": self.api_secret,
            "options": {"defaultType": "swap"},
        }
        
        if self.testnet:
            config["urls"] = {
                "api": "https://api-testnet.bybit.com"
            }
        
        return ccxt.bybit(config)
    
    def _retry_call(self, fn, *args, **kwargs):
        delay = 1.0
        for i in range(5):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                if "RateLimit" in str(e) or "Too many requests" in str(e):
                    time.sleep(delay)
                    delay = min(delay * 2, 30)
                    continue
                raise
        raise RuntimeError("Max retries exceeded")
    
    def _round_amount(self, symbol: str, amount: float) -> float:
        try:
            return float(self.exchange.amount_to_precision(symbol, amount))
        except Exception:
            return float(amount)
    
    def _round_price(self, symbol: str, price: float) -> float:
        try:
            return float(self.exchange.price_to_precision(symbol, price))
        except Exception:
            return float(price)
    
    # ============================================================
    # INFO - Account & Market Information
    # ============================================================
    
    def balance(self, coin: str = "USDT") -> float:
        """Get balance for a coin. Default USDT."""
        bal = self._retry_call(self.exchange.fetch_balance)
        if coin.upper() in bal:
            b = bal[coin.upper()]
            if isinstance(b, dict):
                return float(b.get("free") or 0)
            return float(b)
        return float(bal.get("free", {}).get(coin.upper(), 0))
    
    def total_balance(self, coin: str = "USDT") -> float:
        """Get total balance (free + used) for a coin."""
        bal = self._retry_call(self.exchange.fetch_balance)
        if coin.upper() in bal:
            b = bal[coin.upper()]
            if isinstance(b, dict):
                return float(b.get("total") or 0)
            return float(b)
        return 0.0
    
    def price(self, symbol: str) -> float:
        """Get current price for symbol."""
        ticker = self._retry_call(
            self.exchange.fetch_ticker, 
            symbol.upper().strip()
        )
        return float(ticker.get("last") or ticker.get("close") or 0)
    
    def order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """Get order book."""
        ob = self._retry_call(
            self.exchange.fetch_order_book,
            symbol.upper().strip(), limit
        )
        return {
            "bids": ob.get("bids", [])[:limit],
            "asks": ob.get("asks", [])[:limit],
            "timestamp": ob.get("timestamp")
        }
    
    def positions(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get open positions. If symbol is None, returns all."""
        try:
            raw = self._retry_call(self.exchange.fetch_positions)
        except Exception:
            raw = self._retry_call(
                self.exchange.fetch_positions,
                None, {"category": "linear"}
            )
        
        positions = []
        for pos in raw:
            contracts = pos.get("contracts") or pos.get("size") or 0
            if float(contracts) == 0:
                continue
            if symbol and pos.get("symbol", "").upper() != symbol.upper():
                continue
            
            positions.append({
                "symbol": pos.get("symbol"),
                "side": pos.get("side", "").upper(),
                "amount": float(contracts),
                "entry_price": float(pos.get("entryPrice") or pos.get("average") or 0),
                "leverage": float(pos.get("leverage") or 1),
                "unrealized_pnl": float(pos.get("unrealizedPnl") or 0),
                "timestamp": pos.get("timestamp")
            })
        
        return positions
    
    def open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get open orders."""
        if symbol:
            orders = self._retry_call(
                self.exchange.fetch_open_orders,
                symbol.upper()
            )
        else:
            # Fetch for all symbols - need to iterate
            orders = []
            for sym in self.exchange.markets.keys():
                try:
                    o = self._retry_call(
                        self.exchange.fetch_open_orders, sym
                    )
                    orders.extend(o)
                except Exception:
                    pass
        return orders
    
    def trade_history(self, symbol: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trade history."""
        if symbol:
            return self._retry_call(
                self.exchange.fetch_my_trades,
                symbol.upper(), None, limit
            )
        return []
    
    # ============================================================
    # TRADING - Spot & Futures
    # ============================================================
    
    def buy(
        self,
        symbol: str,
        amount: float,
        stop_loss: float = None,
        take_profit: float = None,
        slippage: float = None
    ) -> Dict[str, Any]:
        """Open a LONG position (market order)."""
        symbol = symbol.upper().strip()
        amount = self._round_amount(symbol, amount)
        
        if amount <= 0:
            raise ValueError(f"Invalid amount: {amount}")
        
        params = {"category": "linear"}
        
        if stop_loss:
            params["stopLoss"] = self._round_price(symbol, stop_loss)
            params["triggerDirection"] = 2
        
        if take_profit:
            params["takeProfit"] = self._round_price(symbol, take_profit)
        
        order = self._retry_call(
            self.exchange.create_order,
            symbol, "market", "buy", amount, None, params
        )
        
        return {
            "success": True,
            "order_id": order.get("id"),
            "symbol": symbol,
            "side": "BUY",
            "amount": amount,
            "price": order.get("average") or order.get("price"),
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "timestamp": order.get("timestamp")
        }
    
    def sell(
        self,
        symbol: str,
        amount: float,
        stop_loss: float = None,
        take_profit: float = None
    ) -> Dict[str, Any]:
        """Open a SHORT position (market order)."""
        symbol = symbol.upper().strip()
        amount = self._round_amount(symbol, amount)
        
        if amount <= 0:
            raise ValueError(f"Invalid amount: {amount}")
        
        params = {"category": "linear"}
        
        if stop_loss:
            params["stopLoss"] = self._round_price(symbol, stop_loss)
            params["triggerDirection"] = 1
        
        if take_profit:
            params["takeProfit"] = self._round_price(symbol, take_profit)
        
        order = self._retry_call(
            self.exchange.create_order,
            symbol, "market", "sell", amount, None, params
        )
        
        return {
            "success": True,
            "order_id": order.get("id"),
            "symbol": symbol,
            "side": "SELL",
            "amount": amount,
            "price": order.get("average") or order.get("price"),
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "timestamp": order.get("timestamp")
        }
    
    def close(self, symbol: str) -> Dict[str, Any]:
        """Close a position (any direction)."""
        symbol = symbol.upper().strip()
        
        positions = self.positions(symbol)
        if not positions:
            return {"success": False, "message": "No open position"}
        
        position = positions[0]
        side = position["side"]
        amount = position["amount"]
        
        close_side = "sell" if side == "LONG" else "buy"
        
        order = self._retry_call(
            self.exchange.create_order,
            symbol, "market", close_side, amount,
            None, {"reduceOnly": True, "category": "linear"}
        )
        
        return {
            "success": True,
            "order_id": order.get("id"),
            "symbol": symbol,
            "closed_side": side,
            "amount": amount,
            "price": order.get("average") or order.get("price"),
            "timestamp": order.get("timestamp")
        }
    
    def close_all(self) -> List[Dict[str, Any]]:
        """Close all open positions."""
        results = []
        for pos in self.positions():
            result = self.close(pos["symbol"])
            results.append(result)
        return results
    
    def set_leverage(self, symbol: str, leverage: float) -> Dict[str, Any]:
        """Set leverage for a symbol. Range: 1-125x."""
        symbol = symbol.upper().strip()
        leverage = max(1, min(float(leverage), 125))
        
        try:
            self._retry_call(
                self.exchange.set_leverage, leverage, symbol
            )
            return {"success": True, "leverage": leverage}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel a specific order."""
        try:
            self._retry_call(
                self.exchange.cancel_order,
                order_id, symbol.upper()
            )
            return {"success": True, "order_id": order_id}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def cancel_all_orders(self, symbol: str = None) -> Dict[str, Any]:
        """Cancel all open orders for a symbol, or all symbols."""
        try:
            if symbol:
                self._retry_call(
                    self.exchange.cancel_all_orders,
                    symbol.upper()
                )
            else:
                # Cancel all - need to do per symbol
                for sym in self.exchange.markets.keys():
                    try:
                        self._retry_call(
                            self.exchange.cancel_all_orders, sym
                        )
                    except Exception:
                        pass
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============================================================
    # TRANSFER - Internal & External
    # ============================================================
    
    def transfer(
        self,
        coin: str,
        amount: float,
        from_account: str,
        to_account: str
    ) -> Dict[str, Any]:
        """
        Transfer between accounts.
        
        Account types:
        - SPOT
        - LINEAR (USDT Perpetual)
        - INVERSE
        - OPTION
        - UNIFIED
        
        Examples:
        - transfer("USDT", 100, "SPOT", "LINEAR")  # Spot to Futures
        - transfer("USDT", 100, "LINEAR", "SPOT")  # Futures to Spot
        """
        try:
            result = self.exchange.transfer(
                coin.upper(), amount, from_account.upper(), to_account.upper()
            )
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def flash_transfer(
        self,
        coin: str,
        amount: float,
        to_user_id: str = None,
        to_account_type: str = None
    ) -> Dict[str, Any]:
        """
        Flash transfer (instant, no fees within Bybit).
        
        Use for:
        - Splitting funds to sub-accounts
        - Moving funds quickly between accounts
        
        Note: Requires specific API permissions.
        """
        # Flash transfer via private API
        params = {
            "transferId": self.exchange.uuid16(),
            "timestamp": int(time.time() * 1000)
        }
        
        if to_user_id:
            params["toUserId"] = to_user_id
        
        try:
            result = self.exchange.privatePostV5AssetTransferUniversalTransfer({
                "coin": coin.upper(),
                "amount": str(amount),
                "fromAccountType": "UNIFIED",
                "toAccountType": to_account_type.upper() if to_account_type else "UNIFIED",
                **params
            })
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def deposit_address(self, coin: str, network: str = None) -> Dict[str, Any]:
        """Get deposit address for a coin."""
        try:
            addr = self._retry_call(
                self.exchange.fetch_deposit_address,
                coin.upper(),
                {"network": network} if network else None
            )
            return {
                "success": True,
                "address": addr.get("address"),
                "tag": addr.get("tag"),
                "network": addr.get("network"),
                "coin": coin.upper()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def withdraw(
        self,
        coin: str,
        amount: float,
        address: str,
        network: str = None,
        tag: str = None
    ) -> Dict[str, Any]:
        """
        Withdraw coins to external wallet.
        
        Warning: This is irreversible. Double-check address!
        """
        try:
            params = {"address": address}
            if network:
                params["network"] = network
            if tag:
                params["to"] = tag
            
            result = self._retry_call(
                self.exchange.withdraw,
                coin.upper(), amount, address, params
            )
            return {
                "success": True,
                "withdraw_id": result.get("id"),
                "coin": coin.upper(),
                "amount": amount,
                "address": address,
                "timestamp": result.get("timestamp")
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============================================================
    # LENDING - Earn & Savings
    # ============================================================
    
    def lending_purchase(
        self,
        coin: str,
        amount: float,
        product_id: str = "all"
    ) -> Dict[str, Any]:
        """
        Purchase flexible savings/lending.
        
        Use for:
        - Flexible savings (earn interest on holdings)
        - Auto-invest features
        
        Note: Bybit lending features require specific API permissions.
        """
        try:
            # Try unified lending endpoint
            result = self.exchange.privatePostV5LendingPurchase({
                "coin": coin.upper(),
                "amount": str(amount)
            })
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def lending_redeem(
        self,
        coin: str,
        amount: float,
        auto: bool = False
    ) -> Dict[str, Any]:
        """
        Redeem from flexible savings.
        
        auto: If True, automatic redemption (no interest)
        """
        try:
            result = self.exchange.privatePostV5LendingRedeem({
                "coin": coin.upper(),
                "amount": str(amount),
                "auto": auto
            })
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def lending_balance(self, coin: str = None) -> Dict[str, Any]:
        """Get lending/savings balance."""
        try:
            result = self.exchange.privateGetV5LendingAccount({
                "coin": coin.upper() if coin else None
            })
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============================================================
    # CRYPTO LOAN - Borrow Against Assets
    # ============================================================
    
    def loan_borrow(
        self,
        coin: str,
        amount: float,
        collateral_coin: str = "BTC",
        collateral_amount: float = None
    ) -> Dict[str, Any]:
        """
        Borrow USDT using crypto as collateral.
        
        Useful for:
        - Getting liquidity without selling assets
        - Leveraged positions
        
        Note: High risk - liquidation possible!
        """
        try:
            # Flexible borrow
            result = self.exchange.privatePostV5CryptoLoanFlexibleBorrow({
                "borrowCoin": coin.upper(),
                "borrowAmount": str(amount),
                "collateralCoin": collateral_coin.upper(),
                "collateralAmount": str(collateral_amount) if collateral_amount else None
            })
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def loan_repay(
        self,
        borrow_order_id: str,
        coin: str = None,
        amount: float = None
    ) -> Dict[str, Any]:
        """Repay a crypto loan."""
        try:
            params = {"orderId": borrow_order_id}
            if coin:
                params["coin"] = coin.upper()
            if amount:
                params["amount"] = str(amount)
            
            result = self.exchange.privatePostV5CryptoLoanRepay(params)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def loan_adjust_ltv(
        self,
        order_id: str,
        collateral_amount: float = None,
        borrow_amount: float = None
    ) -> Dict[str, Any]:
        """Adjust LTV (add/remove collateral or borrow more)."""
        try:
            params = {"orderId": order_id}
            if collateral_amount:
                params["adjustCollateralAmount"] = str(collateral_amount)
            if borrow_amount:
                params["adjustBorrowAmount"] = str(borrow_amount)
            
            result = self.exchange.privatePostV5CryptoLoanAdjustLtv(params)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def loan_balance(self) -> List[Dict[str, Any]]:
        """Get all crypto loan positions."""
        try:
            result = self.exchange.privateGetV5CryptoLoanOngoingOrders({})
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============================================================
    # MARGIN - Cross & Isolated
    # ============================================================
    
    def margin_borrow(
        self,
        coin: str,
        amount: float,
        symbol: str = None,
        isolated: bool = False
    ) -> Dict[str, Any]:
        """Borrow on margin (cross or isolated)."""
        try:
            params = {"coin": coin.upper(), "amount": str(amount)}
            if symbol:
                params["symbol"] = symbol.upper()
            
            if isolated:
                result = self.exchange.borrow_isolated_margin(symbol.upper(), coin.upper(), amount)
            else:
                result = self.exchange.borrow_cross_margin(coin.upper(), amount)
            
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def margin_repay(
        self,
        coin: str,
        amount: float,
        symbol: str = None,
        isolated: bool = False
    ) -> Dict[str, Any]:
        """Repay margin borrow."""
        try:
            params = {"coin": coin.upper(), "amount": str(amount)}
            if symbol:
                params["symbol"] = symbol.upper()
            
            if isolated:
                # Isolated repay
                result = self.exchange.privatePostV5AccountBorrow({
                    "coin": coin.upper(),
                    "amount": str(amount),
                    "symbol": symbol.upper()
                })
            else:
                result = self.exchange.privatePostV5AccountBorrow({
                    "coin": coin.upper(),
                    "amount": str(amount)
                })
            
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============================================================
    # UTILITY
    # ============================================================
    
    def leverage_tokens_purchase(
        self,
        symbol: str,
        amount: float
    ) -> Dict[str, Any]:
        """Purchase leverage tokens (e.g., BTCUP)."""
        try:
            result = self.exchange.privatePostV5SpotLeverTokenPurchase({
                "symbol": symbol.upper(),
                "amount": str(amount)
            })
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def leverage_tokens_redeem(
        self,
        symbol: str,
        amount: float
    ) -> Dict[str, Any]:
        """Redeem leverage tokens."""
        try:
            result = self.exchange.privatePostV5SpotLeverTokenRedeem({
                "symbol": symbol.upper(),
                "amount": str(amount)
            })
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def set_spot_hedge(self, symbol: str, enabled: bool = True) -> Dict[str, Any]:
        """Enable/disable spot hedge mode for futures account."""
        try:
            result = self.exchange.privatePostV5PositionSwitchMode({
                "symbol": symbol.upper(),
                "mode": 3 if enabled else 0,  # 3 = hedge, 0 = one-way
                "category": "linear"
            })
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============================================================
    # WALLET - Full Balance Report
    # ============================================================
    
    def wallet_balance(self, account_type: str = "UNIFIED") -> Dict[str, Any]:
        """
        Get full wallet balance breakdown.
        
        account_type: UNIFIED, SPOT, CONTRACT, OPTION
        """
        try:
            result = self.exchange.privateGetV5AccountWalletBalance({
                "accountType": account_type.upper()
            })
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def all_balances(self) -> Dict[str, Dict[str, float]]:
        """Get all coin balances across all account types."""
        balances = {}
        
        for acc_type in ["UNIFIED", "SPOT", "CONTRACT"]:
            try:
                result = self.wallet_balance(acc_type)
                if result.get("success"):
                    data = result.get("result", {}).get("list", [{}])[0]
                    coins = data.get("coin", [])
                    for coin in coins:
                        c = coin.get("coin", "")
                        equity = float(coin.get("equity", 0))
                        if equity > 0:
                            balances[c] = balances.get(c, 0) + equity
            except Exception:
                pass
        
        return balances
    
    # ============================================================
    # STRATEGY HELPERS (For AI to use)
    # ============================================================
    
    def dca(
        self,
        symbol: str,
        amount: float,
        intervals: int = 4,
        direction: str = "buy"
    ) -> List[Dict[str, Any]]:
        """
        Dollar Cost Averaging - spread buy/sell over multiple orders.
        
        AI can use this to:
        - Buy the dip gradually
        - Sell into strength gradually
        """
        results = []
        per_order = amount / intervals
        
        for i in range(intervals):
            try:
                if direction.lower() == "buy":
                    result = self.buy(symbol, per_order)
                else:
                    result = self.sell(symbol, per_order)
                results.append(result)
                time.sleep(0.5)  # Avoid rate limits
            except Exception as e:
                results.append({"success": False, "error": str(e)})
        
        return results
    
    def grid_orders(
        self,
        symbol: str,
        lower_price: float,
        upper_price: float,
        grid_count: int = 5,
        amount_per_grid: float = 0.001
    ) -> List[Dict[str, Any]]:
        """
        Create a basic grid of orders.
        
        AI can use this for grid trading strategies.
        """
        results = []
        price_step = (upper_price - lower_price) / grid_count
        
        for i in range(grid_count):
            buy_price = lower_price + (price_step * i)
            sell_price = lower_price + (price_step * (i + 1))
            
            try:
                # Place buy order at this level
                buy_order = self.buy(symbol, amount_per_grid)
                results.append({"grid_level": i, "buy": buy_order})
                
                # Place sell order above
                sell_params = {"category": "linear"}
                sell_order = self.exchange.create_order(
                    symbol.upper(), "limit", "sell",
                    amount_per_grid, sell_price, sell_params
                )
                results.append({"grid_level": i, "sell": sell_order})
                
            except Exception as e:
                results.append({"success": False, "error": str(e)})
        
        return results
    
    def take_profit_limit(
        self,
        symbol: str,
        side: str,
        amount: float,
        take_profit_price: float
    ) -> Dict[str, Any]:
        """Place a take profit limit order."""
        try:
            order_side = "buy" if side.lower() == "short" else "sell"
            params = {
                "category": "linear",
                "reduceOnly": True,
                "triggerDirection": 1 if side.upper() == "LONG" else 2
            }
            
            order = self._retry_call(
                self.exchange.create_order,
                symbol.upper(), "limit", order_side,
                amount, take_profit_price, params
            )
            
            return {"success": True, "order_id": order.get("id")}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def stop_loss_limit(
        self,
        symbol: str,
        side: str,
        amount: float,
        stop_price: float
    ) -> Dict[str, Any]:
        """Place a stop loss limit order."""
        try:
            order_side = "buy" if side.lower() == "short" else "sell"
            params = {
                "category": "linear",
                "reduceOnly": True,
                "triggerDirection": 2 if side.upper() == "LONG" else 1
            }
            
            order = self._retry_call(
                self.exchange.create_order,
                symbol.upper(), "limit", order_side,
                amount, stop_price, params
            )
            
            return {"success": True, "order_id": order.get("id")}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# Aliases for easier use
# ============================================================

class BybitTrader(AIBybit):
    """Alias for AIBybit - backward compatibility."""
    pass


# ============================================================
# CLI Interface
# ============================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Bybit Trade - Ultimate Edition")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Balance
    p_balance = subparsers.add_parser("balance", help="Check balance")
    p_balance.add_argument("--coin", default="USDT", help="Coin to check")
    
    # Positions
    p_positions = subparsers.add_parser("positions", help="Check positions")
    p_positions.add_argument("--symbol", help="Specific symbol")
    
    # Price
    p_price = subparsers.add_parser("price", help="Get price")
    p_price.add_argument("symbol", help="Trading pair")
    
    # Buy
    p_buy = subparsers.add_parser("buy", help="Buy")
    p_buy.add_argument("symbol", help="Trading pair")
    p_buy.add_argument("amount", type=float, help="Amount")
    p_buy.add_argument("--sl", type=float, help="Stop loss price")
    p_buy.add_argument("--tp", type=float, help="Take profit price")
    
    # Sell
    p_sell = subparsers.add_parser("sell", help="Sell")
    p_sell.add_argument("symbol", help="Trading pair")
    p_sell.add_argument("amount", type=float, help="Amount")
    p_sell.add_argument("--sl", type=float, help="Stop loss price")
    p_sell.add_argument("--tp", type=float, help="Take profit price")
    
    # Close
    p_close = subparsers.add_parser("close", help="Close position")
    p_close.add_argument("symbol", help="Trading pair")
    
    # Transfer
    p_transfer = subparsers.add_parser("transfer", help="Transfer between accounts")
    p_transfer.add_argument("coin", help="Coin")
    p_transfer.add_argument("amount", type=float, help="Amount")
    p_transfer.add_argument("from_acc", help="From account")
    p_transfer.add_argument("to_acc", help="To account")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    bybit = AIBybit()
    
    if args.command == "balance":
        bal = bybit.balance(args.coin)
        print(f"Balance: {bal} {args.coin}")
    
    elif args.command == "positions":
        positions = bybit.positions(args.symbol)
        if not positions:
            print("No open positions")
        for p in positions:
            print(f"{p['symbol']} | {p['side']} | {p['amount']} | Entry: {p['entry_price']} | PnL: {p['unrealized_pnl']}")
    
    elif args.command == "price":
        price = bybit.price(args.symbol)
        print(f"{args.symbol}: {price}")
    
    elif args.command == "buy":
        result = bybit.buy(args.symbol, args.amount, args.sl, args.tp)
        print(result)
    
    elif args.command == "sell":
        result = bybit.sell(args.symbol, args.amount, args.sl, args.tp)
        print(result)
    
    elif args.command == "close":
        result = bybit.close(args.symbol)
        print(result)
    
    elif args.command == "transfer":
        result = bybit.transfer(args.coin, args.amount, args.from_acc, args.to_acc)
        print(result)


if __name__ == "__main__":
    main()

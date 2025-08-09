from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Annotated, Optional, Union, Dict
import yfinance as yf
from datetime import datetime, date


class HistoricalBar(BaseModel):
    """Single OHLCV bar of historical price data"""

    open: Optional[float] = Field(default=None, description="Opening price")
    high: Optional[float] = Field(default=None, description="High price")
    low: Optional[float] = Field(default=None, description="Low price")
    close: Optional[float] = Field(default=None, description="Closing price (unadjusted)")
    adj_close: Optional[float] = Field(default=None, description="Adjusted closing price")
    volume: Optional[Union[int, float]] = Field(default=None, description="Trading volume")


class HistoricalPrices(BaseModel):
    """Historical OHLCV data for a symbol and resolution period"""

    symbol: str = Field(description="Stock ticker symbol")
    resolution: str = Field(description="Requested resolution alias (1d,5d,1m,6m,YTD,1y,5y)")
    period: str = Field(description="Actual yfinance period parameter used (e.g. 1d,5d,1mo)")
    bars: Dict[date, HistoricalBar] = Field(description="Mapping of date to historical price bar")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "AAPL",
                "resolution": "1y",
                "period": "1y",
                "bars": {
                    "2024-08-09": {
                        "open": 180.12,
                        "high": 182.45,
                        "low": 178.9,
                        "close": 181.25,
                        "adj_close": 181.10,
                        "volume": 51234567
                    }
                }
            }
        }
    }

def register_stock_history(mcp: FastMCP):
    @mcp.tool(
        name="get_historical_prices",
        title="Get Historical Price Data",
        description=(
            "Return historical OHLCV data for a stock symbol using flexible parameters "
            "(period, interval, start, end)."
        )
    )
    async def get_historical_prices(
        symbol: Annotated[str, Field(
            description="Stock ticker symbol (e.g., AAPL, GOOGL, TSLA)",
            min_length=1,
            max_length=10,
            pattern=r"^[A-Z]{1,10}$"
        )],
        period: Annotated[str, Field(
            description="Period: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max. Default: 1y"
        )] = "1y",
        interval: Annotated[str, Field(
            description="Interval: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo. Default: 1d"
        )] = "1d",
        start: Annotated[Optional[str], Field(
            description="Start date (YYYY-MM-DD), inclusive. Overrides period if specified."
        )] = None,
        end: Annotated[Optional[str], Field(
            description="End date (YYYY-MM-DD), exclusive. Used with start date."
        )] = None
    ) -> HistoricalPrices:
        """Fetch historical OHLCV price data for the given symbol and parameters.

        Supports flexible yfinance parameters.
        Priority: start/end dates > period parameter.
        """
        
        if start is not None or end is not None:
            yf_params = {
                "start": start,
                "end": end,
                "interval": interval
            }
            actual_period = f"start={start}, end={end}"
        else:
            yf_params = {
                "period": period,
                "interval": interval
            }
            actual_period = period

        stock = yf.Ticker(symbol.upper())

        hist = stock.history(**yf_params)

        bars: dict[date, HistoricalBar] = {}

        if not hist.empty:
            for idx, row in hist.iterrows():
                # Get date object for the key
                if hasattr(idx, 'date'):
                    date_key = idx.date()  # type: ignore[attr-defined]
                elif hasattr(idx, 'to_pydatetime'):
                    date_key = idx.to_pydatetime().date()  # type: ignore[attr-defined]
                else:
                    # fallback: parse string to date
                    try:
                        date_key = datetime.fromisoformat(str(idx)[:10]).date()
                    except Exception:
                        date_key = datetime.now().date()

                bars[date_key] = HistoricalBar(
                    open=row.get('Open'),
                    high=row.get('High'),
                    low=row.get('Low'),
                    close=row.get('Close'),
                    adj_close=row.get('Adj Close') if 'Adj Close' in hist.columns else None,
                    volume=row.get('Volume')
                )

        return HistoricalPrices(
            symbol=symbol.upper(),
            resolution=period,
            period=actual_period,
            bars=bars
        )

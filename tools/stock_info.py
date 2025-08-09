from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Annotated, Optional, Union
import yfinance as yf


class StockInfo(BaseModel):
    """Comprehensive stock information model for LLM interactions"""
    
    symbol: str = Field(
        description="Stock ticker symbol (e.g., AAPL, GOOGL, TSLA)"
    )
    
    company_name: Optional[str] = Field(
        default=None,
        description="Full legal name of the company"
    )
    
    current_price: Optional[Union[float, str]] = Field(
        default=None,
        description="Current stock price in USD"
    )
    
    market_cap: Optional[Union[int, str]] = Field(
        default=None,
        description="Market capitalization in USD (total value of all shares)"
    )
    
    pe_ratio: Optional[Union[float, str]] = Field(
        default=None,
        description="Price-to-earnings ratio (stock price divided by earnings per share)"
    )
    
    dividend_yield: Optional[Union[float, str]] = Field(
        default=None,
        description="Annual dividend yield as a percentage of stock price"
    )
    
    fifty_two_week_high: Optional[Union[float, str]] = Field(
        default=None,
        description="Highest stock price in the past 52 weeks",
        alias="52_week_high"
    )
    
    fifty_two_week_low: Optional[Union[float, str]] = Field(
        default=None,
        description="Lowest stock price in the past 52 weeks",
        alias="52_week_low"
    )
    
    sector: Optional[str] = Field(
        default=None,
        description="Business sector the company operates in"
    )
    
    industry: Optional[str] = Field(
        default=None,
        description="Specific industry within the sector"
    )
    
    volume: Optional[Union[int, str]] = Field(
        default=None,
        description="Number of shares traded today"
    )
    
    avg_volume: Optional[Union[int, str]] = Field(
        default=None,
        description="Average daily trading volume over recent period"
    )
    
    beta: Optional[Union[float, str]] = Field(
        default=None,
        description="Stock volatility relative to market (1.0 = same as market)"
    )
    
    book_value: Optional[Union[float, str]] = Field(
        default=None,
        description="Book value per share (company's net worth per share)"
    )
    
    eps: Optional[Union[float, str]] = Field(
        default=None,
        description="Earnings per share (company's profit divided by number of shares)"
    )

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "current_price": 150.25,
                "market_cap": 2500000000000,
                "pe_ratio": 28.5,
                "dividend_yield": 0.0045,
                "52_week_high": 182.94,
                "52_week_low": 124.17,
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "volume": 45000000,
                "avg_volume": 50000000,
                "beta": 1.2,
                "book_value": 4.25,
                "eps": 5.89
            }
        }
    }

def register_stock_info(mcp: FastMCP):
    @mcp.tool(
        name="get_stock_info",
        title="Get Stock Information",
        description="Get comprehensive stock information for any publicly traded company using its ticker symbol"
    )
    async def get_stock_info(
        symbol: Annotated[str, Field(
            description="Stock ticker symbol (e.g., 'AAPL' for Apple, 'GOOGL' for Google, 'TSLA' for Tesla)",
            min_length=1,
            max_length=10,
            pattern=r"^[A-Z]{1,10}$"
        )]
    ) -> StockInfo:
        """
        Fetch comprehensive stock market data for a given ticker symbol.
        
        This tool retrieves real-time and historical stock information including:
        - Current stock price and market capitalization
        - Financial ratios (P/E ratio, dividend yield)
        - Trading metrics (volume, beta)
        - Company information (name, sector, industry)
        - 52-week price range
        
        Args:
            symbol: Stock ticker symbol (will be converted to uppercase)
        
        Returns:
            StockInfo: Comprehensive stock data in a structured format
        """
        stock = yf.Ticker(symbol.upper())
        
        return StockInfo(
            symbol=symbol.upper(),
            company_name=stock.info.get('longName'),
            current_price=stock.info.get('currentPrice'),
            market_cap=stock.info.get('marketCap'),
            pe_ratio=stock.info.get('trailingPE'),
            dividend_yield=stock.info.get('dividendYield'),
            **{"52_week_high": stock.info.get('fiftyTwoWeekHigh')},
            **{"52_week_low": stock.info.get('fiftyTwoWeekLow')},
            sector=stock.info.get('sector'),
            industry=stock.info.get('industry'),
            volume=stock.info.get('volume'),
            avg_volume=stock.info.get('averageVolume'),
            beta=stock.info.get('beta'),
            book_value=stock.info.get('bookValue'),
            eps=stock.info.get('trailingEps')
        )

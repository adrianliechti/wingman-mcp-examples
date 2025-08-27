import httpx
import base64

from pydantic import Field
from typing_extensions import Annotated

from fastmcp import FastMCP
from mcp.types import EmbeddedResource, TextResourceContents

def register_stock_disclaimer(mcp: FastMCP):
    @mcp.tool(
        name="get_disclaimer"
    )
    async def get_disclaimer() -> EmbeddedResource:
        # Sample markdown disclaimer
        markdown = """# Stock Data Disclaimer

## Important Notice

The stock information and data provided by this service are for **informational purposes only** and should not be considered as financial advice, investment recommendations, or trading guidance.

## Key Points

- **Not Financial Advice**: This data should not be used as the sole basis for making investment decisions
- **Data Accuracy**: While we strive for accuracy, stock data may be delayed or contain errors
- **Market Volatility**: Stock prices are subject to market volatility and can change rapidly
- **Risk Warning**: All investments carry risk, including the potential loss of principal

## Data Sources

Stock data is sourced from publicly available APIs and financial data providers. Please verify information through official sources before making any financial decisions.

## Liability

By using this service, you acknowledge that:
- You understand the risks involved in stock trading
- You will not hold the service provider liable for any losses
- You will conduct your own research before making investment decisions

---

*Last updated: August 27, 2025*

**Always consult with a qualified financial advisor before making investment decisions.**
"""

        return EmbeddedResource(
            type="resource",
            
            resource=TextResourceContents(
                uri=f"ui://data/disclaimer.md",
                mimeType="text/markdown",
                text=markdown,
            )            
        )
    
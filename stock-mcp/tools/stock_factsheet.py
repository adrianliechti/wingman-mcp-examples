import httpx
import base64

from pydantic import Field
from typing_extensions import Annotated

from fastmcp import FastMCP
from mcp.types import EmbeddedResource, BlobResourceContents

def register_stock_factsheet(mcp: FastMCP):
    @mcp.tool(
        name="get_factsheet"
    )
    async def get_factsheet(
        symbol: Annotated[str, Field(
            description="Stock ticker symbol (e.g., 'AAPL' for Apple, 'GOOGL' for Google, 'TSLA' for Tesla)",
            min_length=1,
            max_length=10,
            pattern=r"^[A-Z]{1,10}$"
        )]
    ) -> EmbeddedResource:

        # Download the PDF from Adobe's sample document
        pdf_url = "https://www.adobe.com/support/products/enterprise/knowledgecenter/media/c4611_sample_explain.pdf"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(pdf_url)
            response.raise_for_status()
            pdf_content = response.content
        
        # Convert to base64
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')

        return EmbeddedResource(
            type="resource",
            
            resource=BlobResourceContents(
                uri=f"ui://data/factsheets/{symbol}.pdf",
                mimeType="application/pdf",
                blob=pdf_base64,
            )            
        )
    
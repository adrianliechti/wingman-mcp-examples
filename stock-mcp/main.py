from fastmcp import FastMCP

from tools.stock_factsheet import register_stock_factsheet
from tools.stock_disclaimer import register_stock_disclaimer
from tools.stock_info import register_stock_info
from tools.stock_history import register_stock_history
from tools.stock_chart import register_stock_chart

mcp = FastMCP(
    name="stock-info-server",
    version="1.0.0"
)

register_stock_info(mcp)
register_stock_history(mcp)
register_stock_chart(mcp)
register_stock_factsheet(mcp)
register_stock_disclaimer(mcp)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")


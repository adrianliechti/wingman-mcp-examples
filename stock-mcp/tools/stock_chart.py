from pydantic import Field
from typing import Annotated, Optional
import base64

from fastmcp import FastMCP
from mcp.types import EmbeddedResource, BlobResourceContents

import yfinance as yf

def register_stock_chart(mcp: FastMCP):
    @mcp.tool(
        name="render_stock_chart",
        title="Create Interactive Stock Chart",
        description="Create a beautiful, interactive stock price chart that you can view in a browser. Shows price movements over time with hover tooltips and smooth animations. Perfect for visualizing stock performance trends."
    )
    async def render_stock_chart(
        symbol: Annotated[str, Field(
            description="Stock ticker symbol (e.g., AAPL, GOOGL, TSLA)",
            min_length=1,
            max_length=10,
            pattern=r"^[A-Z]{1,10}$"
        )],
        chart_type: Annotated[str, Field(
            description="Type of chart: line, candlestick, area"
        )] = "candlestick",
        period: Annotated[str, Field(
            description="Period: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max. Default: 1mo"
        )] = "1mo",
        interval: Annotated[str, Field(
            description="Interval: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo. Default: 1d"
        )] = "1d",
        start: Annotated[Optional[str], Field(
            description="Start date (YYYY-MM-DD), inclusive. Overrides period if specified."
        )] = None,
        end: Annotated[Optional[str], Field(
            description="End date (YYYY-MM-DD), exclusive. Used with start date."
        )] = None
    ) -> EmbeddedResource:
        """Create a beautiful, interactive stock chart that opens in your browser.
        
        This tool generates a professional-looking chart showing stock price movements
        over time. You can hover over data points to see detailed information, and the
        chart includes price statistics and change indicators. Great for analyzing
        stock performance trends and making investment decisions.
        """
        # Get historical data using the same logic as get_historical_prices
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
        
        # Prepare data for D3.js - best effort approach
        chart_data = []
        if not hist.empty:
            for idx, row in hist.iterrows():
                # Convert pandas timestamp to JavaScript date string
                date_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)[:10]  # type: ignore[attr-defined]
                chart_data.append({
                    'date': date_str,
                    'open': float(row.get('Open', 0)),
                    'high': float(row.get('High', 0)),
                    'low': float(row.get('Low', 0)),
                    'close': float(row.get('Close', 0)),
                    'volume': int(row.get('Volume', 0))
                })
        
        # If no data, create a single dummy data point to avoid chart errors
        if not chart_data:
            chart_data = [{
                'date': '2024-01-01',
                'open': 100,
                'high': 100,
                'low': 100,
                'close': 100,
                'volume': 0
            }]
        
        # Calculate price statistics
        latest_price = chart_data[-1]['close']
        first_price = chart_data[0]['close']
        price_change = latest_price - first_price
        price_change_pct = ((latest_price - first_price) / first_price * 100) if first_price != 0 else 0
        
        # Generate chart-specific D3.js code
        if chart_type.lower() == "line":
            chart_script = """
    // Line chart
    const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.close))
        .curve(d3.curveMonotoneX);

    svg.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "#ff8c00")
        .attr("stroke-width", 2)
        .attr("d", line);

    // Add dots
    svg.selectAll(".dot")
        .data(data)
        .enter().append("circle")
        .attr("class", "dot")
        .attr("cx", d => x(d.date))
        .attr("cy", d => y(d.close))
        .attr("r", 3)
        .attr("fill", "#ff8c00")
        .attr("stroke", "#ffaa33")
        .attr("stroke-width", 1)
        .on("mouseover", function(event, d) {
            d3.select(this).attr("r", 5);
            tooltip.style("opacity", 1)
                .html(`Date: ${d3.timeFormat("%Y-%m-%d")(d.date)}<br/>Close: $${d.close.toFixed(2)}`)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px");
        })
        .on("mouseout", function() {
            d3.select(this).attr("r", 3);
            tooltip.style("opacity", 0);
        });
    """
        elif chart_type.lower() == "candlestick":
            chart_script = """
    // Candlestick chart
    const candleWidth = Math.max(1, (width - marginLeft - marginRight) / data.length * 0.8);

    svg.selectAll(".candle")
        .data(data)
        .enter().append("g")
        .attr("class", "candle")
        .each(function(d) {
            const g = d3.select(this);
            const x_pos = x(d.date);
            const isUp = d.close > d.open;
            
            // High-low line
            g.append("line")
                .attr("x1", x_pos)
                .attr("x2", x_pos)
                .attr("y1", y(d.high))
                .attr("y2", y(d.low))
                .attr("stroke", isUp ? "#00ff00" : "#ff4444")
                .attr("stroke-width", 1);
            
            // Open-close rectangle
            g.append("rect")
                .attr("x", x_pos - candleWidth/2)
                .attr("y", y(Math.max(d.open, d.close)))
                .attr("width", candleWidth)
                .attr("height", Math.abs(y(d.open) - y(d.close)))
                .attr("fill", isUp ? "#00ff00" : "#ff4444")
                .attr("stroke", isUp ? "#33ff33" : "#ff6666")
                .attr("stroke-width", 0.5)
                .on("mouseover", function(event) {
                    d3.select(this).attr("stroke-width", 2);
                    tooltip.style("opacity", 1)
                        .html(`Date: ${d3.timeFormat("%Y-%m-%d")(d.date)}<br/>Open: $${d.open.toFixed(2)}<br/>High: $${d.high.toFixed(2)}<br/>Low: $${d.low.toFixed(2)}<br/>Close: $${d.close.toFixed(2)}`)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 10) + "px");
                })
                .on("mouseout", function() {
                    d3.select(this).attr("stroke-width", 0.5);
                    tooltip.style("opacity", 0);
                });
        });
    """
        else:  # area chart
            chart_script = """
    // Area chart
    const area = d3.area()
        .x(d => x(d.date))
        .y0(y(0))
        .y1(d => y(d.close))
        .curve(d3.curveMonotoneX);

    // Gradient definition
    const gradient = svg.append("defs")
        .append("linearGradient")
        .attr("id", "area-gradient")
        .attr("gradientUnits", "userSpaceOnUse")
        .attr("x1", 0).attr("y1", y(0))
        .attr("x2", 0).attr("y2", y(d3.max(data, d => d.close)));

    gradient.append("stop")
        .attr("offset", "0%")
        .attr("stop-color", "#ff8c00")
        .attr("stop-opacity", 0.6);

    gradient.append("stop")
        .attr("offset", "100%")
        .attr("stop-color", "#ff8c00")
        .attr("stop-opacity", 0.1);

    svg.append("path")
        .datum(data)
        .attr("fill", "url(#area-gradient)")
        .attr("d", area);

    // Add line on top
    const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.close))
        .curve(d3.curveMonotoneX);

    svg.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "#ff8c00")
        .attr("stroke-width", 2)
        .attr("d", line);
    """
        
        # Generate complete HTML with D3.js
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{symbol.upper()} Chart</title>
    <style>
        html, body {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            margin: 0;
            padding: 0;
            background-color: #000000;
            color: #ff8c00;
            height: 100%;
            overflow: hidden;
        }}
        .container {{
            width: 100%;
            padding: 20px 0;
            min-height: 100vh;
        }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 30px;
            font-size: 14px;
            color: #cccccc;
        }}
        .stat {{
            text-align: center;
            background: #000000;
            padding: 12px 16px;
            border-radius: 4px;
            border: 1px solid #ff8c00;
        }}
        .stat-value {{
            font-weight: bold;
            font-size: 16px;
            color: #ffffff;
            margin-top: 4px;
        }}
        .positive {{ color: #00ff00; }}
        .negative {{ color: #ff4444; }}
        .tooltip {{
            position: absolute;
            padding: 10px;
            background: #1a1a1a;
            color: #ff8c00;
            border: 1px solid #ff8c00;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }}
        #chart {{ text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="stats">
            <div class="stat">
                <div>Period</div>
                <div class="stat-value">{actual_period}</div>
            </div>
            <div class="stat">
                <div>Current Price</div>
                <div class="stat-value">${latest_price:.2f}</div>
            </div>
            <div class="stat">
                <div>Change</div>
                <div class="stat-value {'positive' if price_change >= 0 else 'negative'}">${price_change:+.2f} ({price_change_pct:+.1f}%)</div>
            </div>
            <div class="stat">
                <div>Data Points</div>
                <div class="stat-value">{len(chart_data)}</div>
            </div>
        </div>
        <div id="chart"></div>
    </div>
    
    <div class="tooltip"></div>

    <script type="module">
        import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

        // Data
        const rawData = {chart_data};
        const data = rawData.map(d => ({{
            ...d,
            date: new Date(d.date)
        }}));

        // Chart dimensions
        const width = window.innerWidth;
        const height = Math.max(400, window.innerHeight * 0.6);
        const marginTop = 20;
        const marginRight = 20;
        const marginBottom = 40;
        const marginLeft = 60;

        // Scales
        const x = d3.scaleTime()
            .domain(d3.extent(data, d => d.date))
            .range([marginLeft, width - marginRight]);

        const y = d3.scaleLinear()
            .domain(d3.extent(data, d => d.close))
            .nice()
            .range([height - marginBottom, marginTop]);

        // Create SVG
        const svg = d3.create("svg")
            .attr("width", width)
            .attr("height", height)
            .attr("style", "background: #000000;");

        // Add grid lines
        svg.append("g")
            .attr("class", "grid")
            .attr("transform", `translate(0,${{height - marginBottom}})`)
            .call(d3.axisBottom(x)
                .tickSize(-height + marginTop + marginBottom)
                .tickFormat("")
            )
            .style("stroke", "#333333")
            .style("stroke-dasharray", "2,2")
            .style("opacity", 0.7);

        svg.append("g")
            .attr("class", "grid")
            .attr("transform", `translate(${{marginLeft}},0)`)
            .call(d3.axisLeft(y)
                .tickSize(-width + marginLeft + marginRight)
                .tickFormat("")
            )
            .style("stroke", "#333333")
            .style("stroke-dasharray", "2,2")
            .style("opacity", 0.7);

        // Add axes
        svg.append("g")
            .attr("transform", `translate(0,${{height - marginBottom}})`)
            .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%m/%d")))
            .style("font-size", "11px")
            .style("font-family", "Monaco, Menlo, Ubuntu Mono, monospace")
            .selectAll("text")
            .style("fill", "#ff8c00");

        svg.selectAll(".domain")
            .style("stroke", "#ff8c00")
            .style("stroke-width", "1px");

        svg.append("g")
            .attr("transform", `translate(${{marginLeft}},0)`)
            .call(d3.axisLeft(y).tickFormat(d => `$$${{d}}`))
            .style("font-size", "11px")
            .style("font-family", "Monaco, Menlo, Ubuntu Mono, monospace")
            .selectAll("text")
            .style("fill", "#ff8c00");

        // Style all axis lines
        svg.selectAll(".domain")
            .style("stroke", "#ff8c00")
            .style("stroke-width", "1px");

        svg.selectAll(".tick line")
            .style("stroke", "#ff8c00")
            .style("stroke-width", "1px");

        // Tooltip
        const tooltip = d3.select(".tooltip");

        {chart_script}

        // Append to DOM
        document.getElementById("chart").appendChild(svg.node());
    </script>
</body>
</html>"""
        
        # Base64 encode the HTML content
        html_bytes = html.encode('utf-8')
        html_base64 = base64.b64encode(html_bytes).decode('ascii')
        
        return EmbeddedResource(
            type="resource",
            resource=BlobResourceContents(
                uri=f"ui://data/chart/{symbol}",
                mimeType="text/html",
                blob=html_base64,
                _meta={
                    "mcpui.dev/ui-preferred-frame-size": ['800px', '1000px']
                }
            )
        )

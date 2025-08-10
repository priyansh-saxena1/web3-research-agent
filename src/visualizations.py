import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, Any

def create_price_chart(data: Dict[str, Any], symbol: str) -> go.Figure:
    try:
        if not data or "prices" not in data:
            return _empty_chart(f"No price data for {symbol}")
        
        prices = data["prices"]
        timestamps = [datetime.fromtimestamp(p[0]/1000) for p in prices]
        values = [p[1] for p in prices]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps, y=values, mode='lines',
            name=f'{symbol.upper()} Price',
            line=dict(color='#00D4AA', width=2)
        ))
        
        fig.update_layout(
            title=f'{symbol.upper()} Price History',
            xaxis_title='Date', yaxis_title='Price (USD)',
            template='plotly_dark', height=400
        )
        
        return fig
    except Exception:
        return _empty_chart(f"Chart error for {symbol}")

def create_market_overview(data: Dict[str, Any]) -> go.Figure:
    try:
        if not data:
            return _empty_chart("No market data available")
        
        fig = go.Figure()
        fig.add_annotation(
            text="Market Overview\n" + str(data)[:200] + "...",
            x=0.5, y=0.5, font=dict(size=12, color="white"),
            showarrow=False, align="left"
        )
        
        fig.update_layout(
            title="Market Overview", template='plotly_dark', height=400,
            xaxis=dict(visible=False), yaxis=dict(visible=False)
        )
        
        return fig
    except Exception:
        return _empty_chart("Market overview error")

def _empty_chart(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message, x=0.5, y=0.5,
        font=dict(size=16, color="white"), showarrow=False
    )
    fig.update_layout(
        template='plotly_dark', height=400,
        xaxis=dict(visible=False), yaxis=dict(visible=False)
    )
    return fig

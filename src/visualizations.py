import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime

def create_price_chart(data: Dict[str, Any], symbol: str) -> str:
    try:
        if not data or "prices" not in data:
            return f"<div style='padding: 20px; text-align: center;'>No price data available for {symbol.upper()}</div>"
        
        prices = data["prices"]
        volumes = data.get("total_volumes", [])
        
        if not prices:
            return f"<div style='padding: 20px; text-align: center;'>No price history found for {symbol.upper()}</div>"
        
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
        
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=[f"{symbol.upper()} Price Chart", "Volume"],
            row_width=[0.7, 0.3]
        )
        
        fig.add_trace(
            go.Scatter(
                x=df["datetime"],
                y=df["price"],
                mode="lines",
                name="Price",
                line=dict(color="#00D4AA", width=2),
                hovertemplate="<b>%{y:$,.2f}</b><br>%{x}<extra></extra>"
            ),
            row=1, col=1
        )
        
        if volumes:
            vol_df = pd.DataFrame(volumes, columns=["timestamp", "volume"])
            vol_df["datetime"] = pd.to_datetime(vol_df["timestamp"], unit="ms")
            
            fig.add_trace(
                go.Bar(
                    x=vol_df["datetime"],
                    y=vol_df["volume"],
                    name="Volume",
                    marker_color="#FF6B6B",
                    opacity=0.7,
                    hovertemplate="<b>$%{y:,.0f}</b><br>%{x}<extra></extra>"
                ),
                row=2, col=1
            )
        
        current_price = df["price"].iloc[-1]
        price_change = ((df["price"].iloc[-1] - df["price"].iloc[0]) / df["price"].iloc[0]) * 100
        
        fig.update_layout(
            title=dict(
                text=f"{symbol.upper()} - ${current_price:,.4f} ({price_change:+.2f}%)",
                x=0.5,
                font=dict(size=20, color="#FFFFFF")
            ),
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            template="plotly_dark",
            showlegend=False,
            height=600,
            margin=dict(l=60, r=60, t=80, b=60),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(255,255,255,0.1)")
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(255,255,255,0.1)")
        
        return fig.to_html(include_plotlyjs="cdn", div_id=f"chart_{symbol}")
        
    except Exception as e:
        return f"<div style='padding: 20px; text-align: center; color: #FF6B6B;'>Chart generation failed: {str(e)}</div>"

def create_market_overview(data: Dict[str, Any]) -> str:
    try:
        if not data or "market_data" not in data:
            return "<div style='padding: 20px; text-align: center;'>Market data unavailable</div>"
        
        market_data = data["market_data"]
        if not market_data:
            return "<div style='padding: 20px; text-align: center;'>No market data found</div>"
        
        df = pd.DataFrame(market_data)
        df = df.head(20)
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                "Market Cap Distribution",
                "24h Price Changes",
                "Trading Volume",
                "Price vs Volume"
            ],
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )
        
        fig.add_trace(
            go.Pie(
                labels=df["symbol"].str.upper(),
                values=df["market_cap"],
                textinfo="label+percent",
                textposition="inside",
                marker=dict(colors=px.colors.qualitative.Set3),
                hovertemplate="<b>%{label}</b><br>Market Cap: $%{value:,.0f}<extra></extra>"
            ),
            row=1, col=1
        )
        
        colors = ["#00D4AA" if x >= 0 else "#FF6B6B" for x in df["price_change_percentage_24h"]]
        fig.add_trace(
            go.Bar(
                x=df["symbol"].str.upper(),
                y=df["price_change_percentage_24h"],
                marker_color=colors,
                hovertemplate="<b>%{x}</b><br>24h Change: %{y:+.2f}%<extra></extra>"
            ),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Bar(
                x=df["symbol"].str.upper(),
                y=df["total_volume"],
                marker_color="#4ECDC4",
                hovertemplate="<b>%{x}</b><br>Volume: $%{y:,.0f}<extra></extra>"
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df["current_price"],
                y=df["total_volume"],
                mode="markers+text",
                text=df["symbol"].str.upper(),
                textposition="top center",
                marker=dict(
                    size=df["market_cap"] / df["market_cap"].max() * 50 + 10,
                    color=df["price_change_percentage_24h"],
                    colorscale="RdYlGn",
                    colorbar=dict(title="24h Change %"),
                    line=dict(width=1, color="white")
                ),
                hovertemplate="<b>%{text}</b><br>Price: $%{x:,.4f}<br>Volume: $%{y:,.0f}<extra></extra>"
            ),
            row=2, col=2
        )
        
        global_info = data.get("global_data", {}).get("data", {})
        total_mcap = global_info.get("total_market_cap", {}).get("usd", 0)
        total_volume = global_info.get("total_volume", {}).get("usd", 0)
        btc_dominance = global_info.get("market_cap_percentage", {}).get("btc", 0)
        
        title_text = f"Crypto Market Overview - Total MCap: ${total_mcap/1e12:.2f}T | 24h Vol: ${total_volume/1e9:.0f}B | BTC Dom: {btc_dominance:.1f}%"
        
        fig.update_layout(
            title=dict(
                text=title_text,
                x=0.5,
                font=dict(size=16, color="#FFFFFF")
            ),
            template="plotly_dark",
            showlegend=False,
            height=800,
            margin=dict(l=60, r=60, t=100, b=60),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(255,255,255,0.1)")
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(255,255,255,0.1)")
        
        return fig.to_html(include_plotlyjs="cdn", div_id="market_overview")
        
    except Exception as e:
        return f"<div style='padding: 20px; text-align: center; color: #FF6B6B;'>Market overview failed: {str(e)}</div>"

def create_comparison_chart(coins_data: List[Dict[str, Any]]) -> str:
    try:
        if not coins_data:
            return "<div style='padding: 20px; text-align: center;'>No comparison data available</div>"
        
        df = pd.DataFrame(coins_data)
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=["Price Comparison", "Market Cap Comparison"]
        )
        
        colors = px.colors.qualitative.Set1[:len(df)]
        
        for i, (_, coin) in enumerate(df.iterrows()):
            fig.add_trace(
                go.Bar(
                    name=coin["symbol"].upper(),
                    x=[coin["symbol"].upper()],
                    y=[coin["current_price"]],
                    marker_color=colors[i],
                    hovertemplate=f"<b>{coin['name']}</b><br>Price: $%{{y:,.4f}}<extra></extra>"
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Bar(
                    name=coin["symbol"].upper(),
                    x=[coin["symbol"].upper()],
                    y=[coin["market_cap"]],
                    marker_color=colors[i],
                    showlegend=False,
                    hovertemplate=f"<b>{coin['name']}</b><br>Market Cap: $%{{y:,.0f}}<extra></extra>"
                ),
                row=1, col=2
            )
        
        fig.update_layout(
            title="Cryptocurrency Comparison",
            template="plotly_dark",
            height=500,
            showlegend=True
        )
        
        return fig.to_html(include_plotlyjs="cdn", div_id="comparison_chart")
        
    except Exception as e:
        return f"<div style='padding: 20px; text-align: center; color: #FF6B6B;'>Comparison chart failed: {str(e)}</div>"

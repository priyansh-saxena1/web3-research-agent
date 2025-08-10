import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CryptoVisualizations:
    """Professional cryptocurrency data visualizations"""
    
    @staticmethod
    def create_price_chart(data: Dict[str, Any], symbol: str = "BTC") -> go.Figure:
        """Create a professional price chart with volume"""
        try:
            if not data or 'prices' not in data:
                return CryptoVisualizations._create_empty_chart("No price data available")
            
            prices = data['prices']
            volumes = data.get('total_volumes', [])
            
            # Convert to DataFrame
            df = pd.DataFrame({
                'timestamp': [pd.to_datetime(p[0], unit='ms') for p in prices],
                'price': [p[1] for p in prices],
                'volume': [v[1] if v else 0 for v in (volumes[:len(prices)] if volumes else [])]
            })
            
            # Create subplot with secondary y-axis
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.1,
                subplot_titles=(f'{symbol.upper()} Price', 'Volume'),
                row_heights=[0.7, 0.3]
            )
            
            # Price line
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['price'],
                    mode='lines',
                    name='Price',
                    line=dict(color='#00d4aa', width=2),
                    hovertemplate='<b>%{y:,.2f} USD</b><br>%{x}<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Volume bars
            if not df['volume'].empty and df['volume'].sum() > 0:
                fig.add_trace(
                    go.Bar(
                        x=df['timestamp'],
                        y=df['volume'],
                        name='Volume',
                        marker_color='rgba(0, 212, 170, 0.3)',
                        hovertemplate='<b>%{y:,.0f}</b><br>%{x}<extra></extra>'
                    ),
                    row=2, col=1
                )
            
            # Update layout
            fig.update_layout(
                title=dict(
                    text=f'{symbol.upper()} Price Analysis',
                    font=dict(size=24, color='#2c3e50'),
                    x=0.5
                ),
                showlegend=False,
                height=600,
                margin=dict(l=60, r=30, t=80, b=60),
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family="SF Pro Display, -apple-system, system-ui, sans-serif", size=12)
            )
            
            # Update axes
            fig.update_xaxes(
                gridcolor='#ecf0f1',
                gridwidth=1,
                showgrid=True,
                tickfont=dict(color='#7f8c8d')
            )
            fig.update_yaxes(
                gridcolor='#ecf0f1',
                gridwidth=1,
                showgrid=True,
                tickfont=dict(color='#7f8c8d')
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating price chart: {e}")
            return CryptoVisualizations._create_empty_chart(f"Error: {str(e)}")
    
    @staticmethod
    def create_market_overview(data: List[Dict[str, Any]]) -> go.Figure:
        """Create market overview with top cryptocurrencies"""
        try:
            if not data:
                return CryptoVisualizations._create_empty_chart("No market data available")
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Take top 10 by market cap
            df = df.head(10).sort_values('market_cap', ascending=True)
            
            # Create horizontal bar chart
            fig = go.Figure()
            
            # Market cap bars
            fig.add_trace(
                go.Bar(
                    y=df['name'],
                    x=df['market_cap'],
                    orientation='h',
                    marker=dict(
                        color=df['price_change_percentage_24h'],
                        colorscale='RdYlGn',
                        colorbar=dict(title="24h Change %"),
                        line=dict(color='white', width=1)
                    ),
                    hovertemplate='<b>%{y}</b><br>Market Cap: $%{x:,.0f}<br>24h: %{marker.color:.2f}%<extra></extra>'
                )
            )
            
            fig.update_layout(
                title=dict(
                    text='Top 10 Cryptocurrencies by Market Cap',
                    font=dict(size=24, color='#2c3e50'),
                    x=0.5
                ),
                xaxis_title='Market Cap (USD)',
                height=500,
                margin=dict(l=120, r=30, t=80, b=60),
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family="SF Pro Display, -apple-system, system-ui, sans-serif", size=12)
            )
            
            fig.update_xaxes(
                gridcolor='#ecf0f1',
                gridwidth=1,
                showgrid=True,
                tickfont=dict(color='#7f8c8d')
            )
            fig.update_yaxes(
                tickfont=dict(color='#2c3e50', size=11)
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating market overview: {e}")
            return CryptoVisualizations._create_empty_chart(f"Error: {str(e)}")
    
    @staticmethod
    def _create_empty_chart(message: str) -> go.Figure:
        """Create an empty chart with error message"""
        fig = go.Figure()
        
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="#7f8c8d")
        )
        
        fig.update_layout(
            height=400,
            margin=dict(l=60, r=60, t=60, b=60),
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False)
        )
        
        return fig

# Convenience functions for backward compatibility
def create_price_chart(data: Dict[str, Any], symbol: str = "BTC") -> go.Figure:
    """Create price chart - backward compatibility function"""
    return CryptoVisualizations.create_price_chart(data, symbol)

def create_market_overview(data: List[Dict[str, Any]]) -> go.Figure:
    """Create market overview - backward compatibility function"""
    return CryptoVisualizations.create_market_overview(data)

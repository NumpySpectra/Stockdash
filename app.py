import os
import requests
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, render_template, request
from plotly.offline import plot
import plotly.graph_objs as go

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

app = Flask(__name__)

# Function to fetch stock data based on timeframe
def fetch_data(symbol: str, timeframe: str) -> pd.DataFrame:
    function_map = {
        "DAILY": "TIME_SERIES_DAILY",
        "WEEKLY": "TIME_SERIES_WEEKLY",
        "MONTHLY": "TIME_SERIES_MONTHLY"
    }

    url = (
        "https://www.alphavantage.co/query"
        f"?function={function_map[timeframe]}&symbol={symbol}&apikey={API_KEY}&outputsize=compact"
    )

    r = requests.get(url, timeout=30).json()

    # Map JSON keys according to timeframe
    key_map = {
        "DAILY": "Time Series (Daily)",
        "WEEKLY": "Weekly Time Series",
        "MONTHLY": "Monthly Time Series"
    }

    if key_map[timeframe] not in r:
        note = r.get("Note") or r.get("Error Message") or "API limit reached or invalid symbol."
        raise ValueError(note)

    df = pd.DataFrame(r[key_map[timeframe]]).T
    df.columns = ["Open", "High", "Low", "Close", "Volume"]
    df = df.astype(float)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df


@app.route("/", methods=["GET", "POST"])
def home():
    table_html = None
    error = None
    chart_div = None
    symbol = "AAPL"
    timeframe = "DAILY"  # Default

    if request.method == "POST":
        symbol = request.form.get("symbol", "AAPL").strip().upper()
        timeframe = request.form.get("timeframe", "DAILY").strip().upper()

    try:
        df = fetch_data(symbol, timeframe)

        # Table (last 30 entries)
        table_html = df.tail(30).to_html(classes="table table-striped table-sm", border=0)

        # Plotly chart
        trace = go.Scatter(
            x=df.index[-30:], 
            y=df['Close'].tail(30), 
            mode='lines+markers', 
            name=symbol
        )
        layout = go.Layout(
            title=f"{symbol} Last 30 {timeframe.title()} Close Prices",
            xaxis_title="Date",
            yaxis_title="Close Price"
        )
        fig = go.Figure(data=[trace], layout=layout)
        chart_div = plot(fig, output_type='div', include_plotlyjs=False)

    except Exception as e:
        error = str(e)

    return render_template(
        "index.html",
        table_html=table_html,
        chart_div=chart_div,
        symbol=symbol,
        timeframe=timeframe,
        error=error
    )


if __name__ == "__main__":
    app.run(debug=True)

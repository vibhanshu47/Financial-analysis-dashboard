from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)

# We add methods=['GET', 'POST'] so the app can receive data from the user
@app.route('/', methods=['GET', 'POST'])
def dashboard():
    # 1. Get the ticker from the user, default to SUZLON.NS if they just opened the page
    ticker = request.form.get('ticker', 'SUZLON.NS')
    
    # Capitalize it just in case they type in lowercase
    ticker = ticker.upper()

    try:
        # 2. Download Data
        stock_data = yf.download(ticker, start="2024-01-01", end="2026-05-30")
        
        # If the user types a fake stock, yfinance returns empty data. We catch that here.
        if stock_data.empty:
            return render_template('index.html', error=f"Could not find data for {ticker}. Check the symbol.", plot_url=None)

        # 3. Apply Logic
        stock_data['20_MA'] = stock_data['Close'].rolling(window=20).mean()
        stock_data['50_MA'] = stock_data['Close'].rolling(window=50).mean()
        stock_data = stock_data.dropna()

        stock_data['Signal'] = 0.0
        stock_data.loc[stock_data['20_MA'] > stock_data['50_MA'], 'Signal'] = 1.0
        stock_data['Position'] = stock_data['Signal'].diff()

        # 4. Draw Graph
        plt.figure(figsize=(12, 6))
        plt.plot(stock_data.index, stock_data['Close'], label=f'{ticker} Close', color='grey', alpha=0.5)
        plt.plot(stock_data.index, stock_data['20_MA'], label='20-Day MA', color='blue', alpha=0.8)
        plt.plot(stock_data.index, stock_data['50_MA'], label='50-Day MA', color='orange', alpha=0.8)
        
        buy_signals = stock_data[stock_data['Position'] == 1.0]
        plt.plot(buy_signals.index, buy_signals['20_MA'], '^', markersize=12, color='green', lw=0, label='BUY')
        
        sell_signals = stock_data[stock_data['Position'] == -1.0]
        plt.plot(sell_signals.index, sell_signals['20_MA'], 'v', markersize=12, color='red', lw=0, label='SELL')
        
        plt.title(f'Algorithmic Pattern Recognition: {ticker}')
        plt.legend(loc='best')
        plt.grid(True, alpha=0.3)

        # 5. Convert for Web
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()

        # 6. Send everything to the HTML page
        return render_template('index.html', plot_url=plot_url, current_ticker=ticker)

    except Exception as e:
        return render_template('index.html', error="An error occurred while processing the data.", plot_url=None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
import os
import sys
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from binance.exceptions import BinanceAPIException

# Ensure proper package resolution when run directly
sys.path.append(str(Path(__file__).resolve().parent.parent))

from Bot.logging_config import logger
from Bot.validators import validate_inputs, ValidationError
from Bot.client import init_binance_client, check_connection
from Bot.orders import place_futures_order

app = Flask(__name__)

# Determine if we should force dry-run on start
def check_keys_missing() -> bool:
    """Uses python-dotenv to check if either standard or custom keys are set in api.env."""
    base_dir = Path(__file__).resolve().parent.parent
    env_path = base_dir / 'api.env'
    if not env_path.exists():
        return True
    
    try:
        import dotenv
        vals = dotenv.dotenv_values(env_path)
        key = vals.get("BINANCE_API_KEY") or vals.get("API_KEY")
        secret = vals.get("BINANCE_API_SECRET") or vals.get("API_SECRET")
        if key and secret and "your_" not in key:
            return False
    except Exception:
        pass
    return True

# Initialize global state client
DRY_RUN_MODE = check_keys_missing()
try:
    binance_client = init_binance_client(dry_run=DRY_RUN_MODE)
except Exception as e:
    logger.warning(f"Error loading live client: {str(e)}. Defaulting server to DRY-RUN mode.")
    DRY_RUN_MODE = True
    binance_client = None

@app.route('/')
def home():
    """Renders the dashboard single page application."""
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    """Returns the current connection status and operation mode."""
    connected = check_connection(binance_client)
    mode = "DRY-RUN (Simulated)" if DRY_RUN_MODE else "LIVE TESTNET (Active)"
    
    return jsonify({
        'connected': connected,
        'mode': mode,
        'api_configured': not DRY_RUN_MODE
    })

@app.route('/api/order', methods=['POST'])
def place_order():
    """Validates inputs and places a Futures order."""
    data = request.json or {}
    
    symbol = data.get('symbol')
    side = data.get('side')
    order_type = data.get('type')
    quantity = data.get('quantity')
    price = data.get('price')
    stop_price = data.get('stop_price')
    
    # 1. Local Validation
    try:
        validated = validate_inputs(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price
        )
    except ValidationError as ve:
        logger.error(f"Web validation error: {str(ve)}")
        return jsonify({
            'success': False,
            'error': f"Input Validation Error: {str(ve)}"
        }), 400
        
    # 2. Execution
    try:
        response = place_futures_order(
            client=binance_client,
            symbol=validated['symbol'],
            side=validated['side'],
            order_type=validated['order_type'],
            quantity=validated['quantity'],
            price=validated['price'],
            stop_price=validated['stop_price']
        )
        return jsonify({
            'success': True,
            'summary': validated,
            'response': response
        })
    except BinanceAPIException as bae:
        return jsonify({
            'success': False,
            'error': f"Binance API Error (Code {bae.code}): {bae.message}"
        }), 502
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Execution Error: {str(e)}"
        }), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Streams the last 50 lines from the central log file."""
    base_dir = Path(__file__).resolve().parent.parent
    log_file = base_dir / 'Logs' / 'trading_bot.log'
    
    if not log_file.exists():
        return jsonify({'logs': "No log file initialized yet. Place an order to generate logs."})
        
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            last_lines = lines[-50:]  # get last 50 lines
            return jsonify({'logs': "".join(last_lines)})
    except Exception as e:
        return jsonify({'logs': f"Error reading log file: {str(e)}"}), 500

def start_web_server(port=5000):
    logger.info(f"Starting lightweight web server on http://127.0.0.1:{port} (DRY_RUN: {DRY_RUN_MODE})")
    app.run(host='127.0.0.1', port=port, debug=False)

if __name__ == "__main__":
    start_web_server()

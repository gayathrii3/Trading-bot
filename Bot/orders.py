import time
import random
from binance.client import Client
from binance.exceptions import BinanceAPIException
from Bot.logging_config import logger

def place_futures_order(
    client: Client,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float = None,
    stop_price: float = None
) -> dict:
    """
    Places an order on Binance USD(S)-M Futures Testnet.
    Supports MARKET, LIMIT, and STOP_LIMIT (underlying type 'STOP') orders.
    If client is None, simulates placing the order in a mock environment (dry-run).
    
    Args:
        client: Initialized python-binance Client or None (for dry-run mode).
        symbol: Alphanumeric trading pair, e.g., 'BTCUSDT'.
        side: 'BUY' or 'SELL'.
        order_type: 'MARKET', 'LIMIT', or 'STOP_LIMIT'.
        quantity: Order quantity in units of base asset.
        price: Limit price (required for LIMIT and STOP_LIMIT).
        stop_price: Stop/trigger price (required for STOP_LIMIT).
        
    Returns:
        dict: The response payload from Binance Futures API.
    """
    logger.info(
        f"Initiating order request -> Symbol: {symbol} | Side: {side} | "
        f"Type: {order_type} | Qty: {quantity} | Price: {price} | StopPrice: {stop_price}"
    )
    
    # 1. Handle Dry-Run Simulation Mode
    if client is None:
        logger.info(f"[DRY-RUN] Simulating order placement: symbol={symbol}, side={side}, type={order_type}")
        simulated_order_id = random.randint(100000000, 999999999)
        simulated_client_id = f"sim_ot_{random.randint(100000, 999999)}"
        
        # Calculate simulated fill price
        sim_price = price if price is not None else 65120.40
        sim_avg_price = str(sim_price)
        
        simulated_response = {
            'orderId': simulated_order_id,
            'clientOrderId': simulated_client_id,
            'symbol': symbol,
            'status': 'FILLED' if order_type == 'MARKET' else 'NEW',
            'executedQty': str(quantity),
            'avgPrice': sim_avg_price,
            'origQty': str(quantity),
            'price': str(price) if price is not None else '0.00',
            'side': side,
            'timeInForce': 'GTC',
            'type': 'STOP' if order_type == 'STOP_LIMIT' else order_type,
            'workingType': 'CONTRACT_PRICE',
            'positionSide': 'BOTH',
            'updateTime': int(time.time() * 1000)
        }
        
        logger.info(f"[DRY-RUN] Order placed successfully! Order ID: {simulated_order_id}")
        logger.debug(f"[DRY-RUN] Simulated Raw API Response: {simulated_response}")
        return simulated_response

    # 2. Live Testnet Mode
    params = {
        'symbol': symbol,
        'side': side,
        'quantity': quantity
    }
    
    if order_type == 'MARKET':
        params['type'] = 'MARKET'
        
    elif order_type == 'LIMIT':
        params['type'] = 'LIMIT'
        params['price'] = price
        params['timeInForce'] = 'GTC'  # Good Till Cancelled
        
    elif order_type == 'STOP_LIMIT':
        # In Binance Futures API, STOP type is a Stop-Limit order
        # which triggers a LIMIT order at 'price' when 'stopPrice' is hit.
        params['type'] = 'STOP'
        params['price'] = price
        params['stopPrice'] = stop_price
        params['timeInForce'] = 'GTC'
        
    logger.debug(f"API Request Parameters: {params}")
    
    try:
        response = client.futures_create_order(**params)
        logger.info(f"Order placed successfully! Order ID: {response.get('orderId')}")
        logger.debug(f"Raw API Response: {response}")
        return response
    except BinanceAPIException as e:
        logger.error(f"Binance API Error placing order: Status Code {e.status_code} | Error Code {e.code} | Message: {e.message}")
        logger.debug(f"Full Binance Exception details: {e}")
        raise e
    except Exception as e:
        logger.error(f"Network or execution error placing order: {str(e)}")
        raise RuntimeError(f"Connection or execution failure: {str(e)}")

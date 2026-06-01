import os
import sys
import argparse
from binance.exceptions import BinanceAPIException

# Ensure proper package resolution when run directly
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from Bot.logging_config import logger
from Bot.validators import (
    validate_inputs,
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    ValidationError
)
from Bot.client import init_binance_client, check_connection
from Bot.orders import place_futures_order

def run_interactive_wizard() -> dict:
    """
    Guides the user interactively through inputting and validating order details.
    Uses only safe ASCII characters to prevent Windows console encoding crashes.
    """
    print("\n" + "=" * 60)
    print("          === BINANCE FUTURES TRADING BOT WIZARD ===")
    print("=" * 60 + "\n")
    print("Provide details for your trade. Inputs will be verified live.\n")
    
    # 1. Symbol
    while True:
        symbol_input = input("> Enter Symbol (e.g., BTCUSDT, ETHUSDT): ").strip()
        try:
            symbol = validate_symbol(symbol_input)
            print(f"   [OK] Valid symbol: {symbol}")
            break
        except ValidationError as e:
            print(f"   [FAIL] Invalid: {str(e)}")
            
    # 2. Side
    while True:
        side_input = input("> Enter Trade Side (BUY/SELL): ").strip()
        try:
            side = validate_side(side_input)
            print(f"   [OK] Valid side: {side}")
            break
        except ValidationError as e:
            print(f"   [FAIL] Invalid: {str(e)}")
            
    # 3. Order Type
    while True:
        type_input = input("> Enter Order Type (MARKET/LIMIT/STOP_LIMIT): ").strip()
        try:
            order_type = validate_order_type(type_input)
            print(f"   [OK] Valid type: {order_type}")
            break
        except ValidationError as e:
            print(f"   [FAIL] Invalid: {str(e)}")
            
    # 4. Quantity
    while True:
        qty_input = input("> Enter Quantity (base unit, e.g. 0.001): ").strip()
        try:
            quantity = validate_quantity(qty_input)
            print(f"   [OK] Valid quantity: {quantity}")
            break
        except ValidationError as e:
            print(f"   [FAIL] Invalid: {str(e)}")
            
    # 5. Price (required for LIMIT / STOP_LIMIT)
    price = None
    if order_type in ('LIMIT', 'STOP_LIMIT'):
        while True:
            price_input = input(f"> Enter Limit Price (e.g. 64000.5): ").strip()
            try:
                price = validate_price(price_input, label="Limit Price")
                print(f"   [OK] Valid price: {price}")
                break
            except ValidationError as e:
                print(f"   [FAIL] Invalid: {str(e)}")
                
    # 6. Stop Price (required for STOP_LIMIT)
    stop_price = None
    if order_type == 'STOP_LIMIT':
        while True:
            stop_input = input("> Enter Trigger Stop Price (e.g. 63900): ").strip()
            try:
                stop_price = validate_price(stop_input, label="Stop Price")
                print(f"   [OK] Valid trigger price: {stop_price}")
                break
            except ValidationError as e:
                print(f"   [FAIL] Invalid: {str(e)}")
                
    return {
        'symbol': symbol,
        'side': side,
        'order_type': order_type,
        'quantity': quantity,
        'price': price,
        'stop_price': stop_price
    }

def print_order_result(success: bool, inputs: dict, response: dict = None, error_msg: str = None, dry_run: bool = False):
    """
    Renders a clear, formatted summary of request parameters and response outcomes.
    Uses only safe ASCII characters to support older/non-UTF-8 terminals.
    """
    print("\n" + "=" * 60)
    mode_str = " [SIMULATED]" if dry_run else ""
    if success:
        print(f"          *** ORDER PLACED SUCCESSFULLY{mode_str} ***          ")
    else:
        print(f"          !!! ORDER PLACEMENT FAILED{mode_str} !!!          ")
    print("=" * 60)
    
    print("\n[Order Request Summary]")
    print(f"  Symbol:     {inputs['symbol']}")
    print(f"  Side:       {inputs['side']}")
    print(f"  Type:       {inputs['order_type']}")
    print(f"  Quantity:   {inputs['quantity']}")
    if inputs['price'] is not None:
        print(f"  Price:      {inputs['price']}")
    if inputs['stop_price'] is not None:
        print(f"  Stop Price: {inputs['stop_price']}")
        
    if success and response:
        print("\n[Order Response Details]")
        print(f"  Order ID:       {response.get('orderId', 'N/A')}")
        print(f"  Client Ord ID:  {response.get('clientOrderId', 'N/A')}")
        print(f"  Status:         {response.get('status', 'N/A')}")
        print(f"  Executed Qty:   {response.get('executedQty', 'N/A')}")
        
        # Safely parse and format average fill price
        avg_price = response.get('avgPrice')
        if avg_price and float(avg_price) > 0:
            print(f"  Avg Fill Price: {avg_price}")
        else:
            print(f"  Avg Fill Price: Market/Unfilled (Limit: {response.get('price', 'N/A')})")
            
        print(f"  Time in Force:  {response.get('timeInForce', 'N/A')}")
        print(f"  Working Type:   {response.get('workingType', 'N/A')}")
    else:
        print("\n[Failure Details]")
        print(f"  Reason: {error_msg}")
        
    print("\n" + "=" * 60 + "\n")

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

def main():
    parser = argparse.ArgumentParser(
        description="Place orders on Binance Futures Testnet (USDT-M) with strict validation & structured logs."
    )
    parser.add_argument("-s", "--symbol", type=str, help="Trading Pair (e.g. BTCUSDT)")
    parser.add_argument("-d", "--side", type=str, choices=["BUY", "SELL", "buy", "sell"], help="Trade Side (BUY/SELL)")
    parser.add_argument("-t", "--type", type=str, help="Order Type (MARKET/LIMIT/STOP_LIMIT)")
    parser.add_argument("-q", "--quantity", type=float, help="Order quantity in base currency unit")
    parser.add_argument("-p", "--price", type=float, help="Limit Price (required for LIMIT and STOP_LIMIT)")
    parser.add_argument("-sp", "--stop-price", type=float, help="Trigger Stop Price (required for STOP_LIMIT)")
    parser.add_argument("-i", "--interactive", action="store_true", help="Launch interactive step-by-step wizard")
    parser.add_argument("-dr", "--dry-run", action="store_true", help="Operate in mock simulation mode")
    
    args = parser.parse_args()
    
    # Check if credentials exist at project root
    keys_missing = check_keys_missing()
                    
    dry_run = args.dry_run
    if keys_missing and not dry_run:
        print("\n[NOTICE] Binance API keys are not configured in api.env.")
        print("[NOTICE] Operating in simulated DRY-RUN mode for testing.")
        print("[NOTICE] (To place actual orders on the Testnet, please set keys in api.env)\n")
        dry_run = True
        
    # If no parameters are passed OR interactive flag is set, run wizard
    if args.interactive or len(sys.argv) == 1:
        trade_details = run_interactive_wizard()
    else:
        # Standard command line execution
        try:
            trade_details = validate_inputs(
                symbol=args.symbol,
                side=args.side,
                order_type=args.type,
                quantity=args.quantity,
                price=args.price,
                stop_price=args.stop_price
            )
        except ValidationError as ve:
            logger.error(f"Command CLI validation failed: {str(ve)}")
            print(f"\n[CLI INPUT ERROR] {str(ve)}")
            parser.print_help()
            sys.exit(1)
            
    # Connect and place order
    try:
        # Initialize client
        client = init_binance_client(dry_run=dry_run)
        
        # Perform check
        if not check_connection(client):
            logger.error("API Connectivity test failed. Exiting.")
            print_order_result(
                success=False,
                inputs=trade_details,
                error_msg="Failed to connect to the Binance Futures Testnet API. Please verify network and credentials.",
                dry_run=dry_run
            )
            sys.exit(1)
            
        # Place order
        response = place_futures_order(
            client=client,
            symbol=trade_details['symbol'],
            side=trade_details['side'],
            order_type=trade_details['order_type'],
            quantity=trade_details['quantity'],
            price=trade_details['price'],
            stop_price=trade_details['stop_price']
        )
        
        # Display output
        print_order_result(success=True, inputs=trade_details, response=response, dry_run=dry_run)
        
    except BinanceAPIException as bae:
        print_order_result(
            success=False,
            inputs=trade_details,
            error_msg=f"Binance API Error (Code {bae.code}): {bae.message}",
            dry_run=dry_run
        )
        sys.exit(1)
    except Exception as e:
        print_order_result(
            success=False,
            inputs=trade_details,
            error_msg=str(e),
            dry_run=dry_run
        )
        sys.exit(1)

if __name__ == "__main__":
    main()

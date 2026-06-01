import re

class ValidationError(Exception):
    """Custom exception raised for validation errors in input parameters."""
    pass

def validate_symbol(symbol: str) -> str:
    """Validates that a symbol is non-empty, uppercase, and alphanumeric."""
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("Symbol must be a non-empty string.")
    
    symbol_clean = symbol.strip().upper()
    if not re.match(r'^[A-Z0-9]{3,20}$', symbol_clean):
        raise ValidationError(f"Symbol '{symbol}' is invalid. It must be alphanumeric and 3-20 characters long.")
    
    return symbol_clean

def validate_side(side: str) -> str:
    """Validates that side is either BUY or SELL."""
    if not side or not isinstance(side, str):
        raise ValidationError("Side must be a non-empty string.")
    
    side_clean = side.strip().upper()
    if side_clean not in ('BUY', 'SELL'):
        raise ValidationError(f"Side '{side}' is invalid. Must be 'BUY' or 'SELL'.")
    
    return side_clean

def validate_order_type(order_type: str) -> str:
    """Validates order type is one of MARKET, LIMIT, or STOP_LIMIT."""
    if not order_type or not isinstance(order_type, str):
        raise ValidationError("Order type must be a non-empty string.")
    
    type_clean = order_type.strip().upper().replace('-', '_').replace(' ', '_')
    if type_clean not in ('MARKET', 'LIMIT', 'STOP_LIMIT'):
        raise ValidationError(f"Order type '{order_type}' is invalid. Must be 'MARKET', 'LIMIT', or 'STOP_LIMIT'.")
    
    return type_clean

def validate_quantity(quantity) -> float:
    """Validates that quantity is a positive number."""
    try:
        qty_float = float(quantity)
    except (ValueError, TypeError):
        raise ValidationError(f"Quantity '{quantity}' must be a valid number.")
    
    if qty_float <= 0:
        raise ValidationError(f"Quantity {qty_float} must be greater than zero.")
    
    return qty_float

def validate_price(price, label="Price") -> float:
    """Validates that price is a positive number."""
    try:
        price_float = float(price)
    except (ValueError, TypeError):
        raise ValidationError(f"{label} '{price}' must be a valid number.")
    
    if price_float <= 0:
        raise ValidationError(f"{label} {price_float} must be greater than zero.")
    
    return price_float

def validate_inputs(symbol: str, side: str, order_type: str, quantity, price=None, stop_price=None) -> dict:
    """
    Validates all inputs together and returns a dictionary of validated/sanitized parameters.
    """
    validated = {}
    validated['symbol'] = validate_symbol(symbol)
    validated['side'] = validate_side(side)
    validated['order_type'] = validate_order_type(order_type)
    validated['quantity'] = validate_quantity(quantity)
    
    if validated['order_type'] == 'LIMIT':
        if price is None or str(price).strip() == '':
            raise ValidationError("Price is required for LIMIT orders.")
        validated['price'] = validate_price(price)
        validated['stop_price'] = None
    elif validated['order_type'] == 'STOP_LIMIT':
        if price is None or str(price).strip() == '':
            raise ValidationError("Price is required for STOP_LIMIT orders.")
        if stop_price is None or str(stop_price).strip() == '':
            raise ValidationError("Stop price is required for STOP_LIMIT orders.")
        validated['price'] = validate_price(price, label="Price")
        validated['stop_price'] = validate_price(stop_price, label="Stop Price")
    else:
        # MARKET order
        validated['price'] = None
        validated['stop_price'] = None
        
    return validated

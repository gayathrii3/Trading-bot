import os
from pathlib import Path
from dotenv import load_dotenv
from binance.client import Client
from Bot.logging_config import logger

def init_binance_client(dry_run: bool = False) -> Client:
    """
    Loads API credentials from api.env (if present) or environment variables,
    and initializes a Binance Client configured for the Futures Testnet.
    Supports both BINANCE_API_KEY/SECRET and API_KEY/SECRET variable names.
    If dry_run is True and keys are missing, returns None instead of raising ValueError.
    """
    base_dir = Path(__file__).resolve().parent.parent
    env_path = base_dir / 'api.env'
    
    if env_path.exists():
        logger.debug(f"Loading environment variables from {env_path}")
        load_dotenv(dotenv_path=env_path)
    else:
        logger.debug("api.env file not found at project root. Loading default system environment.")
        load_dotenv()
        
    # Support both custom and standard Binance naming conventions
    api_key = os.getenv("BINANCE_API_KEY") or os.getenv("API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("API_SECRET")
    
    if not api_key or not api_secret:
        if dry_run:
            logger.warning("API credentials missing. Operating in simulated DRY-RUN mode.")
            return None
        logger.error("Missing API_KEY or API_SECRET.")
        raise ValueError(
            "API Credentials missing! Please make sure BINANCE_API_KEY and BINANCE_API_SECRET "
            "(or API_KEY and API_SECRET) are defined in the api.env file in the project root folder."
        )
        
    logger.debug("Initializing python-binance Client (testnet=True)")
    try:
        client = Client(api_key=api_key, api_secret=api_secret, testnet=True)
        return client
    except Exception as e:
        if dry_run:
            logger.warning(f"Failed to initialize Client: {str(e)}. Operating in simulated DRY-RUN mode.")
            return None
        logger.error(f"Failed to initialize Binance Client: {str(e)}")
        raise RuntimeError(f"Could not initialize Binance Client: {str(e)}")

def check_connection(client: Client) -> bool:
    """
    Verifies connection to the Binance Futures Testnet using futures_ping.
    Returns True if connection is successful, False otherwise.
    """
    if client is None:
        # Dry-run client
        logger.info("Dry-run connectivity check: [SUCCESS] (simulated)")
        return True
        
    logger.debug("Pinging Binance Futures Testnet...")
    try:
        client.futures_ping()
        logger.info("Successfully pinged Binance Futures Testnet API.")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to Binance Futures Testnet: {str(e)}")
        return False

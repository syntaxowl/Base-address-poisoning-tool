import os
import time
from web3 import Web3
from dotenv import load_dotenv
from api_keys import INFURA

# Load environment variables
load_dotenv()

# Configuration
INFURA_URL = "https://base-mainnet.infura.io/v3/"+INFURA  # Your Infura project URL
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
USDC_CONTRACT = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"  # USDC contract address (mainnet)
CHECK_INTERVAL = 100000  # Check every 60 seconds
BLOCK_RANGE = 5  # Number of blocks to check per iteration

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

def is_not_contract(address):
    """Check if the address is not a contract."""
    try:
        code = web3.eth.get_code(web3.to_checksum_address(address))
        return len(code) == 0
    except Exception as e:
        print(f"Error checking contract for address {address}: {str(e)}")
        return False

def analyze_transaction(tx_hash):
    """Analyze a transaction to check if it meets the criteria."""
    try:
        # Get transaction details and receipt
        tx = web3.eth.get_transaction(tx_hash)
        tx_receipt = web3.eth.get_transaction_receipt(tx_hash)
        
        # Check if sender is not a contract
        if not is_not_contract(tx["from"]):
            return False, "Sender is a contract"
        
        # Check if transaction has exactly one log
        if len(tx_receipt["logs"]) != 1:
            return False, f"Transaction has {len(tx_receipt['logs'])} logs, expected 1"
        
        # Check if the log is a Transfer event
        log = tx_receipt["logs"][0]
        
        if log["topics"][0].hex() != "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef":
            return False, "Log is not a Transfer event"
        
        if log["address"].lower() != USDC_CONTRACT.lower():
             return False, "Log is not from USDC contract"
        print("znaleziono")
        
        return True, "Valid transaction"
    except Exception as e:
        return False, f"Error analyzing transaction: {str(e)}"

def scan_logs(start_block, end_block):
    """Scan logs for USDC Transfer events and collect unique transaction hashes."""
    try:
        # Filter logs for USDC Transfer events
        logs = web3.eth.get_logs({
            "fromBlock": start_block,
            "toBlock": end_block,
            "address": USDC_CONTRACT,
            "topics": [TRANSFER_TOPIC]
        })
        
        # Collect unique transaction hashes into a set
        tx_hashes = set(log["transactionHash"] for log in logs)
        print(f"Found {len(tx_hashes)} unique transactions in block range {start_block}-{end_block}")
        
        # Analyze each transaction
        valid_transactions = []
        for tx_hash in tx_hashes:
            is_valid, message = analyze_transaction(tx_hash)
            if is_valid:
                valid_transactions.append((tx_hash.hex(), message))
            else:
                print(f"Transaction {tx_hash.hex()}: {message}")
        
        return valid_transactions
    except Exception as e:
        print(f"Error scanning logs from block {start_block} to {end_block}: {str(e)}")
        return []


def main():
    """Main function to periodically check transactions."""
    latest_block = web3.eth.get_block("latest")["number"]
    start_block = max(latest_block - BLOCK_RANGE + 1, 0)
    
    while True:
        try:
            end_block = web3.eth.get_block("latest")["number"]
            print(f"Checking blocks {start_block} to {end_block}...")
            
            # Scan logs in the block range
            valid_txs = scan_logs(start_block, end_block)
            for tx_hash, message in valid_txs:
                print(f"Valid transaction found in block {start_block}-{end_block}: {tx_hash} ({message})")
            
            # Update start block for next iteration
            start_block = end_block + 1
            
            # Wait before next iteration
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"Error in main loop: {str(e)}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    if not web3.is_connected():
        print("Failed to connect to Ethereum node. Check INFURA_URL.")
    else:
        main()
        
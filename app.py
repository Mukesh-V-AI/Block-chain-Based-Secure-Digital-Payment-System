"""
Main Application Entrypoint

This module sets up the FastAPI server, exposes the REST endpoints for wallet 
generation, transaction creation, mining, and tamper testing, and serves the static 
frontend files.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import crypto_utils
from blockchain import Blockchain, Transaction

app = FastAPI(title="Secure Digital Payment System")

# Allow cross-origin requests for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate the global in-memory blockchain
blockchain = Blockchain()

# Ensure static directory exists
os.makedirs("static", exist_ok=True)

class TxRequest(BaseModel):
    """Pydantic model for incoming transaction requests."""
    sender: str
    recipient: str
    amount: float
    timestamp: float
    signature: str
    sender_pub_key: str

class MineRequest(BaseModel):
    """Pydantic model for mining requests."""
    miner_address: str
    
class TamperRequest(BaseModel):
    """Pydantic model for tamper testing endpoints."""
    block_index: int
    new_amount: float = None

@app.get("/api/wallet/create")
def create_wallet():
    """Generates a new secure wallet and returns keys and address."""
    priv, pub = crypto_utils.generate_key_pair()
    address = crypto_utils.generate_wallet_address(pub)
    return {
        "private_key": priv,
        "public_key": pub,
        "address": address
    }

@app.get("/api/wallet/balance/{address}")
def get_balance(address: str):
    """Retrieves the confirmed balance of a given address."""
    balance = blockchain.get_balance(address)
    return {"address": address, "balance": balance}

@app.post("/api/transaction/create")
def create_transaction(tx_req: TxRequest):
    """
    Receives a signed transaction, validates the signature and balance, 
    and adds it to the Mempool if valid.
    """
    try:
        tx = Transaction(
            sender=tx_req.sender,
            recipient=tx_req.recipient,
            amount=tx_req.amount,
            timestamp=tx_req.timestamp,
            signature=tx_req.signature,
            sender_pub_key=tx_req.sender_pub_key
        )
        blockchain.add_transaction(tx)
        return {"message": "Transaction added to mempool successfully", "tx_id": tx.tx_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mine")
def mine_block(req: MineRequest):
    """
    Executes the Proof-of-Work algorithm, pulling pending transactions from 
    the mempool and minting a new block linked to the chain.
    """
    block = blockchain.mine_pending_transactions(req.miner_address)
    if block:
        return {"message": "Block mined successfully", "block": block.to_dict()}
    raise HTTPException(status_code=400, detail="No transactions in mempool to mine")

@app.get("/api/chain")
def get_chain():
    """Returns the entire blockchain and current mempool state."""
    return {
        "chain": [b.to_dict() for b in blockchain.chain],
        "mempool": [tx.to_dict() for tx in blockchain.mempool]
    }

@app.get("/api/chain/validate")
def validate_chain():
    """
    Runs a comprehensive security audit of the entire blockchain history.
    Verifies hashes, Merkle roots, and cryptographic signatures.
    """
    return blockchain.validate_chain()

@app.post("/api/tamper")
def tamper_chain(req: TamperRequest):
    """
    Tamper Lab: Modifies a previous block artificially to simulate a security breach 
    and demonstrate the immutable ledger properties.
    """
    success = blockchain.tamper_block(req.block_index, req.new_amount)
    if success:
        return {"message": f"Block {req.block_index} has been successfully tampered."}
    raise HTTPException(status_code=400, detail="Invalid block index")

# Serve UI
@app.get("/")
def index():
    """Serves the main frontend Single Page Application (SPA)."""
    return FileResponse("static/index.html")

app.mount("/", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

"""
Blockchain Core Engine

This module defines the core architectural components of the blockchain, including
the Transaction model, Block model, and the Blockchain ledger and consensus engine.
"""

import time
from typing import List
from crypto_utils import verify_signature, hash_data

class Transaction:
    """
    Represents a single peer-to-peer transaction within the blockchain.
    """
    def __init__(self, sender: str, recipient: str, amount: float, timestamp: float, signature: str, sender_pub_key: str, tx_id: str = None):
        """
        Initializes a transaction object and computes its hash.
        
        Args:
            sender (str): The sender's wallet address.
            recipient (str): The recipient's wallet address.
            amount (float): The amount transferred.
            timestamp (float): The Unix timestamp of the transaction.
            signature (str): The base64 digital signature of the payload.
            sender_pub_key (str): The public key of the sender for verification.
            tx_id (str, optional): The pre-computed hash of the transaction. If None, it is calculated.
        """
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = timestamp
        self.signature = signature
        self.sender_pub_key = sender_pub_key
        
        self.tx_id = tx_id if tx_id else self.calculate_hash()

    def calculate_hash(self) -> str:
        """Computes the SHA-256 hash of the transaction payload."""
        payload = f"{self.sender}{self.recipient}{self.amount}{self.timestamp}"
        return hash_data(payload)
        
    def to_dict(self) -> dict:
        """Serializes the transaction into a dictionary."""
        return {
            "tx_id": self.tx_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "signature": self.signature,
            "sender_pub_key": self.sender_pub_key
        }

class Block:
    """
    Represents a single block in the blockchain, containing a list of transactions.
    """
    def __init__(self, index: int, transactions: List[Transaction], previous_hash: str, nonce: int = 0, difficulty: int = 4, timestamp: float = None, merkle_root: str = None, hash: str = None):
        """
        Initializes a Block object.
        
        Args:
            index (int): The position of the block in the chain.
            transactions (List[Transaction]): Transactions included in the block.
            previous_hash (str): The hash of the previous block in the chain.
            nonce (int): The proof-of-work counter.
            difficulty (int): The target leading zeros required for PoW.
            timestamp (float): Unix timestamp of block creation.
            merkle_root (str, optional): The pre-calculated Merkle root.
            hash (str, optional): The pre-calculated block hash.
        """
        self.index = index
        self.timestamp = timestamp or time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.difficulty = difficulty
        self.merkle_root = merkle_root if merkle_root else self.calculate_merkle_root()
        self.hash = hash if hash else self.calculate_hash()

    def calculate_merkle_root(self) -> str:
        """
        Computes the Merkle Root hash from the block's transactions.
        Provides a tamper-evident footprint of all transactions included.
        
        Returns:
            str: The Merkle Root SHA-256 hash.
        """
        if not self.transactions:
            return hash_data("")
        
        tx_hashes = [tx.tx_id for tx in self.transactions]
        
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 != 0:
                tx_hashes.append(tx_hashes[-1])
            new_hashes = []
            for i in range(0, len(tx_hashes), 2):
                new_hashes.append(hash_data(tx_hashes[i] + tx_hashes[i+1]))
            tx_hashes = new_hashes
            
        return tx_hashes[0]

    def calculate_hash(self) -> str:
        """
        Computes the SHA-256 hash of the block's header.
        
        Returns:
            str: The block's SHA-256 hash.
        """
        payload = f"{self.index}{self.timestamp}{self.merkle_root}{self.previous_hash}{self.nonce}"
        return hash_data(payload)

    def mine_block(self):
        """
        Executes the Proof-of-Work algorithm. Loops continuously, incrementing the 
        nonce until a block hash with the required number of leading zeros is found.
        """
        target = '0' * self.difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()
            
    def to_dict(self) -> dict:
        """Serializes the block into a dictionary."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "merkle_root": self.merkle_root,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "hash": self.hash
        }

class Blockchain:
    """
    Manages the entire ledger, mempool, validation logic, and consensus rules.
    """
    def __init__(self):
        self.chain: List[Block] = []
        self.mempool: List[Transaction] = []
        self.difficulty = 4
        self.mining_reward = 10.0
        
        self.create_genesis_block()

    def create_genesis_block(self):
        """Mints the hardcoded initial block of the blockchain."""
        genesis_tx = Transaction(
            sender="0x0000SYSTEM",
            recipient="0x0000SYSTEM",
            amount=0,
            timestamp=time.time(),
            signature="genesis",
            sender_pub_key="genesis"
        )
        genesis_block = Block(0, [genesis_tx], "0")
        genesis_block.mine_block()
        self.chain.append(genesis_block)

    def get_latest_block(self) -> Block:
        """Returns the most recent block in the chain."""
        return self.chain[-1]

    def get_balance(self, address: str) -> float:
        """Calculates the confirmed balance of a given address by traversing the chain."""
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address:
                    balance -= tx.amount
                if tx.recipient == address:
                    balance += tx.amount
        return balance

    def add_transaction(self, tx: Transaction) -> bool:
        """
        Validates and adds a new transaction to the mempool.
        
        Args:
            tx (Transaction): The transaction to be added.
            
        Raises:
            ValueError: If the signature is invalid, funds are insufficient, or parameters are invalid.
            
        Returns:
            bool: True if successfully added.
        """
        if tx.sender == "0x0000SYSTEM":
            return False
            
        if tx.sender == tx.recipient:
            raise ValueError("Sender cannot spend to themselves")
            
        # Verify digital signature
        payload = f"{tx.sender}{tx.recipient}{tx.amount}{tx.timestamp}"
        if not verify_signature(tx.sender_pub_key, tx.signature, payload):
            raise ValueError("Invalid cryptographic signature.")
            
        # Verify balance (including pending spends)
        balance = self.get_balance(tx.sender)
        pending_spend = sum(t.amount for t in self.mempool if t.sender == tx.sender)
        
        if balance < tx.amount + pending_spend:
            raise ValueError("Insufficient funds")
            
        self.mempool.append(tx)
        return True

    def mine_pending_transactions(self, miner_address: str) -> Block:
        """
        Groups mempool transactions, executes PoW, awards the miner, and appends the block.
        
        Args:
            miner_address (str): The address to receive the block reward.
            
        Returns:
            Block: The newly mined block.
        """
        if not self.mempool:
            return None
            
        # Mint the block reward transaction
        reward_tx = Transaction(
            sender="0x0000SYSTEM",
            recipient=miner_address,
            amount=self.mining_reward,
            timestamp=time.time(),
            signature="reward",
            sender_pub_key="system"
        )
        
        transactions_to_mine = self.mempool.copy()
        transactions_to_mine.append(reward_tx)
        
        latest_block = self.get_latest_block()
        new_block = Block(
            index=latest_block.index + 1,
            transactions=transactions_to_mine,
            previous_hash=latest_block.hash,
            difficulty=self.difficulty
        )
        
        new_block.mine_block()
        self.chain.append(new_block)
        self.mempool = []
        return new_block

    def validate_chain(self) -> dict:
        """
        Performs a deep cryptographic audit of the blockchain to detect tampering.
        
        Returns:
            dict: Audit result containing 'is_valid' boolean and 'corrupted_blocks' list.
        """
        corrupted_blocks = []
        
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # 1. Verify continuous chain linkage
            if current_block.previous_hash != previous_block.hash:
                corrupted_blocks.append(current_block.index)
                continue
                
            # 2. Verify block's native hash integrity
            if current_block.hash != current_block.calculate_hash():
                corrupted_blocks.append(current_block.index)
                continue
                
            # 3. Verify internal Merkle Root
            if current_block.merkle_root != current_block.calculate_merkle_root():
                corrupted_blocks.append(current_block.index)
                continue
                
            # 4. Verify all transaction signatures within the block
            invalid_signature = False
            for tx in current_block.transactions:
                if tx.sender == "0x0000SYSTEM":
                    continue
                payload = f"{tx.sender}{tx.recipient}{tx.amount}{tx.timestamp}"
                if not verify_signature(tx.sender_pub_key, tx.signature, payload):
                    invalid_signature = True
                    break
                    
            if invalid_signature:
                corrupted_blocks.append(current_block.index)
                continue
                    
        return {
            "is_valid": len(corrupted_blocks) == 0,
            "corrupted_blocks": list(set(corrupted_blocks))
        }
        
    def tamper_block(self, block_index: int, new_amount: float = None) -> bool:
        """
        TAMPER LAB UTILITY: Deliberately modifies a block's structure or transactions
        to simulate an attack, destroying the chain's integrity.
        
        Args:
            block_index (int): The index of the block to tamper.
            new_amount (float, optional): An unauthorized amount to change a transaction to.
            
        Returns:
            bool: True if successful.
        """
        if 0 < block_index < len(self.chain):
            block = self.chain[block_index]
            tampered = False
            
            if new_amount is not None:
                # Attempt to artificially alter a transaction's amount
                for tx in block.transactions:
                    if tx.sender != "0x0000SYSTEM":
                        tx.amount = new_amount
                        tx.tx_id = tx.calculate_hash()
                        tampered = True
                        break
                        
            if not tampered:
                # Corrupt the block's header hash if no transaction was targeted
                block.hash = hash_data("tampered" + block.hash)
            return True
        return False

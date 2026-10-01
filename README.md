# Secure Digital Payment System (Blockchain Lab)

A complete, production-grade, full-stack Blockchain-Based Secure Digital Payment System that demonstrates core cryptographic and blockchain principles including:
- **Asymmetric Cryptography:** ECDSA (secp256k1) key pair generation and client-side digital signatures.
- **Proof-of-Work (PoW):** Hash-based consensus algorithm with adjustable mining difficulty.
- **Cryptographic Chaining:** SHA-256 block hashing, Merkle Root construction, and strictly linked history.
- **Tamper Detection & Security Auditing:** An interactive environment designed to simulate network breaches and demonstrate immutable ledger integrity.

## Architecture & Tech Stack

- **Backend / Consensus Engine:** Python 3.x, `FastAPI`, `Uvicorn`
- **Cryptography:** Python `ecdsa`, `hashlib` (Backend) | `elliptic.js`, `crypto-js` (Frontend)
- **Frontend / UI:** HTML5, Vanilla JavaScript, Tailwind CSS (Glassmorphism UI)
- **Data Storage:** In-memory state (resets on server restart)

## Quick Start

### 1. Requirements
- Python 3.8+
- pip (Python package manager)

### 2. Installation
Navigate to the project directory and install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run the Server
Launch the FastAPI development server:
```bash
python app.py
```
The API and UI will be available at: **http://127.0.0.1:8000**

## Core Features & Workflow

### 1. Wallet Generation & Key Management
- Click **"Generate New Wallet"** on the dashboard.
- The system generates a highly secure **secp256k1** private and public key pair.
- The wallet address is derived deterministically from the SHA-256 hash of the public key.

### 2. P2P Transactions & Client-Side Signing
- You can create a transaction to transfer funds.
- **Security First:** The transaction payload is hashed and signed *client-side* inside your browser using your Private Key. The private key is never transmitted over the network.
- The backend verifies the signature using the Public Key before accepting it into the Mempool.

### 3. Proof-of-Work Mining
- Transactions sit in the **Mempool** until a miner processes them.
- Click **"Mine Block"** to execute the PoW algorithm. The engine loops until it finds a valid `nonce` that satisfies the target difficulty (hash starts with `0000`).
- The miner is rewarded with newly minted system coins (default: 10.00).

### 4. Interactive Security Audit & Tamper Lab
- Use the **Tamper Lab** to maliciously modify a previous block's transaction amount or break its hash.
- Run the **Security Audit**. The engine iterates through the entire chain verifying:
  1. `previous_hash` chains sequentially.
  2. Merkle Root integrity.
  3. Digital Signature authenticity for every non-system transaction.
  4. Block hash integrity.
- Tampered blocks and subsequent corrupted blocks are flagged instantly.

## Testing the Features (Step-by-Step Guide)

To verify all cryptographic and blockchain functionalities are working properly, follow this workflow in the UI:

### Test 1: Wallet Creation & Genesis State
1. Open the application at `http://127.0.0.1:8000`.
2. Scroll to the **Blockchain Explorer** on the right. You will see **Block #0 (GENESIS)** already mined and linked.
3. On the left under **Wallet Dashboard**, click **Generate New Wallet**.
4. Observe the generated Wallet Address, Public Key, and Private Key. Notice your balance is currently `0.00`.

### Test 2: Proof of Work & Mining Rewards
1. Without making any transactions, go to the **Mempool & Mining** section.
2. Click **Mine Block (PoW)**. 
3. The system will calculate hashes until it finds one starting with `0000`. 
4. Check the **Blockchain Explorer**; **Block #1** is now created.
5. Check your Wallet Dashboard. Your balance should now be `10.00` because the system awarded you for mining the block!

### Test 3: Client-Side Cryptographic Signatures (P2P Transfer)
1. Let's send money. In the **Transfer Funds** panel, enter a random recipient address (e.g., `0x1234567890abcdef`).
2. Enter an amount (e.g., `5.00`) and click **Sign & Send Transaction**.
3. *What happened under the hood:* The browser used your private key to generate an ECDSA signature, which was sent to the server. The server verified it using your public key.
4. You will see a success toast, and the transaction is now sitting in the **Mempool**.
5. Click **Mine Block (PoW)** again.
6. The transaction is confirmed in **Block #2**. Your wallet balance will drop to `15.00` (You had 10, sent 5, and gained another 10 as a mining reward for Block #2).

### Test 4: Dynamic Tamper Detection
1. Scroll down to the **Security Audit & Tamper Lab**. 
2. Let's act as a malicious hacker. Enter **Target Block Index**: `1` (which contains your first mining reward).
3. In **New TX Amount**, enter `100` (trying to fake a 100 coin reward instead of 10) and click **Inject Tamper**.
4. A warning toast will confirm the block was tampered with. 
5. The system automatically runs a **Security Audit**. 
6. Watch the UI: The audit will instantly fail. Block #1 and all subsequent blocks (Block #2) will turn **RED** and display a shaking animation. The cryptographic link is broken! 

## API Endpoints Reference

- `GET /api/wallet/create`: Generates keys and wallet address.
- `GET /api/wallet/balance/{address}`: Calculates the confirmed ledger balance.
- `POST /api/transaction/create`: Submits a signed transaction to the Mempool.
- `POST /api/mine`: Triggers PoW mining for the current mempool.
- `GET /api/chain`: Retrieves the full block history.
- `GET /api/chain/validate`: Runs full cryptographic validation of the ledger.
- `POST /api/tamper`: Simulates tampering of specific blocks for testing.

---
*Built as a demonstrative architectural lab for cryptographic and blockchain engineering principles.*

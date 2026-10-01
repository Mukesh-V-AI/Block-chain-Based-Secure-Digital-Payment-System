const API_BASE = 'http://localhost:8000/api';

// Initialize Elliptic Curve secp256k1
const EC = window.elliptic.ec;
const ec = new EC('secp256k1');

// DOM Elements
const btnCreateWallet = document.getElementById('btnCreateWallet');
const walletDetails = document.getElementById('walletDetails');
const elWalletAddress = document.getElementById('walletAddress');
const elPublicKey = document.getElementById('publicKey');
const elPrivateKey = document.getElementById('privateKey');
const elWalletBalance = document.getElementById('walletBalance');
const btnRefreshBalance = document.getElementById('btnRefreshBalance');

const transferForm = document.getElementById('transferForm');
const txRecipient = document.getElementById('txRecipient');
const txAmount = document.getElementById('txAmount');

const btnMineBlock = document.getElementById('btnMineBlock');
const mempoolContainer = document.getElementById('mempoolContainer');
const blockchainContainer = document.getElementById('blockchainContainer');

const btnAuditChain = document.getElementById('btnAuditChain');
const auditStatus = document.getElementById('auditStatus');
const auditIcon = document.getElementById('auditIcon');
const auditTitle = document.getElementById('auditTitle');
const auditMessage = document.getElementById('auditMessage');

const tamperForm = document.getElementById('tamperForm');
const tamperBlockIndex = document.getElementById('tamperBlockIndex');
const tamperTxAmount = document.getElementById('tamperTxAmount');

const toastContainer = document.getElementById('toastContainer');

// State
let currentWallet = null;

// --- TOAST NOTIFICATIONS ---
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    let bgColor = 'bg-blue-600';
    if (type === 'success') bgColor = 'bg-emerald-600';
    if (type === 'error') bgColor = 'bg-red-600';
    if (type === 'warning') bgColor = 'bg-orange-600';

    toast.className = `toast-notification px-4 py-3 rounded shadow-lg text-white font-medium text-sm ${bgColor} flex items-center justify-between min-w-[250px]`;
    toast.innerHTML = `
        <span>${message}</span>
        <button class="ml-4 hover:text-gray-200" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        if(toast.parentElement) {
            toast.classList.add('toast-hiding');
            setTimeout(() => toast.remove(), 300);
        }
    }, 4000);
}

// --- WALLET & CRYPTO LOGIC ---

btnCreateWallet.addEventListener('click', async () => {
    try {
        btnCreateWallet.textContent = 'Generating...';
        btnCreateWallet.disabled = true;

        const res = await fetch(`${API_BASE}/wallet/create`);
        const data = await res.json();
        
        currentWallet = data;
        
        elWalletAddress.textContent = data.address;
        elPublicKey.textContent = data.public_key;
        elPrivateKey.textContent = data.private_key;
        
        walletDetails.classList.remove('hidden');
        await updateBalance();
        showToast("Wallet generated successfully!", "success");
    } catch (e) {
        showToast("Failed to create wallet", "error");
        console.error(e);
    } finally {
        btnCreateWallet.textContent = 'Generate New Wallet';
        btnCreateWallet.disabled = false;
    }
});

btnRefreshBalance.addEventListener('click', updateBalance);

async function updateBalance() {
    if (!currentWallet) return;
    try {
        const res = await fetch(`${API_BASE}/wallet/balance/${currentWallet.address}`);
        const data = await res.json();
        elWalletBalance.textContent = data.balance.toFixed(2);
    } catch(e) {
        console.error("Balance fetch error", e);
    }
}

// Client-Side Signing Logic matching Python's sigencode_der
function signTransaction(privateKeyHex, sender, recipient, amount, timestamp) {
    const payload = `${sender}${recipient}${amount}${timestamp}`;
    const msgHash = CryptoJS.SHA256(payload).toString(CryptoJS.enc.Hex);
    const key = ec.keyFromPrivate(privateKeyHex, 'hex');
    const sig = key.sign(msgHash);
    const der = sig.toDER();
    return btoa(String.fromCharCode.apply(null, der));
}

// --- TRANSFER LOGIC ---

transferForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentWallet) {
        showToast("Please create a wallet first.", "warning");
        return;
    }

    const recipient = txRecipient.value.trim();
    const amount = parseFloat(txAmount.value);
    
    if (recipient === currentWallet.address) {
        showToast("Cannot send to yourself.", "error");
        return;
    }
    
    if (amount <= 0) {
        showToast("Amount must be greater than zero.", "error");
        return;
    }

    try {
        const timestamp = Date.now() / 1000.0;
        const signature = signTransaction(currentWallet.private_key, currentWallet.address, recipient, amount, timestamp);
        
        const txPayload = {
            sender: currentWallet.address,
            recipient: recipient,
            amount: amount,
            timestamp: timestamp,
            signature: signature,
            sender_pub_key: currentWallet.public_key
        };
        
        const res = await fetch(`${API_BASE}/transaction/create`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(txPayload)
        });
        
        const data = await res.json();
        if (res.ok) {
            txRecipient.value = '';
            txAmount.value = '';
            showToast("Transaction signed and added to mempool!", "success");
            await fetchChainData();
        } else {
            showToast(`Transaction failed: ${data.detail}`, "error");
        }
    } catch (e) {
        console.error(e);
        showToast("Transaction error.", "error");
    }
});


// --- BLOCKCHAIN DATA FETCHING ---

async function fetchChainData() {
    try {
        const res = await fetch(`${API_BASE}/chain`);
        const data = await res.json();
        
        renderMempool(data.mempool);
        renderBlockchain(data.chain);
    } catch (e) {
        console.error("Fetch chain error", e);
    }
}

function renderMempool(mempool) {
    mempoolContainer.innerHTML = '';
    
    if (mempool.length === 0) {
        mempoolContainer.innerHTML = '<div class="text-gray-500 text-sm italic">No pending transactions.</div>';
        return;
    }
    
    mempool.forEach(tx => {
        const el = document.createElement('div');
        el.className = 'bg-gray-800 p-3 rounded border border-gray-700 text-sm transition hover:bg-gray-700';
        el.innerHTML = `
            <div class="flex justify-between items-center mb-1">
                <span class="font-bold text-gray-300 truncate w-24" title="${tx.tx_id}">${tx.tx_id.substring(0, 8)}...</span>
                <span class="text-emerald-400 font-bold">${tx.amount}</span>
            </div>
            <div class="text-xs text-gray-500 flex justify-between">
                <span class="truncate w-1/2" title="${tx.sender}">From: ${tx.sender === '0x0000SYSTEM' ? 'SYSTEM' : tx.sender.substring(0,10)+'...'}</span>
                <span class="truncate w-1/2 text-right" title="${tx.recipient}">To: ${tx.recipient.substring(0,10)+'...'}</span>
            </div>
        `;
        mempoolContainer.appendChild(el);
    });
}

function renderBlockchain(chain) {
    blockchainContainer.innerHTML = '';
    
    const reversedChain = [...chain].reverse();
    
    reversedChain.forEach(block => {
        const isGenesis = block.index === 0;
        
        const el = document.createElement('div');
        el.className = `glass-panel p-4 rounded-xl block-card mb-4 border-l-4 border-emerald-500`;
        el.id = `block-${block.index}`;
        
        el.innerHTML = `
            <div class="flex justify-between items-center mb-2 border-b border-gray-700 pb-2">
                <div class="font-bold text-lg text-emerald-400">Block #${block.index} ${isGenesis ? '<span class="text-xs bg-emerald-900/50 text-emerald-300 px-2 py-1 rounded ml-2">GENESIS</span>' : ''}</div>
                <div class="text-xs text-gray-400">${new Date(block.timestamp * 1000).toLocaleString()}</div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs mb-3 font-mono">
                <div>
                    <span class="text-gray-500">Hash:</span>
                    <div class="truncate text-gray-300" title="${block.hash}">${block.hash}</div>
                </div>
                <div>
                    <span class="text-gray-500">Prev Hash:</span>
                    <div class="truncate text-gray-400" title="${block.previous_hash}">${block.previous_hash}</div>
                </div>
                <div>
                    <span class="text-gray-500">Merkle Root:</span>
                    <div class="truncate text-gray-400" title="${block.merkle_root}">${block.merkle_root}</div>
                </div>
                <div>
                    <span class="text-gray-500">Nonce:</span>
                    <div class="text-gray-300">${block.nonce}</div>
                </div>
            </div>
            
            <div>
                <div class="text-sm text-gray-400 font-semibold mb-2 flex items-center justify-between cursor-pointer hover:text-gray-200 transition" onclick="document.getElementById('txs-${block.index}').classList.toggle('hidden')">
                    <span>Transactions (${block.transactions.length})</span>
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                </div>
                
                <div id="txs-${block.index}" class="hidden space-y-2 mt-2">
                    ${block.transactions.map(tx => `
                        <div class="bg-gray-800 p-2 rounded text-xs border border-gray-700 hover:border-gray-500 transition">
                            <div class="flex justify-between text-gray-300 mb-1">
                                <span class="truncate w-3/4" title="${tx.tx_id}">ID: ${tx.tx_id}</span>
                                <span class="text-emerald-400 font-bold">${tx.amount}</span>
                            </div>
                            <div class="text-gray-500 flex justify-between">
                                <span class="truncate w-2/5" title="${tx.sender}">${tx.sender === '0x0000SYSTEM' ? 'SYSTEM' : tx.sender.substring(0,16)+'...'}</span>
                                <span>&rarr;</span>
                                <span class="truncate w-2/5 text-right" title="${tx.recipient}">${tx.recipient.substring(0,16)+'...'}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        blockchainContainer.appendChild(el);
    });
}

// --- MINING LOGIC ---

btnMineBlock.addEventListener('click', async () => {
    btnMineBlock.disabled = true;
    btnMineBlock.innerHTML = `<svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Mining...`;
    
    try {
        const minerAddress = currentWallet ? currentWallet.address : "0x0000MINER_ANONYMOUS";
        
        const res = await fetch(`${API_BASE}/mine`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ miner_address: minerAddress })
        });
        
        const data = await res.json();
        if (res.ok) {
            showToast("Block mined successfully! PoW solved.", "success");
            await fetchChainData();
            if(currentWallet) await updateBalance();
            await runAudit();
        } else {
            showToast("Mining failed: " + data.detail, "error");
        }
    } catch (e) {
        console.error(e);
        showToast("Mining error.", "error");
    } finally {
        btnMineBlock.disabled = false;
        btnMineBlock.innerHTML = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg> Mine Block (PoW)`;
    }
});


// --- AUDIT & TAMPER LOGIC ---

btnAuditChain.addEventListener('click', runAudit);

async function runAudit() {
    auditStatus.classList.remove('hidden');
    auditStatus.className = 'mb-4 p-3 rounded-lg border flex items-center gap-3 bg-blue-900/50 border-blue-500 text-blue-100';
    auditIcon.innerHTML = `<svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>`;
    auditTitle.textContent = "Auditing Ledger...";
    auditMessage.textContent = "Verifying hashes and signatures...";
    
    try {
        const res = await fetch(`${API_BASE}/chain/validate`);
        const data = await res.json();
        
        document.querySelectorAll('.block-card').forEach(el => {
            el.classList.remove('block-invalid', 'border-red-500');
            el.classList.add('block-valid', 'border-emerald-500');
        });
        
        if (data.is_valid) {
            auditStatus.className = 'mb-4 p-3 rounded-lg border flex items-center gap-3 bg-emerald-900/30 border-emerald-500 text-emerald-100 transition-all';
            auditIcon.innerHTML = `<svg class="h-6 w-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`;
            auditTitle.textContent = "Chain is SECURE";
            auditMessage.textContent = "All cryptographic links and signatures are valid.";
            showToast("Ledger verification passed.", "success");
        } else {
            auditStatus.className = 'mb-4 p-3 rounded-lg border flex items-center gap-3 bg-red-900/30 border-red-500 text-red-100 transition-all';
            auditIcon.innerHTML = `<svg class="h-6 w-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>`;
            auditTitle.textContent = "SECURITY ALERT - TAMPERING DETECTED";
            auditMessage.textContent = `Integrity failure at blocks: ${data.corrupted_blocks.join(', ')}. All subsequent blocks invalidated.`;
            
            showToast("Chain tampering detected!", "error");

            const minCorrupted = Math.min(...data.corrupted_blocks);
            
            document.querySelectorAll('.block-card').forEach(el => {
                const idAttr = el.id;
                if (idAttr) {
                    const idx = parseInt(idAttr.split('-')[1]);
                    if (idx >= minCorrupted) {
                        el.classList.remove('block-valid', 'border-emerald-500');
                        el.classList.add('block-invalid', 'border-red-500');
                    }
                }
            });
        }
    } catch (e) {
        console.error(e);
        auditStatus.className = 'mb-4 p-3 rounded-lg border flex items-center gap-3 bg-red-900/30 border-red-500 text-red-100';
        auditTitle.textContent = "Audit Failed";
        auditMessage.textContent = "Could not communicate with the node.";
        showToast("Audit Failed.", "error");
    }
}

tamperForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const idx = parseInt(tamperBlockIndex.value);
    const amountVal = tamperTxAmount.value;
    const amount = amountVal ? parseFloat(amountVal) : null;
    
    try {
        const payload = { block_index: idx };
        if (amount !== null) payload.new_amount = amount;
        
        const res = await fetch(`${API_BASE}/tamper`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            tamperTxAmount.value = '';
            tamperBlockIndex.value = '';
            showToast(`Block ${idx} tampered successfully.`, "warning");
            await fetchChainData();
            await runAudit();
        } else {
            const data = await res.json();
            showToast(`Tamper failed: ${data.detail}`, "error");
        }
    } catch (e) {
        console.error(e);
        showToast("Tamper API error", "error");
    }
});

// Initialization
fetchChainData();

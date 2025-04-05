// blockchain-ui.js - JavaScript to handle blockchain integration
// Add this to your existing JavaScript file or include as a separate script

document.addEventListener('DOMContentLoaded', function() {
    // Blockchain tab activation
    document.getElementById('blockchain-tab').addEventListener('click', initBlockchain);
    
    // Blockchain trade form submission
    document.getElementById('blockchainTradeForm').addEventListener('submit', function(e) {
        e.preventDefault();
        submitBlockchainTrade();
    });
    
    // Refresh blockchain transactions
    document.getElementById('refreshBlockchainTx').addEventListener('click', loadBlockchainTransactions);
});

// Initialize blockchain functionality
function initBlockchain() {
    checkBlockchainStatus();
    loadBlockchainTransactions();
}

// Check the blockchain connection status
function checkBlockchainStatus() {
    const statusBadge = document.getElementById('blockchainStatusBadge');
    const statusDiv = document.getElementById('blockchainStatus');
    
    statusBadge.className = 'badge bg-secondary';
    statusBadge.textContent = 'Checking...';
    
    fetch('/api/blockchain/status')
        .then(response => response.json())
        .then(data => {
            if (data.connected) {
                statusBadge.className = 'badge bg-success';
                statusBadge.textContent = data.demoMode ? 'Demo Mode' : 'Connected';
                
                statusDiv.innerHTML = `
                    <div class="alert alert-success">
                        <strong>Connected to Blockchain</strong>
                        ${data.demoMode ? '<span class="badge bg-info ms-2">Demo Mode</span>' : ''}
                    </div>
                    <p>Account: <code>${data.account}</code></p>
                    <p class="text-muted small">
                        ${data.demoMode 
                            ? 'Running in demonstration mode. No actual blockchain transactions will be made.' 
                            : 'Connected to Ethereum test network. Transactions will be recorded on the test blockchain.'}
                    </p>
                `;
            } else {
                statusBadge.className = 'badge bg-danger';
                statusBadge.textContent = 'Disconnected';
                
                statusDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Blockchain Connection Failed</strong>
                    </div>
                    <p>Error: ${data.error || 'Could not connect to blockchain'}</p>
                    <button class="btn btn-sm btn-outline-primary" onclick="checkBlockchainStatus()">Retry Connection</button>
                `;
            }
        })
        .catch(error => {
            statusBadge.className = 'badge bg-danger';
            statusBadge.textContent = 'Error';
            
            statusDiv.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Blockchain Connection Error</strong>
                </div>
                <p>Error: ${error.message}</p>
                <button class="btn btn-sm btn-outline-primary" onclick="checkBlockchainStatus()">Retry Connection</button>
            `;
        });
}

// Load and display blockchain transactions
function loadBlockchainTransactions() {
    const transactionsDiv = document.getElementById('blockchainTransactions');
    
    transactionsDiv.innerHTML = '<p class="text-center"><div class="spinner-border spinner-border-sm text-primary" role="status"></div> Loading transactions...</p>';
    
    fetch('/api/blockchain/trades')
        .then(response => response.json())
        .then(trades => {
            if (trades.length === 0) {
                transactionsDiv.innerHTML = '<p class="text-center text-muted">No transactions yet</p>';
                return;
            }
            
            transactionsDiv.innerHTML = '';
            
            trades.forEach(trade => {
                const tradeElement = document.createElement('div');
                tradeElement.className = 'list-group-item';
                
                // Format energy amount (convert Wh to kWh)
                const energyKWh = (trade.energyAmount / 1000).toFixed(2);
                
                tradeElement.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <span>
                            <span class="badge bg-primary">Trade #${trade.id}</span>
                            ${energyKWh} kWh at ${trade.price} ETH/kWh
                        </span>
                        <button class="btn btn-sm btn-outline-success buy-energy" data-id="${trade.id}">
                            Buy
                        </button>
                    </div>
                    <div class="text-muted small mt-1">
                        Seller: <code>${abbreviateAddress(trade.seller)}</code>
                        <br>Created: ${formatDate(trade.timestamp)}
                    </div>
                `;
                
                transactionsDiv.appendChild(tradeElement);
            });
            
            // Add event listeners to buy buttons
            document.querySelectorAll('.buy-energy').forEach(button => {
                button.addEventListener('click', function() {
                    buyEnergyOnBlockchain(this.dataset.id);
                });
            });
        })
        .catch(error => {
            transactionsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Error Loading Transactions</strong>
                    <p>${error.message}</p>
                </div>
                <button class="btn btn-sm btn-outline-primary" onclick="loadBlockchainTransactions()">Try Again</button>
            `;
        });
}

// Submit a trade to the blockchain
function submitBlockchainTrade() {
    const type = document.getElementById('bcTradeType').value;
    const amount = parseFloat(document.getElementById('bcAmount').value);
    const price = parseFloat(document.getElementById('bcPrice').value);
    
    // Only selling is implemented in the smart contract
    if (type === 'buy') {
        alert('Buy orders are not supported directly. Please purchase an existing sell order.');
        return;
    }
    
    // Convert kWh to Wh for the contract
    const amountWh = Math.floor(amount * 1000);
    
    // Show processing indicator
    const submitButton = document.querySelector('#blockchainTradeForm button[type="submit"]');
    const originalButtonText = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div> Processing...';
    
    fetch('/api/blockchain/trades', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            energyAmount: amountWh,
            price: price
        })
    })
    .then(response => response.json())
    .then(data => {
        // Reset button
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonText;
        
        if (data.success) {
            // Show transaction details
            showTransactionDetails(data.transactionHash, 'Trade Created');
            
            // Reset form
            document.getElementById('blockchainTradeForm').reset();
            
            // Refresh transactions
            loadBlockchainTransactions();
        } else {
            alert('Error creating trade: ' + data.error);
        }
    })
    .catch(error => {
        // Reset button
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonText;
        
        alert('Error: ' + error.message);
    });
}

// Buy energy on the blockchain
function buyEnergyOnBlockchain(tradeId) {
    if (!confirm('Are you sure you want to purchase this energy?')) {
        return;
    }
    
    fetch(`/api/blockchain/trades/${tradeId}/fulfill`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show transaction details
            showTransactionDetails(data.transactionHash, 'Energy Purchased');
            
            // Refresh transactions
            loadBlockchainTransactions();
        } else {
            alert('Error purchasing energy: ' + data.error);
        }
    })
    .catch(error => {
        alert('Error: ' + error.message);
    });
}

// Show transaction details modal and start monitoring
function showTransactionDetails(txHash, title) {
    // Get modal elements
    const modal = new bootstrap.Modal(document.getElementById('txDetailsModal'));
    const modalTitle = document.querySelector('#txDetailsModal .modal-title');
    const txDetails = document.getElementById('txDetails');
    const progress = document.getElementById('txConfirmationProgress');
    const confirmationText = document.getElementById('txConfirmationText');
    const viewOnExplorer = document.getElementById('viewOnExplorer');
    
    // Set modal content
    modalTitle.textContent = title;
    txDetails.innerHTML = `
        <div class="text-center mb-3">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2">Processing transaction...</p>
        </div>
        <div class="alert alert-info">
            <strong>Transaction Hash:</strong>
            <br><code>${txHash}</code>
        </div>
    `;
    
    // Set explorer link (using Sepolia testnet explorer)
    viewOnExplorer.href = `https://sepolia.etherscan.io/tx/${txHash}`;
    
    // Reset progress bar
    progress.style.width = '0%';
    confirmationText.textContent = 'Waiting for confirmation...';
    
    // Show modal
    modal.show();
    
    // Start monitoring transaction status
    monitorTransaction(txHash);
}

// Monitor transaction status
function monitorTransaction(txHash) {
    // In a demo implementation, we'll simulate confirmations
    const progress = document.getElementById('txConfirmationProgress');
    const confirmationText = document.getElementById('txConfirmationText');
    const txDetails = document.getElementById('txDetails');
    
    let confirmations = 0;
    const maxConfirmations = 6; // Ethereum typically considers 6 confirmations as "final"
    
    // Check status every 3 seconds
    const interval = setInterval(() => {
        fetch(`/api/blockchain/transaction/${txHash}/status`)
            .then(response => response.json())
            .then(data => {
                confirmations = data.confirmations;
                const percentage = Math.min((confirmations / maxConfirmations) * 100, 100);
                
                // Update progress bar
                progress.style.width = `${percentage}%`;
                confirmationText.textContent = `${confirmations} of ${maxConfirmations} confirmations`;
                
                if (confirmations >= maxConfirmations) {
                    // Transaction confirmed
                    clearInterval(interval);
                    
                    progress.classList.remove('progress-bar-animated');
                    progress.classList.add('bg-success');
                    confirmationText.textContent = 'Transaction confirmed!';
                    
                    txDetails.innerHTML = `
                        <div class="alert alert-success">
                            <i class="bi bi-check-circle-fill"></i> Transaction Confirmed
                        </div>
                        <table class="table table-sm">
                            <tr>
                                <th>Transaction Hash:</th>
                                <td><code>${data.hash}</code></td>
                            </tr>
                            <tr>
                                <th>Block Number:</th>
                                <td>${data.blockNumber}</td>
                            </tr>
                            <tr>
                                <th>Confirmations:</th>
                                <td>${data.confirmations}</td>
                            </tr>
                        </table>
                    `;
                }
            })
            .catch(error => {
                console.error('Error checking transaction status:', error);
            });
    }, 3000);
    
    // Clear interval when modal is closed
    document.getElementById('txDetailsModal').addEventListener('hidden.bs.modal', function () {
        clearInterval(interval);
    }, { once: true });
}

// Helper function to abbreviate blockchain address
function abbreviateAddress(address) {
    if (!address) return '';
    return address.substring(0, 6) + '...' + address.substring(address.length - 4);
}

// Helper function to format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}
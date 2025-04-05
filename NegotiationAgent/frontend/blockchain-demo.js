// blockchain-demo.js - Standalone Blockchain Demo for Frontend

class BlockchainDemo {
    constructor() {
        // Mock blockchain configuration
        this.config = {
            account: '0x742d35Cc6634C0532925a3b844Bc454e4438f44e',
            demoMode: true
        };

        // Mock trades storage
        this.trades = [
            {
                id: 1,
                seller: '0x93F4ec6dEB14e48048E2aB6910Fd3D21d2DCeeAb',
                energyAmount: 5000, // 5 kWh
                price: 0.0825,
                timestamp: new Date(Date.now() - 3600000).toISOString()
            },
            {
                id: 2,
                seller: '0x1a58916EDc96D6Ea6a2D3e3BC163e8d9F0B0c69c',
                energyAmount: 8000, // 8 kWh
                price: 0.0775,
                timestamp: new Date(Date.now() - 7200000).toISOString()
            }
        ];
    }

    // Get blockchain status
    getStatus() {
        return {
            connected: true,
            demoMode: this.config.demoMode,
            account: this.config.account
        };
    }

    // Get trades
    getTrades() {
        return this.trades;
    }

    // Create a new trade
    createTrade(energyAmount, price) {
        const newTrade = {
            id: this.trades.length + 1,
            seller: this.config.account,
            energyAmount: Math.floor(energyAmount * 1000), // Convert kWh to Wh
            price: price,
            timestamp: new Date().toISOString()
        };

        this.trades.push(newTrade);

        return {
            success: true,
            transactionHash: this.generateTransactionHash(),
            trade: newTrade
        };
    }

    // Buy a trade
    buyTrade(tradeId) {
        const trade = this.trades.find(t => t.id === tradeId);
        
        if (!trade) {
            return { success: false, error: 'Trade not found' };
        }

        return {
            success: true,
            transactionHash: this.generateTransactionHash(),
            trade: trade
        };
    }

    // Generate mock transaction hash
    generateTransactionHash() {
        const characters = '0123456789abcdef';
        let hash = '0x';
        for (let i = 0; i < 64; i++) {
            hash += characters.charAt(Math.floor(Math.random() * characters.length));
        }
        return hash;
    }

    // Monitor transaction (simulate blockchain confirmation)
    monitorTransaction(txHash) {
        return new Promise((resolve) => {
            const maxConfirmations = 6;
            let currentConfirmations = 0;

            const interval = setInterval(() => {
                currentConfirmations++;

                if (currentConfirmations >= maxConfirmations) {
                    clearInterval(interval);
                    resolve({
                        hash: txHash,
                        blockNumber: Math.floor(Math.random() * 10000000),
                        confirmations: maxConfirmations
                    });
                }
            }, 1000);
        });
    }
}

// Expose to global scope for easy access
window.BlockchainDemo = BlockchainDemo;

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Create global blockchain demo instance
    window.blockchainDemo = new BlockchainDemo();

    // Hijack existing blockchain functions to use demo
    window.initBlockchain = function() {
        const statusBadge = document.getElementById('blockchainStatusBadge');
        const statusDiv = document.getElementById('blockchainStatus');
        
        const status = window.blockchainDemo.getStatus();
        
        statusBadge.className = 'badge bg-success';
        statusBadge.textContent = 'Demo Mode';
        
        statusDiv.innerHTML = `
            <div class="alert alert-success">
                <strong>Connected to Blockchain</strong>
                <span class="badge bg-info ms-2">Demo Mode</span>
            </div>
            <p>Account: <code>${status.account}</code></p>
            <p class="text-muted small">Running in demonstration mode. No actual blockchain transactions will be made.</p>
        `;
        
        window.loadBlockchainTransactions();
    };

    window.loadBlockchainTransactions = function() {
        const transactionsDiv = document.getElementById('blockchainTransactions');
        const trades = window.blockchainDemo.getTrades();
        
        transactionsDiv.innerHTML = '';
        
        trades.forEach(trade => {
            const tradeElement = document.createElement('div');
            tradeElement.className = 'list-group-item';
            
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
                window.buyEnergyOnBlockchain(this.dataset.id);
            });
        });
    };

    window.submitBlockchainTrade = function() {
        const type = document.getElementById('bcTradeType').value;
        const amount = parseFloat(document.getElementById('bcAmount').value);
        const price = parseFloat(document.getElementById('bcPrice').value);
        
        if (type === 'buy') {
            alert('Buy orders are not supported. Please purchase an existing sell order.');
            return;
        }
        
        const submitButton = document.querySelector('#blockchainTradeForm button[type="submit"]');
        const originalButtonText = submitButton.innerHTML;
        submitButton.disabled = true;
        submitButton.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div> Processing...';
        
        try {
            const result = window.blockchainDemo.createTrade(amount, price);
            
            submitButton.disabled = false;
            submitButton.innerHTML = originalButtonText;
            
            window.showTransactionDetails(result.transactionHash, 'Trade Created');
            document.getElementById('blockchainTradeForm').reset();
            window.loadBlockchainTransactions();
        } catch (error) {
            alert('Error creating trade: ' + error.message);
            submitButton.disabled = false;
            submitButton.innerHTML = originalButtonText;
        }
    };

    window.buyEnergyOnBlockchain = function(tradeId) {
        if (!confirm('Are you sure you want to purchase this energy?')) {
            return;
        }
        
        try {
            const result = window.blockchainDemo.buyTrade(parseInt(tradeId));
            
            if (result.success) {
                window.showTransactionDetails(result.transactionHash, 'Energy Purchased');
                window.loadBlockchainTransactions();
            } else {
                alert('Error purchasing energy: ' + result.error);
            }
        } catch (error) {
            alert('Error: ' + error.message);
        }
    };

    window.showTransactionDetails = function(txHash, title) {
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
        
        // Set explorer link (simulated)
        viewOnExplorer.href = `https://sepolia.etherscan.io/tx/${txHash}`;
        
        // Reset progress bar
        progress.style.width = '0%';
        confirmationText.textContent = 'Waiting for confirmation...';
        
        // Show modal
        modal.show();
        
        // Start monitoring transaction status
        window.blockchainDemo.monitorTransaction(txHash)
            .then(data => {
                progress.style.width = '100%';
                progress.classList.remove('progress-bar-animated');
                progress.classList.add('bg-success');
                confirmationText.textContent = 'Transaction confirmed!';
                
                txDetails.innerHTML = `
                    <div class="alert alert-success">
                        <i class="bi bi-check-circle-fill"></i> Transaction Confirmed
                    </div>
                    <table class="table table-sm" style="word-break: break-all; table-layout: fixed; width: 100%;">
                        <tr>
                            <th>Transaction Hash:</th>
                            <td><div style="word-break: break-all;"><code>${data.hash}</code></div></td>
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
            });
    };

    // Utility functions (ensure they are defined globally)
    window.abbreviateAddress = function(address) {
        if (!address) return '';
        return address.substring(0, 6) + '...' + address.substring(address.length - 4);
    };

    window.formatDate = function(dateString) {
        return new Date(dateString).toLocaleString();
    };
});
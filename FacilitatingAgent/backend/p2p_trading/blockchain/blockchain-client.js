const Web3 = require('web3');
const contractABI = require('./contractABI.json'); // We'll create this file next

class BlockchainClient {
    constructor(demoMode = true) {
        this.demoMode = demoMode;
        this.contractAddress = '0x0000000000000000000000000000000000000000'; // Replace with actual deployed contract
        
        // For demo purposes - connect to a test network
        // In production, you would use a real Ethereum network
        if (demoMode) {
            // Connect to a local ganache instance for demo
            this.web3 = new Web3('http://localhost:8545');
            console.log('Connected to local blockchain in DEMO mode');
        } else {
            // Connect to Sepolia test network - you would need to provide your own endpoint
            this.web3 = new Web3('https://sepolia.infura.io/v3/YOUR_INFURA_PROJECT_ID');
            console.log('Connected to Sepolia test network');
        }
        
        // Initialize the contract
        this.contract = new this.web3.eth.Contract(contractABI, this.contractAddress);
    }
    
    // Get the current account
    async getAccount() {
        const accounts = await this.web3.eth.getAccounts();
        return accounts[0];
    }
    
    // Create a new energy trade
    async createEnergyTrade(energyAmount, pricePerKWh) {
        try {
            const account = await this.getAccount();
            
            // Convert price to wei
            const priceInWei = this.web3.utils.toWei(pricePerKWh.toString(), 'ether');
            
            // Create the transaction
            const tx = await this.contract.methods.createTrade(energyAmount, priceInWei).send({
                from: account,
                gas: 3000000
            });
            
            console.log('Trade created on blockchain:', tx.transactionHash);
            return {
                success: true,
                tradeId: tx.events.TradeCreated.returnValues.tradeId,
                transactionHash: tx.transactionHash
            };
        } catch (error) {
            console.error('Error creating energy trade:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    // Fulfill an energy trade
    async fulfillEnergyTrade(tradeId) {
        try {
            const account = await this.getAccount();
            
            // Get trade details to calculate price
            const tradeDetails = await this.contract.methods.getTradeDetails(tradeId).call();
            const totalPrice = (tradeDetails.energyAmount * tradeDetails.price) / 1000;
            
            // Buy the energy
            const tx = await this.contract.methods.fulfillTrade(tradeId).send({
                from: account,
                value: totalPrice,
                gas: 3000000
            });
            
            console.log('Trade fulfilled on blockchain:', tx.transactionHash);
            return {
                success: true,
                transactionHash: tx.transactionHash
            };
        } catch (error) {
            console.error('Error fulfilling energy trade:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    // Get all active trades
    async getActiveTrades() {
        try {
            const activeTrades = await this.contract.methods.getActiveTrades().call();
            const tradeDetails = [];
            
            // Get details for each active trade
            for (const tradeId of activeTrades) {
                const details = await this.contract.methods.getTradeDetails(tradeId).call();
                tradeDetails.push({
                    id: tradeId,
                    seller: details.seller,
                    energyAmount: details.energyAmount,
                    price: this.web3.utils.fromWei(details.price, 'ether'),
                    timestamp: new Date(details.timestamp * 1000).toISOString()
                });
            }
            
            return tradeDetails;
        } catch (error) {
            console.error('Error getting active trades:', error);
            return [];
        }
    }
    
    // Get user's balance
    async getBalance(address) {
        try {
            if (!address) {
                address = await this.getAccount();
            }
            
            const balance = await this.contract.methods.balances(address).call();
            return this.web3.utils.fromWei(balance, 'ether');
        } catch (error) {
            console.error('Error getting balance:', error);
            return '0';
        }
    }
    
    // Deposit funds
    async deposit(amount) {
        try {
            const account = await this.getAccount();
            const amountInWei = this.web3.utils.toWei(amount.toString(), 'ether');
            
            const tx = await this.contract.methods.deposit().send({
                from: account,
                value: amountInWei,
                gas: 3000000
            });
            
            console.log('Deposit successful:', tx.transactionHash);
            return {
                success: true,
                transactionHash: tx.transactionHash
            };
        } catch (error) {
            console.error('Error depositing funds:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    // Withdraw funds
    async withdraw(amount) {
        try {
            const account = await this.getAccount();
            const amountInWei = this.web3.utils.toWei(amount.toString(), 'ether');
            
            const tx = await this.contract.methods.withdraw(amountInWei).send({
                from: account,
                gas: 3000000
            });
            
            console.log('Withdrawal successful:', tx.transactionHash);
            return {
                success: true,
                transactionHash: tx.transactionHash
            };
        } catch (error) {
            console.error('Error withdrawing funds:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    // Generate a fake transaction hash for demo purposes
    generateDemoTransactionHash() {
        const characters = '0123456789abcdef';
        let hash = '0x';
        for (let i = 0; i < 64; i++) {
            hash += characters.charAt(Math.floor(Math.random() * characters.length));
        }
        return hash;
    }
    
    // Demo mode implementations that simulate blockchain operations
    async demoCreateEnergyTrade(energyAmount, pricePerKWh) {
        if (!this.demoMode) return this.createEnergyTrade(energyAmount, pricePerKWh);
        
        // Simulate blockchain delay
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        const tradeId = Math.floor(Math.random() * 1000);
        const txHash = this.generateDemoTransactionHash();
        
        console.log('Demo trade created:', txHash);
        return {
            success: true,
            tradeId: tradeId,
            transactionHash: txHash
        };
    }
    
    async demoFulfillEnergyTrade(tradeId) {
        if (!this.demoMode) return this.fulfillEnergyTrade(tradeId);
        
        // Simulate blockchain delay
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        const txHash = this.generateDemoTransactionHash();
        
        console.log('Demo trade fulfilled:', txHash);
        return {
            success: true,
            transactionHash: txHash
        };
    }
    
    async demoGetActiveTrades() {
        if (!this.demoMode) return this.getActiveTrades();
        
        // Generate some demo trades
        const demoTrades = [];
        const numTrades = Math.floor(Math.random() * 5) + 2; // 2-6 trades
        
        for (let i = 0; i < numTrades; i++) {
            demoTrades.push({
                id: i,
                seller: '0x' + '1234567890abcdef'.repeat(2) + i.toString(16).padStart(2, '0'),
                energyAmount: Math.floor(Math.random() * 10000) + 500, // 500-10500 Wh
                price: (Math.random() * 0.1 + 0.05).toFixed(4), // 0.05-0.15 ETH per kWh
                timestamp: new Date(Date.now() - Math.random() * 86400000).toISOString() // Last 24 hours
            });
        }
        
        return demoTrades;
    }
}

module.exports = BlockchainClient;

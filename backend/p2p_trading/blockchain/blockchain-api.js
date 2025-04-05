const express = require('express');
const router = express.Router();
const BlockchainClient = require('./blockchain-client');

// Initialize blockchain client in demo mode
const blockchainClient = new BlockchainClient(true);

// Get blockchain status
router.get('/status', async (req, res) => {
    try {
        const account = await blockchainClient.getAccount();
        res.json({
            connected: true,
            account: account,
            demoMode: blockchainClient.demoMode
        });
    } catch (error) {
        res.status(500).json({
            connected: false,
            error: error.message
        });
    }
});

// Get active trades from blockchain
router.get('/trades', async (req, res) => {
    try {
        const trades = await blockchainClient.demoGetActiveTrades();
        res.json(trades);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Create a new trade on blockchain
router.post('/trades', async (req, res) => {
    try {
        const { energyAmount, price } = req.body;
        
        if (!energyAmount || !price) {
            return res.status(400).json({ error: 'Energy amount and price are required' });
        }
        
        const result = await blockchainClient.demoCreateEnergyTrade(
            parseInt(energyAmount),
            parseFloat(price)
        );
        
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Fulfill (buy) a trade
router.post('/trades/:id/fulfill', async (req, res) => {
    try {
        const tradeId = req.params.id;
        const result = await blockchainClient.demoFulfillEnergyTrade(tradeId);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get user balance
router.get('/balance', async (req, res) => {
    try {
        const address = req.query.address; // Optional
        const balance = await blockchainClient.getBalance(address);
        res.json({ balance });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Demo endpoint to simulate transaction progress
router.get('/transaction/:hash/status', (req, res) => {
    const txHash = req.params.hash;
    
    // Simulate blockchain confirmations
    // In a real implementation, you would query the blockchain for this information
    const confirmations = Math.floor(Math.random() * 10) + 1;
    const status = confirmations >= 6 ? 'confirmed' : 'pending';
    
    res.json({
        hash: txHash,
        status: status,
        confirmations: confirmations,
        blockNumber: status === 'confirmed' ? Math.floor(Math.random() * 1000000) + 15000000 : null,
        timestamp: Date.now()
    });
});

module.exports = router;

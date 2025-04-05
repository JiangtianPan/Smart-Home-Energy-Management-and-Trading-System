// server.js
// Main backend server file with blockchain integration

const express = require('express');
const bodyParser = require('body-parser');
const session = require('express-session');
const path = require('path');

// Import blockchain routes
const blockchainRoutes = require('./blockchain-api');

// Create Express app
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));
app.use(session({
    secret: 'energy-trading-secret-key',
    resave: false,
    saveUninitialized: true,
    cookie: { secure: false } // Set to true in production with HTTPS
}));

// Sample user data (in a real app, this would be in a database)
const users = [
    { username: 'user1', password: 'password1' },
    { username: 'user2', password: 'password2' },
    { username: 'user3', password: 'password3' }
];

// Sample orders data (in a real app, this would be in a database)
let orders = [
    { id: 1, user: 'user1', type: 'sell', amount: 5.0, price: 0.15, status: 'open' },
    { id: 2, user: 'user2', type: 'buy', amount: 3.5, price: 0.12, status: 'open' },
    { id: 3, user: 'user3', type: 'sell', amount: 2.0, price: 0.14, status: 'open' }
];

// Sample trade history (in a real app, this would be in a database)
let tradeHistory = [
    { id: 101, user: 'user1', type: 'sell', amount: 4.0, price: 0.13, status: 'matched', match_time: '2025-03-01T10:30:00', matched_with: 102 },
    { id: 102, user: 'user2', type: 'buy', amount: 4.0, price: 0.13, status: 'matched', match_time: '2025-03-01T10:30:00', matched_with: 101 }
];

// Authentication middleware
const requireLogin = (req, res, next) => {
    if (req.session.user) {
        next();
    } else {
        res.status(401).json({ error: 'Unauthorized' });
    }
};

// Routes

// Login
app.post('/login', (req, res) => {
    const { username, password } = req.body;
    
    const user = users.find(u => u.username === username && u.password === password);
    
    if (user) {
        req.session.user = { username: user.username };
        res.json({ success: true });
    } else {
        res.json({ error: 'Invalid username or password' });
    }
});

// Logout
app.post('/logout', (req, res) => {
    req.session.destroy();
    res.json({ success: true });
});

// Get current user
app.get('/current_user', (req, res) => {
    if (req.session.user) {
        res.json({ logged_in: true, username: req.session.user.username });
    } else {
        res.json({ logged_in: false });
    }
});

// Get all open orders
app.get('/orders', requireLogin, (req, res) => {
    // In a real app, you would filter orders from a database
    const openOrders = orders.filter(order => order.status === 'open');
    res.json(openOrders);
});

// Get user's orders
app.get('/my_orders', requireLogin, (req, res) => {
    // In a real app, you would query orders from a database
    const username = req.session.user.username;
    const userOrders = orders.filter(order => order.user === username);
    res.json(userOrders);
});

// Get trade history
app.get('/trade_history', requireLogin, (req, res) => {
    // In a real app, you would query trade history from a database
    res.json(tradeHistory);
});

// Submit a new order
app.post('/submit_order', requireLogin, (req, res) => {
    const { type, amount, price } = req.body;
    const username = req.session.user.username;
    
    // Create a new order
    const newOrder = {
        id: orders.length + 1,
        user: username,
        type,
        amount: parseFloat(amount),
        price: parseFloat(price),
        status: 'open'
    };
    
    // In a real app, you would save to a database
    orders.push(newOrder);
    
    res.json({ success: true, order: newOrder });
});

// Delete an order
app.delete('/delete_order/:id', requireLogin, (req, res) => {
    const orderId = parseInt(req.params.id);
    const username = req.session.user.username;
    
    // Find the order
    const orderIndex = orders.findIndex(order => 
        order.id === orderId && order.user === username && order.status === 'open'
    );
    
    if (orderIndex === -1) {
        return res.json({ error: 'Order not found or cannot be deleted' });
    }
    
    // Remove the order (in a real app, you would mark as deleted in a database)
    orders.splice(orderIndex, 1);
    
    res.json({ success: true });
});

// Blockchain API routes
app.use('/api/blockchain', blockchainRoutes);

// Start server
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
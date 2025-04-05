// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title EnergyTrading
 * @dev Smart contract for P2P energy trading demonstration
 */
contract EnergyTrading {
    // Structure to store energy trade information
    struct EnergyTrade {
        address seller;
        address buyer;
        uint256 energyAmount; // in Wh (watt-hours)
        uint256 price; // price per kWh in wei
        uint256 timestamp;
        bool fulfilled;
    }
    
    // Array to store all energy trades
    EnergyTrade[] public trades;
    
    // Mapping to track user balances (in wei)
    mapping(address => uint256) public balances;
    
    // Events for front-end updates
    event TradeCreated(uint256 indexed tradeId, address seller, uint256 energyAmount, uint256 price);
    event TradeFulfilled(uint256 indexed tradeId, address buyer, address seller, uint256 energyAmount, uint256 totalPrice);
    event BalanceDeposited(address user, uint256 amount);
    event BalanceWithdrawn(address user, uint256 amount);
    
    /**
     * @dev Create a new energy sell order
     * @param _energyAmount Amount of energy to sell in Wh
     * @param _pricePerKWh Price per kWh in wei
     */
    function createTrade(uint256 _energyAmount, uint256 _pricePerKWh) public returns (uint256) {
        uint256 tradeId = trades.length;
        
        trades.push(EnergyTrade({
            seller: msg.sender,
            buyer: address(0), // No buyer yet
            energyAmount: _energyAmount,
            price: _pricePerKWh,
            timestamp: block.timestamp,
            fulfilled: false
        }));
        
        emit TradeCreated(tradeId, msg.sender, _energyAmount, _pricePerKWh);
        return tradeId;
    }
    
    /**
     * @dev Fulfill an existing energy trade (buy energy)
     * @param _tradeId ID of the trade to fulfill
     */
    function fulfillTrade(uint256 _tradeId) public payable {
        require(_tradeId < trades.length, "Trade does not exist");
        EnergyTrade storage trade = trades[_tradeId];
        
        require(!trade.fulfilled, "Trade already fulfilled");
        require(trade.seller != msg.sender, "Cannot buy your own energy");
        
        // Calculate total price (convert Wh to kWh by dividing by 1000)
        uint256 totalPrice = (trade.energyAmount * trade.price) / 1000;
        require(msg.value >= totalPrice, "Insufficient payment");
        
        // Update trade information
        trade.buyer = msg.sender;
        trade.fulfilled = true;
        
        // Transfer payment to seller's balance
        balances[trade.seller] += totalPrice;
        
        // Refund excess payment
        if (msg.value > totalPrice) {
            payable(msg.sender).transfer(msg.value - totalPrice);
        }
        
        emit TradeFulfilled(_tradeId, msg.sender, trade.seller, trade.energyAmount, totalPrice);
    }
    
    /**
     * @dev Deposit funds to user's balance
     */
    function deposit() public payable {
        balances[msg.sender] += msg.value;
        emit BalanceDeposited(msg.sender, msg.value);
    }
    
    /**
     * @dev Withdraw funds from user's balance
     * @param _amount Amount to withdraw
     */
    function withdraw(uint256 _amount) public {
        require(balances[msg.sender] >= _amount, "Insufficient balance");
        
        balances[msg.sender] -= _amount;
        payable(msg.sender).transfer(_amount);
        
        emit BalanceWithdrawn(msg.sender, _amount);
    }
    
    /**
     * @dev Get all active (unfulfilled) trades
     * @return Array of trade IDs
     */
    function getActiveTrades() public view returns (uint256[] memory) {
        // First, count active trades
        uint256 activeCount = 0;
        for (uint256 i = 0; i < trades.length; i++) {
            if (!trades[i].fulfilled) {
                activeCount++;
            }
        }
        
        // Then populate array of active trade IDs
        uint256[] memory activeTrades = new uint256[](activeCount);
        uint256 currentIndex = 0;
        
        for (uint256 i = 0; i < trades.length; i++) {
            if (!trades[i].fulfilled) {
                activeTrades[currentIndex] = i;
                currentIndex++;
            }
        }
        
        return activeTrades;
    }
    
    /**
     * @dev Get details of a specific trade
     */
    function getTradeDetails(uint256 _tradeId) public view returns (
        address seller,
        address buyer,
        uint256 energyAmount,
        uint256 price,
        uint256 timestamp,
        bool fulfilled
    ) {
        require(_tradeId < trades.length, "Trade does not exist");
        EnergyTrade storage trade = trades[_tradeId];
        
        return (
            trade.seller,
            trade.buyer,
            trade.energyAmount,
            trade.price,
            trade.timestamp,
            trade.fulfilled
        );
    }
    
    /**
     * @dev Get the total number of trades
     */
    function getTradeCount() public view returns (uint256) {
        return trades.length;
    }
}
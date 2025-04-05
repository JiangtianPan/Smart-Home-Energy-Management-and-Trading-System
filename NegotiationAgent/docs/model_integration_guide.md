# P2P Energy Trading Platform - Model Integration Guide

This document describes how to integrate mathematical models with the P2P trading platform.

## Available Model Interfaces

The platform provides the following interfaces for model integration:

### 1. Prediction Agent Interface
- `predict_energy_production(location, time_period)`: Predicts energy production
- `predict_energy_consumption(user_profile, time_period)`: Predicts energy consumption

### 2. Negotiation Agent Interface
- `get_optimal_price(order_type, market_data)`: Suggests optimal pricing

### 3. Behavioral Agent Interface
- `get_appliance_priority(user_id, appliances)`: Returns appliance priorities

### 4. Demand Response Agent Interface
- `get_demand_response_action(grid_status, user_profile)`: Suggests demand response actions

## Integration Steps

1. Implement your mathematical models as Python functions
2. Update the `model_interface.py` file to call your model functions
3. Test the integration using the provided API endpoints
4. Connect the frontend buttons to the API endpoints

## Backend Implementation

```python
# Example of integrating a pricing model
def my_pricing_model(order_type, market_data):
    # Implement your sophisticated pricing algorithm here
    # ...
    return optimal_price

# Then in model_interface.py:
def get_optimal_price(self, order_type, market_data):
    # Call your model instead of returning sample data
    return my_pricing_model(order_type, market_data)
```

## Frontend Integration

The frontend includes dedicated entry points for each model interface in the Smart Trading Assistant section. To connect these to your backend models:

### 1. Enable the Buttons

First, remove the `disabled` attribute and "Coming Soon" badges from the buttons in `index.html`:

```html
<!-- Before: -->
<button class="btn btn-sm btn-outline-primary" id="predictProductionBtn" disabled>
    <span class="badge bg-info">Coming Soon</span>
    Predict Production
</button>

<!-- After: -->
<button class="btn btn-sm btn-outline-primary" id="predictProductionBtn">
    Predict Production
</button>
```

### 2. Add Event Listeners

Add event listeners for each button in the JavaScript section:

```javascript
// Add these event listeners in the DOMContentLoaded function
document.getElementById('predictProductionBtn').addEventListener('click', predictProduction);
document.getElementById('predictConsumptionBtn').addEventListener('click', predictConsumption);
document.getElementById('optimalPriceBtn').addEventListener('click', getOptimalPrice);
document.getElementById('demandResponseBtn').addEventListener('click', checkDemandResponse);

// Implementation of the handler functions
function predictProduction() {
    // Get user location or use default
    const location = { latitude: 34.05, longitude: -118.25 }; // Example coordinates
    const timePeriod = { start: new Date(), duration: '24h' };
    
    fetch('/api/predict_production', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ location, time_period: timePeriod })
    })
    .then(response => response.json())
    .then(data => {
        // Display the prediction results
        alert(`Predicted production: ${data.prediction} kWh`);
        // You could also display this in a modal or dedicated UI element
    })
    .catch(error => {
        console.error('Error predicting production:', error);
        alert('Error predicting production');
    });
}

// Implement similar functions for the other buttons
```

### 3. Create API Endpoints

Make sure your backend has the corresponding API endpoints:

```python
# In your Flask/FastAPI app
@app.route('/api/predict_production', methods=['POST'])
def api_predict_production():
    data = request.json
    location = data.get('location')
    time_period = data.get('time_period')
    
    # Call your model interface
    prediction = model_interface.predict_energy_production(location, time_period)
    
    return jsonify({'prediction': prediction})

# Implement similar endpoints for the other model interfaces
```

## Creating Model Result Displays

To properly display model results, you should add UI components. For example, for production prediction:

```html
<!-- Add this to index.html -->
<div class="modal fade" id="productionPredictionModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Production Prediction</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
        <div id="productionPredictionResults">
          <!-- Results will be displayed here -->
        </div>
      </div>
    </div>
  </div>
</div>
```

Then update your JavaScript to display results in the modal:

```javascript
function predictProduction() {
    // ... fetch code from above ...
    .then(data => {
        // Create a visualization of the prediction
        const resultsDiv = document.getElementById('productionPredictionResults');
        resultsDiv.innerHTML = `
            <h6>Predicted Energy Production</h6>
            <p>Total: <strong>${data.prediction} kWh</strong></p>
            <div class="progress">
                <div class="progress-bar bg-success" style="width: ${data.prediction / 10}%"></div>
            </div>
            <p class="mt-3">Prediction is based on your location and weather forecast.</p>
        `;
        
        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('productionPredictionModal'));
        modal.show();
    })
    // ... catch error ...
}
```

## Testing Your Integration

1. Implement a simple model for testing
2. Connect the frontend buttons to your API endpoints
3. Test each feature individually
4. Verify that data flows correctly from frontend to model and back

## Deployment Considerations

When deploying your integrated system:

1. Ensure your models are optimized for production performance
2. Consider adding caching for expensive model predictions
3. Implement proper error handling for model failures
4. Add monitoring to track model performance and usage

---

This integration guide provides the foundation for connecting sophisticated mathematical models to your P2P Energy Trading platform, enabling AI-driven decision support for users.
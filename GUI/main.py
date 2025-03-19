import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import requests
from datetime import datetime
import random
from fastapi import FastAPI
import uvicorn
import multiprocessing

# ==================== FastAPI Backend ====================
def run_fastapi():
    api = FastAPI()

    # Simulated data storage
    class DataStore:
        def __init__(self):
            self.energy_data = {
                "solar": [3.5, 3.7, 4.0],
                "wind": [2.0, 2.1, 1.9],  # Wind production data
                "grid": [0.5, -0.3, 0.2],  # Grid input data (positive=import, negative=export)
                "consumption": [2.8, 3.0, 3.2],
                "timestamps": [datetime.now().isoformat() for _ in range(3)]
            }
            self.trades = []
            self.weather = {
                "temperature": 23.5,
                "humidity": 65,
                "wind_speed": 12,
                "condition": "sunny",
                "icon": "wi-day-sunny"
            }

    data_store = DataStore()

    @api.get("/api/energy/current")
    def get_current_energy():
        # Simulate data updates
        new_solar = max(0, data_store.energy_data["solar"][-1] + random.uniform(-0.5, 0.5))
        new_wind = max(0, random.uniform(1.0, 3.0))  # Simulate wind production
        new_grid = random.uniform(-2.0, 2.0)         # Simulate grid input
        data_store.energy_data["solar"].append(new_solar)
        data_store.energy_data["wind"].append(new_wind)
        data_store.energy_data["grid"].append(new_grid)
        data_store.energy_data["consumption"].append(random.uniform(2.5, 3.5))
        data_store.energy_data["timestamps"].append(datetime.now().isoformat())
        return data_store.energy_data

    @api.get("/api/trading-power")
    def get_trading_power():
        # Simulate trading power data (positive=selling, negative=buying)
        trading_power = {
            "monthly_total": random.uniform(-100, 100),  # Random between -100 and 100 kWh
            "timestamp": datetime.now().isoformat()
        }
        return trading_power

    @api.get("/api/trades")
    def get_active_trades():
        return {"trades": data_store.trades}

    @api.post("/api/trades")
    def create_trade(trade: dict):
        data_store.trades.append(trade)
        return {"status": "success"}

    @api.get("/api/weather")
    def get_weather():
        # Simulate weather changes
        data_store.weather["temperature"] += random.uniform(-0.5, 0.5)
        data_store.weather["humidity"] = random.randint(60, 80)
        data_store.weather["wind_speed"] = random.randint(5, 15)
        return data_store.weather

    uvicorn.run(api, host="0.0.0.0", port=8000)

# ==================== Dash Frontend ====================
def run_dash():
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            "https://cdnjs.cloudflare.com/ajax/libs/weather-icons/2.0.12/css/weather-icons.min.css"
        ]
    )
    server = app.server

    API_BASE = "http://localhost:8000/api"

    # ======== Components ========
    def navbar():
        return dbc.NavbarSimple(
            children=[
                dbc.NavItem(dbc.NavLink("Dashboard", href="#")),
                dbc.NavItem(dbc.NavLink("Trading", href="#")),
                dbc.NavItem(dbc.NavLink("Appliances", href="#")),
                dbc.NavItem(dbc.NavLink("Settings", href="#")),
            ],
            brand="Smart Home Energy Management and Trading System Dashboard",
            color="primary",
            dark=True,
        )

    def weather_card():
        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Span("Current Weather", className="me-2"),
                        html.I(id="weather-icon", className="wi wi-day-sunny")
                    ],
                    className="d-flex align-items-center"
                ),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H2("--°C", id="weather-temp", className="mb-0"),
                                        html.Small("Feels like --°C", id="weather-feels-like", className="text-muted")
                                    ],
                                    width=10
                                ),
                                dbc.Col(
                                    [
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div("💧", style={'fontSize': '2rem'}),
                                                        html.Div("--%", id="weather-humidity")
                                                    ]
                                                ),
                                                dbc.Col([
                                                    html.Div(
                                                        html.Img(
                                                            src="/assets/windpng.png",
                                                            style={"width": "45px"}
                                                        )
                                                    ),
                                                    html.Div("-- m/s", id="weather-wind")
                                                ])
                                            ]
                                        )
                                    ],
                                    width=10
                                )
                            ]
                        ),
                        html.Hr(),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Small("Condition", className="text-muted"),
                                        html.Div(
                                            [
                                                html.Span("--", id="weather-condition"),
                                                html.I(id="weather-condition-icon", style={'margin-left': '5px'})
                                            ],
                                            className="d-flex align-items-center"
                                        )
                                    ],
                                    width=10
                                )
                            ]
                        )
                    ]
                )
            ],
            # Only set width=100% so the card won't exceed its column
            style={'width': '100%'}
        )

    def energy_gauge(title, value, max_value):
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=value,
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={'axis': {'range': [0, max_value]}},
                number={'font': {'size': 24}}
            )
        )
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))

        return dbc.Card(
            [
                dbc.CardHeader(title),
                dbc.CardBody(
                    dcc.Graph(
                        figure=fig,
                        config={'displayModeBar': False},
                        style={'height': '220px','width': '180px'}
                    )
                )
            ],
            style={'width': '100%'}
        )

    def trading_power_card():
        return dbc.Card(
            [
                dbc.CardHeader("Trading Power with Neighborhood"),
                dbc.CardBody(
                    [
                        html.H4("-- kWh", id="trading-power-value", className="mb-0"),
                        html.Small("This Month", className="text-muted")
                    ]
                )
            ],
            style={'width': '100%'}
        )

    def monthly_energy_card():
        return dbc.Card(
            [
                dbc.CardHeader("Monthly Energy Consumption"),
                dbc.CardBody(
                    [
                        html.H4("-- KWh", id="monthly-energy", className="mb-0"),
                        html.Small("Total for this month", className="text-muted")
                    ]
                )
            ],
            style={'width': '100%'}
        )

    # ======== Real-Time Cards (7 columns, same width) ========
    def real_time_cards():
        """
        Single row containing 7 columns, each forced to 250px wide via Flexbox.
        className="flex-nowrap" ensures no wrapping, so horizontally scrollable if needed.
        """
        col_style = {
            'flex': '0 0 250px',  # fixed at 250px
            'maxWidth': '250px',
            'minWidth': '250px'
        }

        return dbc.Row(
            [
                dbc.Col(weather_card(), className="d-flex", style=col_style),
                dbc.Col(html.Div(id="solar-gauge"), className="d-flex", style=col_style),
                dbc.Col(html.Div(id="wind-gauge"), className="d-flex", style=col_style),
                dbc.Col(html.Div(id="battery-gauge"), className="d-flex", style=col_style),
                dbc.Col(html.Div(id="grid-gauge"), className="d-flex", style=col_style),
                dbc.Col(trading_power_card(), className="d-flex", style=col_style),
                dbc.Col(monthly_energy_card(), className="d-flex", style=col_style),
            ],
            className="mb-4 flex-nowrap",
            style={
                'height': '100%',
                'overflowX': 'auto'
            }
        )

    def energy_charts():
        return html.Div(
            [
                dcc.Graph(id="energy-overview"),
                dcc.Interval(id="update-interval", interval=5*1000)  # updates every 5 seconds
            ]
        )

    def trading_table():
        return dash_table.DataTable(
            id='trades-table',
            columns=[
                {'name': 'Time', 'id': 'timestamp'},
                {'name': 'Price (kWh)', 'id': 'price'},
                {'name': 'Energy (kWh)', 'id': 'energy'},
                {'name': 'Status', 'id': 'status'}
            ],
            data=[],  # Initialize with empty data
            style_cell={'textAlign': 'center'},
            style_header={'fontWeight': 'bold'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{status} = "Pending"'},
                    'backgroundColor': '#fff3cd',
                    'color': '#856404'
                }
            ]
        )

    # ======== Layout ========
    app.layout = html.Div(
        [
            navbar(),
            dbc.Container(
                [
                    html.Div(id="alerts"),
                    html.Div(
                        [
                            # Dashboard Tab
                            html.Div(
                                [
                                    real_time_cards(),
                                    energy_charts()
                                ],
                                id="dashboard-tab"
                            ),

                            # Trading Tab
                            html.Div(
                                [
                                    html.H3("Energy Trading", className="mt-4"),
                                    trading_table(),
                                    dbc.Button("Refresh Trades", id="refresh-trades", className="mt-2")
                                ],
                                id="trading-tab",
                                style={'display': 'none'}
                            ),

                            # Settings Tab
                            html.Div(
                                [
                                    html.H3("User Preferences", className="mt-4"),
                                    dbc.Form(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Trading Strategy"),
                                                            dcc.Dropdown(
                                                                id="strategy-select",
                                                                options=[
                                                                    {'label': 'Aggressive', 'value': 'aggressive'},
                                                                    {'label': 'Conservative', 'value': 'conservative'}
                                                                ],
                                                                value='conservative'
                                                            )
                                                        ],
                                                        width=6
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Peak Hours Avoidance"),
                                                            dbc.Input(
                                                                id="peak-time-start",
                                                                type="time",
                                                                value="09:00",  # Default value
                                                                style={'margin-left': '10px'}
                                                            )
                                                        ],
                                                        width=6
                                                    )
                                                ]
                                            )
                                        ]
                                    )
                                ],
                                id="settings-tab",
                                style={'display': 'none'}
                            )
                        ]
                    )
                ],
                fluid=True
            )
        ]
    )

    # ======== Callbacks ========
    @app.callback(
        [
            Output('energy-overview', 'figure'),
            Output('solar-gauge', 'children'),
            Output('wind-gauge', 'children'),
            Output('battery-gauge', 'children'),
            Output('grid-gauge', 'children')
        ],
        [Input('update-interval', 'n_intervals')]
    )
    def update_energy_data(n):
        try:
            response = requests.get(f"{API_BASE}/energy/current")
            data = response.json()

            # Build line chart
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=data['timestamps'][-60:],
                    y=data['solar'][-60:],
                    name='Solar Production(Kw)',
                    line=dict(color='green')
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=data['timestamps'][-60:],
                    y=data['wind'][-60:],
                    name='Wind Production(Kw)',
                    line=dict(color='orange')
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=data['timestamps'][-60:],
                    y=data['grid'][-60:],
                    name='Grid Import(Kw)',
                    line=dict(color='red')
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=data['timestamps'][-60:],
                    y=data['consumption'][-60:],
                    name='Consumption(Kw)',
                    line=dict(color='blue')
                )
            )
            fig.update_layout(
                title="History and Forecast of Energy Production and Consumption (Last 60 Minutes)",
                showlegend=True,
                xaxis_title="Time",
                yaxis_title="kW",
                legend=dict(x=0, y=1.1, orientation='h')
            )

            # Create updated gauges
            solar_gauge_card = energy_gauge(
                title=html.Div(
                    [
                        html.Img(
                            src=" ",
                            style={"justifyContent": "center","height": "20px", "marginRight": "8px"}
                        ),
                        "Solar Production (Kw)"
                    ]
                ),
                value=data['solar'][-1],
                max_value=10
            )
            wind_gauge_card = energy_gauge(
                title=html.Div(
                    [
                        html.Img(
                            src=" ",
                            style={"justifyContent": "center","height": "20px", "marginRight": "8px"}
                        ),
                        "Wind Production (Kw)"
                    ]
                ),
                value=data['wind'][-1],
                max_value=10
            )
            battery_gauge_card = energy_gauge(
                title=html.Div(
                    [
                        html.Img(
                            src=" ",
                            style={"justifyContent": "center","height": "20px", "marginRight": "8px"}
                        ),
                        "   Battery Level (%)"
                    ]
                ),
                value=65,  # Example static value
                max_value=100
            )
            grid_gauge_card = energy_gauge(
                title=html.Div(
                    [
                        html.Img(
                            src=" ",
                            style={"justifyContent": "center","height": "20px", "marginRight": "8px"}
                        ),
                        "   Grid Import (Kw)"
                    ]
                ),
                value=data['grid'][-1],
                max_value=5
            )

            return (
                fig,
                solar_gauge_card,
                wind_gauge_card,
                battery_gauge_card,
                grid_gauge_card
            )
        except Exception:
            return go.Figure(), "Error", "Error", "Error", "Error"

    @app.callback(
        Output('trading-power-value', 'children'),
        [Input('update-interval', 'n_intervals')]
    )
    def update_trading_power(n):
        try:
            response = requests.get(f"{API_BASE}/trading-power")
            data = response.json()
            trading_power = data['monthly_total']
            return f"{trading_power:.1f} kWh"
        except:
            return "-- kWh"

    @app.callback(
        Output('monthly-energy', 'children'),
        [Input('update-interval', 'n_intervals')]
    )
    def update_monthly_energy(n):
        try:
            # Simulate monthly energy data
            monthly_energy = random.uniform(30, 50)  # Random between 30 and 50 MWh
            return f"{monthly_energy:.1f} kWh"
        except:
            return "-- kWh"

    @app.callback(
        [
            Output('weather-temp', 'children'),
            Output('weather-feels-like', 'children'),
            Output('weather-humidity', 'children'),
            Output('weather-wind', 'children'),
            Output('weather-condition', 'children'),
            Output('weather-condition-icon', 'className')
        ],
        [Input('update-interval', 'n_intervals')]
    )
    def update_weather(n):
        try:
            response = requests.get(f"{API_BASE}/weather")
            data = response.json()
            temp = f"{data['temperature']:.1f}°C"
            feels_like = f"Feels like {data['temperature'] + random.uniform(-2, 2):.1f}°C"
            humidity = f"{data['humidity']}%"
            wind = f"{data['wind_speed']} m/s"
            condition = data['condition'].capitalize()
            icon_class = f"wi {data['icon']}"
            return temp, feels_like, humidity, wind, condition, icon_class
        except:
            return "--°C", "Feels like --°C", "--%", "-- m/s", "N/A", "wi wi-na"

    # Run the Dash server
    app.run_server(port=8050)

# ==================== Main: Run Both ====================
if __name__ == '__main__':
    api_process = multiprocessing.Process(target=run_fastapi)
    dash_process = multiprocessing.Process(target=run_dash)

    api_process.start()
    dash_process.start()

    api_process.join()
    dash_process.join()

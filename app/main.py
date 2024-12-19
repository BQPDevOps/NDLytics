from nicegui import ui, app
from config import config
from utils import permission_required
from modules.session_manager import SessionManager

from pages import *

import tracemalloc

tracemalloc.start()


@ui.page("/")
@permission_required("dashboard_view")
def root():
    ui.navigate.to("/signin")


@ui.page("/signin")
def root_signing():
    signin_page()


@ui.page("/dashboard")
@permission_required("dashboard_view")
def root_dashboard():
    """Dashboard page route handler"""
    session_manager = SessionManager()
    return dashboard_page(session_manager)


@ui.page("/campaigns")
@permission_required("dashboard_view")
def root_campaigns():
    session_manager = SessionManager()
    return campaigns_page(session_manager)


@ui.page("/tasks")
@permission_required("dashboard_view")
def root_tasks():
    session_manager = SessionManager()
    return tasks_page(session_manager)


@ui.page("/goals")
@permission_required("dashboard_view")
def root_goals():
    session_manager = SessionManager()
    return goals_page(session_manager)


@ui.page("/settings")
@permission_required("dashboard_view")
def root_settings():
    session_manager = SessionManager()
    return settings_page(session_manager)


@ui.page("/unauthorized")
def root_unauthorized():
    unauthorized_page()


app.add_static_files("/static", "static")

"""
    Provided within the project files are all of the main components and services used in the application.
    The main.py file is the entry point for the application. It is responsible for setting up the application and running the server.
    The nicegui library is used to create the UI and handle the routing for the application.
    The nicegui library is a wrapper around the quart library and is used to create the UI and handle the routing for the application.
    The Cognito middleware is used to handle the authentication and authorization for the application.
    The Dynamo middleware is used to handle the database for the application.
    The S3 middleware is used to handle the file storage for the application.
    The SessionManager is used to handle the session for the application.
    The StandardPage is used to handle the page for the application as a base class for all pages.
    The DashboardPage is used to handle the dashboard page for the application.
    The DashboardPage needs to be display analytical data extrapolated from the .csv files outlined in the project files.
    Using the MTDCollected widget as a starting point, create widgets to display the following analytical data:
    - Total Collected MTD
    - Total Collected YTD
    - Total Collected Last 12 Months
    - Total Collected Last 12 Months (Rolling)
    - Total Collected Last 12 Months (Rolling) by Month
    - Total Collected Last 12 Months (Rolling) by Day
    - Total Collected Last 12 Months (Rolling) by Week
    - Total Collected Last 12 Months (Rolling) by Year
    - Calendar Heatmap of Collected Amount by Day of Month
    - Calendar Heatmap of Collected Amount by Day of Week
    - Calendar Heatmap of Collected Amount by Day of Year
    - Payment Type Breakdown of Collected Amount by Month
    - Payment Type Breakdown of Collected Amount by Day of Month
    - Payment Type Breakdown of Collected Amount by Day of Week
    - Payment Type Breakdown of Collected Amount by Day of Year
    - Payment Type Breakdown of Collected Amount YTD
    - Payment Type Breakdown of Collected Amount Last 12 Months
    - Payment Type Breakdown of Collected Amount Last 12 Months (Rolling)
    - Client Breakdown of Collected Amount by Month
    - Client Breakdown of Collected Amount by Day of Month
    - Client Breakdown of Collected Amount by Day of Week
    - Client Breakdown of Collected Amount by Day of Year
    - Client Breakdown of Collected Amount YTD
    - Client Breakdown of Collected Amount Last 12 Months
    - Client Breakdown of Collected Amount Last 12 Months (Rolling)
    - Call Outcome Analysis
    - Growth Metrics
    - Operator Performance Analysis
    - Call Duration Analysis
    - Call Type Analysis
    - Caller Analysis
    - Caller Type Analysis
    - Caller Behavior Analysis
    - Sentiment Analysis
    - Agent Performance Analysis
    - Agent Utilization Analysis
    - Agent Satisfaction Analysis
    - Agent Productivity Analysis
    - Agent Sentiment Analysis
    - Agent Caller Analysis
    - Agent Caller Type Analysis
    - Agent Caller Behavior Analysis
    - LSTM Forecast of Collected Amount
    - ARIMA Forecast of Collected Amount
    - Prophet Forecast of Collected Amount
    - Time Series Decomposition of Collected Amount
    - Seasonal Decomposition of Collected Amount
    - Trend Analysis of Collected Amount
    - Seasonal Analysis of Collected Amount
    - Holiday Analysis of Collected Amount
    - Anomaly Detection of Collected Amount
    - Anomaly Detection of Collected Amount by Month
    - Anomaly Detection of Collected Amount by Day of Month
    - Anomaly Detection of Collected Amount by Day of Week
    - Anomaly Detection of Collected Amount by Day of Year
    - Anomaly Detection of Collected Amount by Payment Type
    - Anomaly Detection of Collected Amount by Client
    - Anomaly Detection of Collected Amount by Caller
    - Anomaly Detection of Collected Amount by Caller Type
    - Anomaly Detection of Collected Amount by Caller Behavior
    - Anomaly Detection of Collected Amount by Sentiment
    - Anomaly Detection of Collected Amount by Agent
    - Anomaly Detection of Collected Amount by Agent Performance
    - Anomaly Detection of Collected Amount by Agent Utilization
    - Anomaly Detection of Collected Amount by Agent Satisfaction
    - Anomaly Detection of Collected Amount by Agent Productivity
    - Anomaly Detection of Collected Amount by Agent Sentiment
    - Anomaly Detection of Collected Amount by Agent Caller
    - Anomaly Detection of Collected Amount by Agent Caller Type
    - Anomaly Detection of Collected Amount by Agent Caller Behavior
    - Anomaly Detection of Collected Amount by Agent Sentiment
    - Anomaly Detection of Collected Amount by Agent Caller
    - Anomaly Detection of Collected Amount by Agent Caller Type
    - Anomaly Detection of Collected Amount by Agent Caller Behavior
    - XGBoost Forecast of Collected Amount
    - LightGBM Forecast of Collected Amount
    - CatBoost Forecast of Collected Amount
    - Random Forest Forecast of Collected Amount
    - Gradient Boosting Forecast of Collected Amount
    - AdaBoost Forecast of Collected Amount
    - Extra Trees Forecast of Collected Amount
    - Calling Strategy Simulation
    - Calling Strategy Optimization
    - Calling Strategy Analysis
    - Calling Strategy Comparison
    - Calling Strategy Performance
    - Calling Strategy Recommendations
    - Calling Strategy Recommendations by Month
    - Calling Strategy Recommendations by Day of Month
    - Calling Strategy Recommendations by Day of Week
    - Calling Strategy Recommendations by Day of Year
    - Calling Strategy Recommendations by Payment Type
    - Calling Strategy Recommendations by Client
    - Calling Strategy Recommendations by Caller
    - Calling Strategy Recommendations by Caller Type
    - Calling Strategy Recommendations by Caller Behavior
    - Zip Code Analysis
    - Visualization of Caller Behavior
    - Visualization of Agent Performance
    - Visualization of Agent Utilization
    - Visualization of Agent Satisfaction
    - Visualization of Agent Productivity
    - Visualization of Agent Sentiment
    - Visualization of Agent Caller
    - Visualization of Agent Caller Type
    - Visualization of Agent Caller Behavior
    - Visualization of Sentiment
    - Visualization of Call Types
    - Visualization of Call Outcomes
    - Visualization of Call Durations
    - Genetic Algorithm Optimization of Calling Strategy
    - Simulated Annealing Optimization of Calling Strategy
    - Tabu Search Optimization of Calling Strategy
    - Particle Swarm Optimization of Calling Strategy
    - Ant Colony Optimization of Calling Strategy
    - Differential Evolution Optimization of Calling Strategy
    - CMA-ES Optimization of Calling Strategy
    - DEAP Optimization of Calling Strategy
    - Evolutionary Strategy Optimization of Calling Strategy
    - Evolutionary Programming Optimization of Calling Strategy
    - Harmony Search Optimization of Calling Strategy
    - Firefly Algorithm Optimization of Calling Strategy
    - Glowworm Swarm Optimization of Calling Strategy
    - Artificial Bee Colony Optimization of Calling Strategy
    - Teaching Learning Based Optimization of Calling Strategy
    - Imperialist Competitive Algorithm Optimization of Calling Strategy
    - Cultural Algorithm Optimization of Calling Strategy
    """

ui.run(
    storage_secret=config.app_storage_secret,
    title="NDLytics",
    port=8000,
    host="0.0.0.0",
)

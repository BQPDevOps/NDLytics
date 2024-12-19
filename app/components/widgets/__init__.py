from .CallAnalytics import create_call_analytics_widget
from .CollectionEffectiveness import create_collection_effectiveness_widget
from .PortfolioPerformance import create_portfolio_performance_widget
from .CollectionInsights import create_collection_insights_widget
from .WidgetFramework import WidgetFramework

# from .RiskScoring import create_risk_scoring_widget

__all__ = [
    "create_call_analytics_widget",
    "create_collection_effectiveness_widget",
    "create_portfolio_performance_widget",
    "create_collection_insights_widget",
    "WidgetFramework",
    # "create_risk_scoring_widget",
]

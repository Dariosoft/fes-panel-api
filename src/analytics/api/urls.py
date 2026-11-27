from django.urls import path

from analytics.api.views import PanelAnalyticsMetricsView, PanelAnalyticsTimelineView

urlpatterns = [
    path(
        "timeline",
        PanelAnalyticsTimelineView.as_view(),
        name="panel-analytics-timeline",
    ),
    path(
        "metrics",
        PanelAnalyticsMetricsView.as_view(),
        name="panel-analytics-metrics",
    ),
]

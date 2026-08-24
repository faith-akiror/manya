from django.urls import path

from apps.legal.views import (
    CategoryDetailAPIView,
    CategoryListAPIView,
    TopicDetailAPIView,
    TopicListAPIView,
    TopicSearchAPIView,
)

urlpatterns = [
    path("categories/", CategoryListAPIView.as_view(), name="legal-category-list"),
    path(
        "categories/<slug:slug>/",
        CategoryDetailAPIView.as_view(),
        name="legal-category-detail",
    ),
    path("topics/", TopicListAPIView.as_view(), name="legal-topic-list"),
    path(
        "topics/<slug:slug>/", TopicDetailAPIView.as_view(), name="legal-topic-detail"
    ),
    path("search/", TopicSearchAPIView.as_view(), name="legal-search"),
]

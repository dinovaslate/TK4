from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (
    BookingCreateView,
    CatalogView,
    HomeView,
    LandingView,
    ProfileView,
    RagaLoginView,
    RegisterView,
    ReviewCreateView,
    VenueDetailView,
    WishlistToggleView,
    WishlistView,
)

urlpatterns = [
    path("", LandingView.as_view(), name="landing"),
    path("login/", RagaLoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("home/", HomeView.as_view(), name="home"),
    path("catalog/", CatalogView.as_view(), name="catalog"),
    path("wishlist/", WishlistView.as_view(), name="wishlist"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("venues/<slug:slug>/", VenueDetailView.as_view(), name="venue_detail"),
    path("venues/<slug:slug>/toggle-wishlist/", WishlistToggleView.as_view(), name="toggle_wishlist"),
    path("venues/<slug:slug>/book/", BookingCreateView.as_view(), name="book_venue"),
    path("venues/<slug:slug>/review/", ReviewCreateView.as_view(), name="add_review"),
]

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, FormView, TemplateView

from .forms import BookingForm, LoginForm, RegistrationForm, ReviewForm, VenueFilterForm
from .models import Booking, Review, Venue, WishlistItem


class RagaLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, "Welcome back! Time to secure your next matchday.")
        return super().form_valid(form)


class RegisterView(FormView):
    form_class = RegistrationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Account created successfully. Let's find your perfect pitch!")
        return super().form_valid(form)


class LandingView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return redirect("login")


class VenueListBaseView(LoginRequiredMixin, TemplateView):
    template_name = "main/home.html"

    def get_filter_form(self):
        return VenueFilterForm(self.request.GET or None)

    def get_queryset(self):
        queryset = Venue.objects.prefetch_related("amenities").annotate(bookings_count=Count("bookings"))
        form = self.get_filter_form()
        if form.is_valid():
            q = form.cleaned_data.get("q")
            city = form.cleaned_data.get("city")
            category = form.cleaned_data.get("category")
            max_price = form.cleaned_data.get("max_price")
            if q:
                queryset = queryset.filter(name__icontains=q)
            if city:
                queryset = queryset.filter(city__iexact=city)
            if category:
                queryset = queryset.filter(category__slug=category)
            if max_price:
                queryset = queryset.filter(price_per_hour__lte=max_price)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter_form = self.get_filter_form()
        context["filter_form"] = filter_form
        context["venues"] = self.get_queryset()
        wishlist_ids = set(
            WishlistItem.objects.filter(user=self.request.user).values_list("venue_id", flat=True)
        )
        context["wishlist_ids"] = wishlist_ids
        context["has_filters"] = any(
            value for key, value in filter_form.cleaned_data.items() if key != "q"
        ) if filter_form.is_bound and filter_form.is_valid() else False
        return context


class HomeView(VenueListBaseView):
    template_name = "main/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_venues"] = context["venues"].order_by("-bookings_count", "name")[:3]
        return context


class CatalogView(VenueListBaseView):
    template_name = "main/catalog.html"


class VenueDetailView(LoginRequiredMixin, DetailView):
    model = Venue
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "main/venue_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venue = self.object
        context["booking_form"] = BookingForm(venue, self.request.POST or None)
        context["review_form"] = ReviewForm(self.request.POST or None)
        context["wishlist_ids"] = set(
            WishlistItem.objects.filter(user=self.request.user).values_list("venue_id", flat=True)
        )
        context["upcoming_bookings"] = venue.bookings.filter(date__gte=timezone.now().date()).order_by("date")[:5]
        return context


class WishlistToggleView(LoginRequiredMixin, View):
    def post(self, request, slug):
        venue = get_object_or_404(Venue, slug=slug)
        wishlist_item, created = WishlistItem.objects.get_or_create(user=request.user, venue=venue)
        if not created:
            wishlist_item.delete()
            messages.info(request, f"Removed {venue.name} from your wishlist.")
        else:
            messages.success(request, f"Saved {venue.name} to your wishlist.")
        return redirect(request.POST.get("next", venue.get_absolute_url()))


class WishlistView(LoginRequiredMixin, TemplateView):
    template_name = "main/wishlist.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items = (
            WishlistItem.objects.filter(user=self.request.user)
            .select_related("venue", "venue__category")
            .prefetch_related("venue__amenities")
            .order_by("-created_at")
        )
        context["items"] = items
        return context


class BookingCreateView(LoginRequiredMixin, View):
    def post(self, request, slug):
        venue = get_object_or_404(Venue, slug=slug)
        form = BookingForm(venue, request.POST)
        if not form.is_valid():
            messages.error(request, "Please correct the highlighted errors before booking.")
            context = {
                "object": venue,
                "booking_form": form,
                "review_form": ReviewForm(),
                "wishlist_ids": set(
                    WishlistItem.objects.filter(user=request.user).values_list("venue_id", flat=True)
                ),
                "upcoming_bookings": venue.bookings.filter(date__gte=timezone.now().date()).order_by("date")[:5],
            }
            return render(request, "main/venue_detail.html", context)
        booking: Booking = form.save(commit=False)
        booking.user = request.user
        booking.venue = venue
        booking.save()
        form.save_m2m()
        messages.success(
            request,
            "Booking received! We'll confirm availability shortly and notify you via email.",
        )
        return redirect("profile")


class ReviewCreateView(LoginRequiredMixin, View):
    def post(self, request, slug):
        venue = get_object_or_404(Venue, slug=slug)
        form = ReviewForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Unable to save your review. Please check the form and try again.")
            context = {
                "object": venue,
                "booking_form": BookingForm(venue),
                "review_form": form,
                "wishlist_ids": set(
                    WishlistItem.objects.filter(user=request.user).values_list("venue_id", flat=True)
                ),
                "upcoming_bookings": venue.bookings.filter(date__gte=timezone.now().date()).order_by("date")[:5],
            }
            return render(request, "main/venue_detail.html", context)
        Review.objects.update_or_create(
            user=request.user,
            venue=venue,
            defaults={
                "rating": form.cleaned_data["rating"],
                "comment": form.cleaned_data["comment"],
            },
        )
        messages.success(request, "Thank you for sharing your experience!")
        return redirect(venue.get_absolute_url())


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "main/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["upcoming_bookings"] = (
            self.request.user.bookings.filter(date__gte=timezone.now().date())
            .select_related("venue")
            .order_by("date", "start_time")
        )
        context["past_bookings"] = (
            self.request.user.bookings.filter(date__lt=timezone.now().date())
            .select_related("venue")
            .order_by("-date")
        )
        context["wishlist_count"] = self.request.user.wishlist.count()
        context["review_count"] = self.request.user.reviews.count()
        return context

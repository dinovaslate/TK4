from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class VenueCategory(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Amenity(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    icon = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.name


class Venue(TimeStampedModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    city = models.CharField(max_length=80)
    address = models.CharField(max_length=255)
    category = models.ForeignKey(VenueCategory, on_delete=models.PROTECT, related_name="venues")
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.PositiveIntegerField(default=10)
    hero_image = models.URLField(help_text="Main hero image for the venue")
    description = models.TextField()
    highlights = models.TextField(blank=True, help_text="Comma separated bullet points")
    amenities = models.ManyToManyField(Amenity, related_name="venues", blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Venue.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("venue_detail", args=[self.slug])

    def highlight_items(self) -> list[str]:
        if not self.highlights:
            return []
        return [item.strip() for item in self.highlights.split(",") if item.strip()]

    def average_rating(self) -> Decimal | None:
        ratings = self.reviews.all().values_list("rating", flat=True)
        if not ratings:
            return None
        return sum(Decimal(rating) for rating in ratings) / Decimal(len(ratings))


class VenueImage(TimeStampedModel):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="gallery")
    image_url = models.URLField()
    alt_text = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ("pk",)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.venue.name} image"


class AddOn(TimeStampedModel):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="add_ons")
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=9, decimal_places=2)

    class Meta:
        ordering = ("name",)
        unique_together = ("venue", "name")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.venue.name})"


class WishlistItem(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist")
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="wishlisted_by")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "venue"), name="unique_wishlist_item"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.user} → {self.venue}"


class Booking(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Waiting for confirmation"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="bookings")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    add_ons = models.ManyToManyField(AddOn, related_name="bookings", blank=True)

    class Meta:
        ordering = ("-date", "start_time")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.venue.name} on {self.date}"

    @property
    def is_upcoming(self) -> bool:
        event_datetime = datetime.combine(self.date, self.start_time)
        if timezone.is_naive(event_datetime):
            event_datetime = timezone.make_aware(event_datetime, timezone.get_current_timezone())
        return event_datetime >= timezone.now()

    def total_price(self) -> Decimal:
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        duration = (end - start).total_seconds() / 3600
        duration_hours = Decimal(str(duration)).quantize(Decimal("0.01"))
        base_price = (self.venue.price_per_hour * duration_hours).quantize(Decimal("0.01"))
        add_on_total = sum((add_on.price for add_on in self.add_ons.all()), Decimal("0.00"))
        return base_price + add_on_total


class Review(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField()

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=("user", "venue"), name="unique_review_per_user"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.venue.name} review by {self.user}"

    def rating_stars(self) -> range:
        return range(self.rating)

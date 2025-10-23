from django.contrib import admin

from .models import AddOn, Amenity, Booking, Review, Venue, VenueCategory, VenueImage, WishlistItem


@admin.register(VenueCategory)
class VenueCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "created_at")


class VenueImageInline(admin.TabularInline):
    model = VenueImage
    extra = 1


class AddOnInline(admin.TabularInline):
    model = AddOn
    extra = 1


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "category", "price_per_hour", "capacity")
    search_fields = ("name", "city", "category__name")
    list_filter = ("category", "city")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [VenueImageInline, AddOnInline]
    filter_horizontal = ("amenities",)


@admin.register(VenueImage)
class VenueImageAdmin(admin.ModelAdmin):
    list_display = ("venue", "image_url", "created_at")


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("user", "venue", "created_at")
    search_fields = ("user__username", "venue__name")


class BookingAddOnInline(admin.TabularInline):
    model = Booking.add_ons.through
    extra = 1


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("venue", "user", "date", "start_time", "end_time", "status")
    list_filter = ("status", "venue", "date")
    search_fields = ("venue__name", "user__username")
    inlines = [BookingAddOnInline]
    exclude = ("add_ons",)


@admin.register(AddOn)
class AddOnAdmin(admin.ModelAdmin):
    list_display = ("name", "venue", "price")
    list_filter = ("venue",)
    search_fields = ("name", "venue__name")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("venue", "user", "rating", "created_at")
    list_filter = ("rating", "venue")
    search_fields = ("venue__name", "user__username", "comment")

from __future__ import annotations

from datetime import date, datetime

from datetime import date

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import AddOn, Booking, Review, Venue, VenueCategory


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Email",
                "autocomplete": "email",
            }
        ),
    )

    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "autocomplete": "current-password",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "style",
                "background:transparent; border:0; color:#eaf5ff; font-size:15px; width:100%;",
            )


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "placeholder": "First Name",
                "autocomplete": "given-name",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Last Name",
                "autocomplete": "family-name",
            }
        ),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Enter Your Email",
                "autocomplete": "email",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("username", None)
        self.fields["password1"].widget.attrs.update(
            {
                "placeholder": "Enter Your Password",
                "autocomplete": "new-password",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "placeholder": "Confirm Password",
                "autocomplete": "new-password",
            }
        )
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "style",
                "background:transparent; border:0; color:#eaf5ff; font-size:15px; width:100%;",
            )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email

    def save(self, commit: bool = True):
        user: User = super().save(commit=False)
        user.username = self.cleaned_data["email"].lower()
        user.email = self.cleaned_data["email"].lower()
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            user.save()
        return user


class VenueFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search venue name",
            }
        ),
        label="Search",
    )
    city = forms.ChoiceField(required=False, choices=[("", "All Cities")])
    category = forms.ChoiceField(required=False, choices=[("", "All Categories")])
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        label="Max Price",
        widget=forms.NumberInput(
            attrs={
                "placeholder": "Max Price",
                "step": "10000",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cities = Venue.objects.order_by("city").values_list("city", flat=True).distinct()
        city_choices = [("", "All Cities"), *[(city, city) for city in cities if city]]
        categories = VenueCategory.objects.order_by("name").values_list("slug", "name")
        category_choices = [("", "All Categories"), *list(categories)]
        self.fields["city"].choices = city_choices
        self.fields["category"].choices = category_choices
        for name in ("q", "city", "category", "max_price"):
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault(
                    "style",
                    "background:transparent; border:0; color:#EAFBF9; font-weight:600; width:100%;",
                )


class BookingForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "min": date.today().isoformat()}),
    )
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))
    add_ons = forms.ModelMultipleChoiceField(
        queryset=AddOn.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Booking
        fields = ("date", "start_time", "end_time", "notes", "add_ons")
        widgets = {
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Any special requests or match details",
                }
            )
        }

    def __init__(self, venue: Venue, *args, **kwargs):
        self.venue = venue
        super().__init__(*args, **kwargs)
        self.fields["add_ons"].queryset = venue.add_ons.all()
        self.fields["date"].widget.attrs["min"] = date.today().isoformat()
        for field_name in ("date", "start_time", "end_time", "notes"):
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.setdefault("class", "input-control")
                self.fields[field_name].widget.attrs.setdefault("style", "background:rgba(6,23,28,0.6); border:1px solid var(--stroke); color:#EAFBF9; padding:10px 12px; border-radius:12px;")

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        booking_date = cleaned.get("date")
        if start and end and start >= end:
            self.add_error("end_time", "End time must be later than start time.")
        if booking_date and booking_date < date.today():
            self.add_error("date", "Please select a date in the future.")
        if booking_date and start and end:
            overlapping = (
                Booking.objects.filter(
                    venue=self.venue,
                    date=booking_date,
                )
                .exclude(status=Booking.Status.CANCELLED)
                .exclude(status=Booking.Status.REJECTED)
                .filter(start_time__lt=end, end_time__gt=start)
            )
            if overlapping.exists():
                raise forms.ValidationError(
                    "The selected time overlaps with an existing booking. Please choose another slot."
                )
        return cleaned


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {
            "rating": forms.RadioSelect(
                choices=[(i, str(i)) for i in range(1, 6)],
            ),
            "comment": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Share your experience playing here...",
                }
            ),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get("rating")
        if rating not in range(1, 6):
            raise forms.ValidationError("Please choose a rating between 1 and 5.")
        return rating

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["comment"].widget.attrs.setdefault(
            "style",
            "background:rgba(6,23,28,0.6); border:1px solid var(--stroke); color:#EAFBF9; padding:10px 12px; border-radius:12px;",
        )

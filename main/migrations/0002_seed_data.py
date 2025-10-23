from django.db import migrations
from django.utils.text import slugify


def create_seed_data(apps, schema_editor):
    VenueCategory = apps.get_model('main', 'VenueCategory')
    Amenity = apps.get_model('main', 'Amenity')
    Venue = apps.get_model('main', 'Venue')
    VenueImage = apps.get_model('main', 'VenueImage')
    AddOn = apps.get_model('main', 'AddOn')

    category_specs = [
        ('futsal', 'Futsal Arena'),
        ('basketball', 'Basketball Court'),
        ('badminton', 'Badminton Hall'),
    ]

    categories = {}
    for key, name in category_specs:
        slug = slugify(name)
        category, _ = VenueCategory.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
            },
        )
        categories[key] = category

    amenities = {}
    for name in [
        'Locker Room',
        'Shower Facility',
        'Scoreboard',
        'Premium Lighting',
        'Hydration Station',
        'Coaching Bench',
        'Medical Kit',
    ]:
        amenity, _ = Amenity.objects.get_or_create(name=name)
        amenities[name] = amenity

    venues_data = [
        {
            'name': 'Arena Sinar Utama',
            'city': 'Jakarta',
            'address': 'Jl. Sudirman No. 21, Jakarta',
            'category': categories['futsal'],
            'price_per_hour': 450000,
            'capacity': 12,
            'hero_image': 'https://images.unsplash.com/photo-1529421308418-eab9886eff54?auto=format&fit=crop&w=1200&q=80',
            'description': 'Five-a-side indoor turf with FIFA grade lighting and seamless locker flow.',
            'highlights': 'FIFA Certified Turf,Instant Hydration Bar,VIP Locker Suite',
            'amenities': ['Locker Room', 'Premium Lighting', 'Hydration Station', 'Medical Kit'],
            'images': [
                'https://images.unsplash.com/photo-1508602637331-485529c7b3fb?auto=format&fit=crop&w=1200&q=80',
                'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=1200&q=80',
            ],
            'add_ons': [
                ('Match Official', 150000, 'Certified referee for competitive play'),
                ('High-Speed Camera', 200000, 'Capture match highlights in 4K'),
            ],
        },
        {
            'name': 'Skyline Hoop Dome',
            'city': 'Bandung',
            'address': 'Jl. Braga No. 77, Bandung',
            'category': categories['basketball'],
            'price_per_hour': 520000,
            'capacity': 10,
            'hero_image': 'https://images.unsplash.com/photo-1519861155730-0b5fbf0dd889?auto=format&fit=crop&w=1200&q=80',
            'description': 'NBA sized hardwood with climate control, perfect for scrimmages and leagues.',
            'highlights': 'Maple Hardwood Court,Instant Replay Screen,Climate Controlled Dome',
            'amenities': ['Locker Room', 'Scoreboard', 'Premium Lighting', 'Coaching Bench'],
            'images': [
                'https://images.unsplash.com/photo-1517649763962-0c623066013b?auto=format&fit=crop&w=1200&q=80',
                'https://images.unsplash.com/photo-1521412644187-c49fa049e84d?auto=format&fit=crop&w=1200&q=80',
            ],
            'add_ons': [
                ('Live Stats Table', 180000, 'In-game statistician and digital scoreboard integration'),
                ('Premium Ball Rental', 60000, 'Official game balls sanitized and ready'),
            ],
        },
        {
            'name': 'Featherlight Badminton Hub',
            'city': 'Yogyakarta',
            'address': 'Jl. Malioboro No. 9, Yogyakarta',
            'category': categories['badminton'],
            'price_per_hour': 280000,
            'capacity': 8,
            'hero_image': 'https://images.unsplash.com/photo-1551958219-acbc608c6377?auto=format&fit=crop&w=1200&q=80',
            'description': 'High ceiling tournament-ready courts with anti-slip mat and pro lighting.',
            'highlights': 'Tournament Grade Flooring,Instant Stringing Service,Rest Lounge',
            'amenities': ['Locker Room', 'Premium Lighting', 'Hydration Station'],
            'images': [
                'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=1200&q=80',
                'https://images.unsplash.com/photo-1504639725590-34d0984388bd?auto=format&fit=crop&w=1200&q=80',
            ],
            'add_ons': [
                ('Shuttlecock Bundle', 40000, 'Competition grade shuttlecock pack'),
                ('On-site Coach', 220000, 'Certified coach to guide drills and tactics'),
            ],
        },
    ]

    for data in venues_data:
        slug = slugify(data['name'])
        venue, created = Venue.objects.get_or_create(
            slug=slug,
            defaults={
                'name': data['name'],
                'city': data['city'],
                'address': data['address'],
                'category': data['category'],
                'price_per_hour': data['price_per_hour'],
                'capacity': data['capacity'],
                'hero_image': data['hero_image'],
                'description': data['description'],
                'highlights': data['highlights'],
            },
        )
        if not created:
            Venue.objects.filter(pk=venue.pk).update(
                name=data['name'],
                city=data['city'],
                address=data['address'],
                category=data['category'],
                price_per_hour=data['price_per_hour'],
                capacity=data['capacity'],
                hero_image=data['hero_image'],
                description=data['description'],
                highlights=data['highlights'],
            )
            venue.refresh_from_db()
        venue.amenities.set([amenities[name] for name in data['amenities']])
        for image in data['images']:
            VenueImage.objects.get_or_create(venue=venue, image_url=image)
        for name, price, description in data['add_ons']:
            AddOn.objects.get_or_create(
                venue=venue,
                name=name,
                defaults={'price': price, 'description': description},
            )


def delete_seed_data(apps, schema_editor):
    Venue = apps.get_model('main', 'Venue')
    VenueCategory = apps.get_model('main', 'VenueCategory')
    Amenity = apps.get_model('main', 'Amenity')

    venue_names = [
        'Arena Sinar Utama',
        'Skyline Hoop Dome',
        'Featherlight Badminton Hub',
    ]
    Venue.objects.filter(name__in=venue_names).delete()
    VenueCategory.objects.filter(name__in=[
        'Futsal Arena',
        'Basketball Court',
        'Badminton Hall',
    ]).delete()
    Amenity.objects.filter(name__in=[
        'Locker Room',
        'Shower Facility',
        'Scoreboard',
        'Premium Lighting',
        'Hydration Station',
        'Coaching Bench',
        'Medical Kit',
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_seed_data, delete_seed_data),
    ]

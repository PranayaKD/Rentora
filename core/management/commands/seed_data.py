import random
from django.core.management.base import BaseCommand
from core.models import Car

class Command(BaseCommand):
    help = 'Seeds database with 76 Indian cars and premium vehicles'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')
        
        cars_data = [
            # BUDGET SEGMENT (499 - 3999)
            ("Maruti Suzuki", "Alto K10", "Hatchback", 499, 5, "Petrol/CNG", "Manual", "1.0L", "24 kmpl", 1000, 150),
            ("Maruti Suzuki", "S-Presso", "Hatchback", 599, 5, "Petrol/CNG", "Manual/AMT", "1.0L", "25 kmpl", 1000, 150),
            ("Maruti Suzuki", "Wagon R", "Hatchback", 699, 5, "Petrol/CNG", "Manual/AMT", "1.2L", "23 kmpl", 1500, 150),
            ("Maruti Suzuki", "Swift", "Hatchback", 799, 5, "Petrol", "Manual/AMT", "1.2L", "22 kmpl", 2000, 150),
            ("Maruti Suzuki", "Baleno", "Hatchback", 1299, 5, "Petrol", "Manual/AMT", "1.2L", "22 kmpl", 2500, 150),
            ("Maruti Suzuki", "Dzire", "Sedan", 1499, 5, "Petrol/CNG", "Manual/AMT", "1.2L", "23 kmpl", 2500, 150),
            ("Maruti Suzuki", "Ertiga", "MPV", 1999, 7, "Petrol/CNG", "Manual/AT", "1.5L", "20 kmpl", 3000, 150),
            ("Maruti Suzuki", "Brezza", "Compact SUV", 2499, 5, "Petrol", "Manual/AT", "1.5L", "19 kmpl", 3500, 150),
            ("Maruti Suzuki", "Grand Vitara", "SUV", 2999, 5, "Hybrid", "Manual/AT", "1.5L", "27 kmpl", 4000, 150),
            
            ("Tata", "Tiago", "Hatchback", 799, 5, "Petrol/CNG", "Manual/AMT", "1.2L", "20 kmpl", 1500, 150),
            ("Tata", "Tigor", "Sedan", 1299, 5, "Petrol/CNG", "Manual/AMT", "1.2L", "20 kmpl", 2500, 150),
            ("Tata", "Tiago EV", "Electric", 1499, 5, "Electric", "Automatic", "Electric 55kW", "315 km", 3000, 150),
            ("Tata", "Tigor EV", "Electric", 1699, 5, "Electric", "Automatic", "Electric 55kW", "315 km", 3500, 150),
            ("Tata", "Punch", "Micro SUV", 1599, 5, "Petrol/CNG", "Manual/AMT", "1.2L", "19 kmpl", 2500, 150),
            ("Tata", "Punch EV", "Electric", 1999, 5, "Electric", "Automatic", "Electric", "421 km", 3500, 150),
            ("Tata", "Nexon", "Compact SUV", 2199, 5, "Petrol/Diesel", "Manual/AMT/AT", "1.2L Turbo", "17 kmpl", 4000, 150),
            ("Tata", "Nexon EV", "Electric", 2699, 5, "Electric", "Automatic", "Electric", "465 km", 4500, 150),
            ("Tata", "Harrier", "SUV", 3499, 5, "Diesel", "Manual/AT", "2.0L Diesel", "16 kmpl", 5000, 150),
            ("Tata", "Safari", "SUV", 3999, 7, "Diesel", "Manual/AT", "2.0L Diesel", "16 kmpl", 6000, 150),
            
            ("Hyundai", "Grand i10 Nios", "Hatchback", 899, 5, "Petrol/CNG", "Manual/AMT", "1.2L", "20 kmpl", 2000, 150),
            ("Hyundai", "i20", "Hatchback", 1499, 5, "Petrol/Diesel", "Manual/IVT/DCT", "1.2L", "20 kmpl", 2500, 150),
            ("Hyundai", "Aura", "Sedan", 1299, 5, "Petrol/CNG", "Manual/AMT", "1.2L", "20 kmpl", 2500, 150),
            ("Hyundai", "Verna", "Sedan", 2199, 5, "Petrol", "Manual/IVT/DCT", "1.5L Turbo", "18 kmpl", 3500, 150),
            ("Hyundai", "Venue", "Compact SUV", 1899, 5, "Petrol/Diesel/CNG", "Manual/IMT/DCT", "1.0L Turbo", "18 kmpl", 3000, 150),
            ("Hyundai", "Creta", "SUV", 2699, 5, "Petrol/Diesel", "Manual/IVT/DCT/AT", "1.5L", "17 kmpl", 4000, 150),
            ("Hyundai", "Creta Electric", "Electric", 2999, 5, "Electric", "Automatic", "Electric", "473 km", 4500, 150),
            ("Hyundai", "Alcazar", "SUV", 3499, 7, "Petrol/Diesel", "Manual/AT", "1.5L Turbo", "16 kmpl", 5000, 150),
            ("Hyundai", "Tucson", "Premium SUV", 10999, 5, "Petrol/Diesel", "AT", "2.0L Diesel", "15 kmpl", 15000, 150),
            
            ("Mahindra", "KUV100", "Micro SUV", 999, 6, "Petrol/Diesel", "Manual", "1.2L", "18 kmpl", 2000, 150),
            ("Mahindra", "Bolero", "SUV", 2199, 7, "Diesel", "Manual", "1.5L Diesel", "16 kmpl", 3000, 150),
            ("Mahindra", "Bolero Neo", "Compact SUV", 1999, 7, "Diesel", "Manual", "1.5L Diesel", "17 kmpl", 3000, 150),
            ("Mahindra", "Scorpio N", "SUV", 3499, 7, "Petrol/Diesel", "Manual/AT", "2.2L Diesel", "15 kmpl", 5000, 150),
            ("Mahindra", "Scorpio Classic", "SUV", 2999, 7, "Diesel", "Manual", "2.2L Diesel", "15 kmpl", 4500, 150),
            ("Mahindra", "XUV300", "Compact SUV", 1999, 5, "Petrol/Diesel", "Manual/AMT", "1.2L Turbo", "17 kmpl", 3500, 150),
            ("Mahindra", "XUV400 EV", "Electric", 2699, 5, "Electric", "Automatic", "Electric", "456 km", 4500, 150),
            ("Mahindra", "XUV700", "Premium SUV", 11999, 7, "Petrol/Diesel", "Manual/AT", "2.0L Turbo", "15 kmpl", 20000, 150),
            ("Mahindra", "Thar", "Off-road SUV", 3999, 4, "Petrol/Diesel", "Manual/AT", "2.2L Diesel", "15 kmpl", 6000, 150),
            ("Mahindra", "Thar Roxx", "Off-road SUV", 4499, 5, "Petrol/Diesel", "Manual/AT", "2.0L Turbo", "15 kmpl", 7000, 150),
            ("Mahindra", "BE 6", "Electric", 12999, 5, "Electric", "Automatic", "Electric", "682 km", 20000, 150),
            
            # MID SEGMENT
            ("Volkswagen", "Polo", "Hatchback", 2299, 5, "Petrol", "Manual/AT", "1.0L TSI", "18 kmpl", 4000, 150),
            ("Volkswagen", "Virtus", "Sedan", 2999, 5, "Petrol", "Manual/AT/DSG", "1.0L TSI", "18 kmpl", 5000, 150),
            ("Volkswagen", "Taigun", "Compact SUV", 3499, 5, "Petrol", "Manual/AT/DSG", "1.0L TSI", "17 kmpl", 6000, 150),
            ("Volkswagen", "Tiguan", "Premium SUV", 10999, 5, "Petrol", "DSG", "2.0L TSI", "14 kmpl", 12000, 150),
            
            ("Skoda", "Slavia", "Sedan", 2999, 5, "Petrol", "Manual/AT/DSG", "1.0L TSI", "18 kmpl", 5000, 150),
            ("Skoda", "Kushaq", "Compact SUV", 3499, 5, "Petrol", "Manual/AT/DSG", "1.0L TSI", "17 kmpl", 6000, 150),
            ("Skoda", "Kodiaq", "Premium SUV", 12999, 7, "Petrol", "DSG", "2.0L TSI", "13 kmpl", 12000, 150),
            ("Skoda", "Superb", "Luxury Sedan", 14999, 5, "Petrol", "DSG", "2.0L TSI", "14 kmpl", 15000, 150),
            
            ("Honda", "Amaze", "Sedan", 1699, 5, "Petrol", "Manual/CVT", "1.2L", "19 kmpl", 3000, 150),
            ("Honda", "City", "Sedan", 2499, 5, "Hybrid", "Manual/CVT", "1.5L", "24 kmpl", 5000, 150),
            ("Honda", "Elevate", "SUV", 3499, 5, "Petrol", "Manual/CVT", "1.5L", "16 kmpl", 6000, 150),
            
            ("Toyota", "Glanza", "Hatchback", 1599, 5, "Petrol/CNG", "Manual/AMT", "1.2L", "22 kmpl", 3000, 150),
            ("Toyota", "Urban Cruiser Hyryder", "Hybrid", 3499, 5, "Hybrid", "Manual/AT", "1.5L Hybrid", "27 kmpl", 6000, 150),
            ("Toyota", "Innova Crysta", "MPV", 4999, 7, "Petrol/Diesel", "Manual/AT", "2.4L Diesel", "15 kmpl", 8000, 150),
            ("Toyota", "Innova HyCross", "Hybrid", 12999, 7, "Hybrid", "e-CVT", "2.0L Hybrid", "21 kmpl", 20000, 150),
            ("Toyota", "Fortuner", "Premium SUV", 15999, 7, "Petrol/Diesel", "Manual/AT", "2.8L Diesel", "14 kmpl", 25000, 150),
            ("Toyota", "Corolla Hybrid", "Luxury Sedan", 11999, 5, "Hybrid", "e-CVT", "1.8L Hybrid", "23 kmpl", 15000, 150),
            
            ("Kia", "Sonet", "Compact SUV", 2499, 5, "Petrol/Diesel", "Manual/IMT/DCT/AT", "1.0L Turbo", "18 kmpl", 5000, 150),
            ("Kia", "Seltos", "SUV", 3499, 5, "Petrol/Diesel", "Manual/IVT/DCT/AT", "1.5L Turbo", "16 kmpl", 6000, 150),
            ("Kia", "Carens", "MPV", 3999, 7, "Petrol/Diesel", "Manual/DCT/AT", "1.5L Turbo", "16 kmpl", 7000, 150),
            ("Kia", "EV6", "Electric", 12999, 5, "Electric", "Automatic", "Electric", "528 km", 15000, 150),
            
            ("MG", "Hector", "SUV", 3499, 6, "Hybrid", "Manual/CVT/DCT", "1.5L Turbo", "15 kmpl", 8000, 150),
            ("MG", "ZS EV", "Electric", 3999, 5, "Electric", "Automatic", "Electric", "461 km", 7000, 150),
            ("MG", "Comet EV", "Micro SUV", 999, 4, "Electric", "Automatic", "Electric", "230 km", 2000, 150),
            ("MG", "Windsor EV", "Electric", 2499, 5, "Electric", "Automatic", "Electric", "331 km", 5000, 150),
            
            # PREMIUM SEGMENT (> 10000)
            ("BMW", "3 Series", "Luxury Sedan", 19999, 5, "Petrol/Diesel", "AT", "2.0L", "14 kmpl", 25000, 150),
            ("BMW", "5 Series", "Luxury Sedan", 24999, 5, "Petrol/Diesel", "AT", "2.0L", "12 kmpl", 35000, 150),
            ("BMW", "X1", "Premium SUV", 16999, 5, "Hybrid", "AT", "1.5L", "18 kmpl", 25000, 150),
            ("BMW", "X5", "Premium SUV", 29999, 5, "Petrol/Diesel", "AT", "3.0L", "10 kmpl", 50000, 150),
            ("Mercedes-Benz", "C-Class", "Luxury Sedan", 18999, 5, "Petrol", "AT", "1.5L Turbo", "14 kmpl", 30000, 150),
            ("Mercedes-Benz", "E-Class", "Luxury Sedan", 24999, 5, "Petrol/Diesel", "AT", "2.0L", "12 kmpl", 40000, 150),
            ("Mercedes-Benz", "GLC", "Premium SUV", 21999, 5, "Petrol", "AT", "2.0L Turbo", "12 kmpl", 35000, 150),
            ("Audi", "A4", "Luxury Sedan", 17999, 5, "Petrol", "DSG", "2.0L TFSI", "14 kmpl", 30000, 150),
            ("Audi", "Q3", "Premium SUV", 18999, 5, "Petrol", "DSG", "1.4L TFSI", "15 kmpl", 30000, 150),
            
            # ULTRA LUXURY
            ("Mercedes-Benz", "S-Class", "Ultra Luxury", 59999, 5, "Petrol", "AT", "3.0L", "10 kmpl", 100000, 150),
            ("BMW", "7 Series", "Ultra Luxury", 54999, 5, "Hybrid", "AT", "3.0L", "10 kmpl", 100000, 150),
            ("Rolls Royce", "Ghost", "Ultra Luxury", 149999, 5, "Petrol", "AT", "6.75L V12", "6 kmpl", 500000, 150),
            ("Bentley", "Bentayga", "Ultra Luxury", 129999, 5, "Petrol", "AT", "4.0L V8", "8 kmpl", 500000, 150),
            ("Land Rover", "Defender 110", "Premium SUV", 34999, 5, "Diesel", "AT", "3.0L", "12 kmpl", 50000, 150),
            ("Land Rover", "Range Rover Sport", "Ultra Luxury", 49999, 5, "Hybrid", "AT", "3.0L", "10 kmpl", 100000, 150),
        ]

        count = 0
        for data in cars_data:
            brand, name, category, price, seats, fuel, trans, engine, mileage, deposit, free_km = data
            
            # Dummy image formatted name
            brand_slug = brand.lower().replace(" ", "-")
            name_slug = name.lower().replace(" ", "-")
            image_path = f"cars/{brand_slug}-{name_slug}.jpg"
            
            car, created = Car.objects.update_or_create(
                brand=brand,
                name=name,
                defaults={
                    'category': category,
                    'price_per_day': price,
                    'seats': seats,
                    'fuel_type': fuel,
                    'transmission': trans,
                    'engine': engine,
                    'mileage': mileage,
                    'security_deposit': deposit,
                    'free_km': free_km,
                    'rating': round(random.uniform(3.5, 5.0), 1),
                }
            )
            if created:
                car.image = image_path
                car.is_available = random.choice([True, True, True, False])
                car.save()
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {count} cars.'))
        
        # FINAL GLOBAL AUDIT: Enforce User Pricing Tiers
        from django.db.models import Q
        from decimal import Decimal
        
        self.stdout.write('Running global pricing audit...')
        premium_brands = ['Tesla', 'BMW', 'Mercedes-Benz', 'Audi', 'Rolls Royce', 'Bentley', 'Mercedes', 'Land Rover', 'Lamborghini', 'Porsche']
        indian_brands = ['Maruti Suzuki', 'Tata', 'Mahindra', 'Hyundai', 'Kia', 'Skoda', 'Volkswagen', 'MG', 'Honda']
        # Toyota is now a mixed/premium brand, handled separately
        
        # 1. Ensure Premium Brands are > 10,000
        premium_updated = Car.objects.filter(brand__in=premium_brands, price_per_day__lt=10000).update(price_per_day=Decimal(25000))
        
        # 2. Handle Toyota Luxury Specifically
        toyota_luxury_updated = Car.objects.filter(brand='Toyota', name__in=['Fortuner', 'Innova HyCross', 'Corolla Hybrid'], price_per_day__lt=10000).update(price_per_day=Decimal(15000))
        
        # 3. Ensure non-luxury Indian cars are in 499-3999 range
        indian_restricted = Car.objects.filter(
            brand__in=indian_brands
        ).exclude(
            Q(category__icontains='Luxury') | Q(category__icontains='Premium')
        )
        
        # Cap at 3999
        over_priced_indian = indian_restricted.filter(price_per_day__gt=3999).update(price_per_day=Decimal(3999))
        
        # Bottom floor 499
        under_priced_indian = indian_restricted.filter(price_per_day__lt=499).update(price_per_day=Decimal(499))
        
        self.stdout.write(self.style.SUCCESS(f'Audit Complete: Updated {premium_updated} Premium cars and {over_priced_indian + under_priced_indian} Indian cars.'))

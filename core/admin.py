from django.contrib import admin
from .models import Car, Booking, Review, Wishlist, PromoCode, Notification


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'category', 'price_per_day', 'is_available', 'rating')
    list_filter = ('category', 'fuel_type', 'is_available')
    search_fields = ('name', 'brand')
    list_editable = ('is_available',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'user', 'car', 'pickup_date', 'dropoff_date', 'total_price', 'status')
    list_filter = ('status', 'pickup_date')
    search_fields = ('booking_reference', 'user__username')
    list_editable = ('status',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'car', 'rating', 'created_at')
    list_filter = ('rating',)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'car', 'created_at')


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'is_active', 'used_count', 'usage_limit', 'expiry_date')
    list_filter = ('is_active', 'discount_type')
    search_fields = ('code',)




@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('user__username', 'title')

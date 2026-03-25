from django.urls import path
from . import views

urlpatterns = [
    path('admin-panel/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-panel/cars/', views.admin_cars_list_view, name='admin_cars_list'),
    path('admin-panel/cars/add/', views.admin_car_add_view, name='admin_car_add'),
    path('admin-panel/cars/edit/<int:car_id>/', views.admin_car_edit_view, name='admin_car_edit'),
    path('admin-panel/cars/delete/<int:car_id>/', views.admin_car_delete_view, name='admin_car_delete'),
    path('admin-panel/bookings/', views.admin_bookings_list_view, name='admin_bookings_list'),
    path('admin-panel/bookings/<int:booking_id>/status/', views.admin_booking_status_view, name='admin_booking_status'),
    path('api/admin/revenue/', views.api_admin_revenue, name='api_admin_revenue'),
]

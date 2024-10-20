# shifts/urls.py

from django.urls import path
from . import views

app_name = 'shifts'

urlpatterns = [
    # Shift Management URLs
    path('', views.ShiftListView.as_view(), name='shift_list'),
    path('create/', views.ShiftCreateView.as_view(), name='shift_create'),
    path('<int:pk>/update/', views.ShiftUpdateView.as_view(), name='shift_update'),
    path('<int:pk>/delete/', views.ShiftDeleteView.as_view(), name='shift_delete'),
    path('<int:pk>/', views.ShiftDetailView.as_view(), name='shift_detail'),
    path('<int:shift_id>/book/', views.book_shift, name='book_shift'),
    path('<int:shift_id>/unbook/', views.unbook_shift, name='unbook_shift'),
    path('<int:shift_id>/complete/', views.ShiftCompleteView.as_view(), name='shift_complete'),
    path('get_address/', views.get_address, name='get_address'),
    path('<int:pk>/assign/', views.assign_worker, name='assign_worker'),

    # Staff Management URLs
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.add_staff, name='add_staff'),
    path('staff/<int:user_id>/edit/', views.edit_staff, name='edit_staff'),
    path('staff/<int:user_id>/delete/', views.delete_staff, name='delete_staff'),
]
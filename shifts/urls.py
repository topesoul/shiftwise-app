from django.urls import path
from .views import (
    ShiftListView,
    ShiftCreateView,
    ShiftUpdateView,
    ShiftDeleteView,
    ShiftDetailView,
    book_shift,
    unbook_shift,
    get_address,
)

app_name = 'shifts'

urlpatterns = [
    path('', ShiftListView.as_view(), name='shift_list'),
    path('create/', ShiftCreateView.as_view(), name='shift_create'),
    path('<int:pk>/edit/', ShiftUpdateView.as_view(), name='shift_update'),
    path('<int:pk>/delete/', ShiftDeleteView.as_view(), name='shift_delete'),
    path('<int:pk>/', ShiftDetailView.as_view(), name='shift_detail'),
    path('<int:shift_id>/book/', book_shift, name='book_shift'),
    path('<int:shift_id>/unbook/', unbook_shift, name='unbook_shift'),
    path('get_address/', get_address, name='get_address'),
]
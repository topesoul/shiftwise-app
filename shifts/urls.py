from django.urls import path
from .views import ShiftListView, ShiftCreateView, ShiftUpdateView, ShiftDeleteView, book_shift

app_name = 'shifts'

urlpatterns = [
    path('', ShiftListView.as_view(), name='shift_list'),
    path('create/', ShiftCreateView.as_view(), name='shift_create'),
    path('<int:pk>/edit/', ShiftUpdateView.as_view(), name='shift_update'),
    path('<int:pk>/delete/', ShiftDeleteView.as_view(), name='shift_delete'),
    path('<int:shift_id>/book/', book_shift, name='book_shift'),
]

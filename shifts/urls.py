from django.urls import path
from .views import ShiftListView, ShiftCreateView, ShiftUpdateView, ShiftDeleteView

urlpatterns = [
    path('', ShiftListView.as_view(), name='shift_list'),
    path('create/', ShiftCreateView.as_view(), name='shift_create'),
    path('<int:pk>/edit/', ShiftUpdateView.as_view(), name='shift_update'),
    path('<int:pk>/delete/', ShiftDeleteView.as_view(), name='shift_delete'),
]

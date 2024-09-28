from django.urls import path
from . import views

urlpatterns = [
    path('', views.shift_list, name='shift_list'),
    path('create/', views.shift_create, name='shift_create'),
    path('<int:pk>/edit/', views.shift_update, name='shift_update'),
    path('<int:pk>/delete/', views.shift_delete, name='shift_delete'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.hardware_list, name='hardware_list'),
    path('<int:hw_id>/', views.hardware_detail, name='hardware_detail'),
    path('my/', views.my_hardware, name='my_hardware'),
    path('add/', views.add_user_hardware, name='add_user_hardware'),
    path('<int:hw_id>/remove/', views.remove_user_hardware, name='remove_user_hardware'),
]

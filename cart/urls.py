from . import views
from django.urls import path
from .views import ProductAPI, CartAPI


urlpatterns = [
    path('products', ProductAPI.as_view(), name='products'),
    path('cart', CartAPI.as_view(), name='cart'),

]

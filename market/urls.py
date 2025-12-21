from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cart/', views.cart, name='cart'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('callback', views.payment_response, name='payment_response'),
    path('webhook/', views.webhook_flw, name='webhook'),
    path('send-email/', views.send_test_email, name='send_test_email')

] 

from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path ("checkout/", views.checkoutView, name="checkout"),
    path ("detailcheckout/<int:id>/", views.detailCheckoutView, name="detailcheckout"),
    path('callback', views.payment_response, name='payment_response'),
    path('webhook/', views.webhook_flw, name='webhook')
]




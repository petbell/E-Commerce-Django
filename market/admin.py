from django.contrib import admin
from .models import Product, Carts, CartItem, Transaction, Order

# Register your models here.
admin.site.register(Product)
admin.site.register(Carts)
admin.site.register(CartItem)
admin.site.register(Transaction)
admin.site.register(Order)
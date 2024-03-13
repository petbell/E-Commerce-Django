from django.contrib import admin
from .models import Product, Carts, CartItem, Transaction

# Register your models here.
admin.site.register(Product)
admin.site.register(Carts)
admin.site.register(CartItem)
admin.site.register(Transaction)
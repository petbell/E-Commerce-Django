from django.contrib import admin
from .models import Items, Cart, CartItem

# Register your models here.
admin.site.register(Items)
admin.site.register(Cart)
admin.site.register(CartItem)
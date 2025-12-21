from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name


# changed to carts cos of reverse accessor error with payments.cart.user
class Carts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='CartItem')
    
    
    #def __str__(self):
     #   return User(self.user)
    
    @property
    def total_amount (self):
        cartitems = self.cartitem_set.all()
        total = sum([item.total_price for item in cartitems])
        #item.total_price for item in cartitems
        return total
    
    
    @property
    def num_of_items(self):
        cartitems = self.cartitem_set.all()
        quantity = sum([item.quantity for item in cartitems])
        return quantity

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Carts, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    
    @property 
    def total_price(self):
        all_price = self.product.price * self.quantity
        return all_price
    
    
    def __str__(self):
        return str(self.id)
    
class Transaction(models.Model):
    customer_name = models.CharField (max_length= 100, null=True)
    email = models.EmailField (max_length= 100, null=True)
    phone = models.CharField (max_length= 20, null=True)
    status = models.CharField (max_length= 20, null=True, default='pending')
    amount = models.IntegerField(default= 0)
    tx_ref = models.CharField (max_length= 100)
    currency= models.CharField (max_length= 20, default='NGN', null=True)
    #transaction_id = models.CharField (max_length= 100, null=True)
    transaction_id = models.IntegerField ( null=True, unique=True)
    payment_type = models.CharField (max_length= 100, null=True)
    date= models.DateTimeField(auto_now_add=True)

    
    def __str__(self):
        return self.tx_ref
    
class Order(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} - {self.total_price}"

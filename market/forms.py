from django import forms

class CheckoutForm (forms.Form):
    customer_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    phone = forms.IntegerField()
    
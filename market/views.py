from django.shortcuts import render, redirect
from .models import Product, CartItem , Carts, Transaction
from django.http import HttpResponse, JsonResponse

import math, random, requests, hashlib
from .forms import CheckoutForm
from django.views.decorators.http import require_http_methods
from django.conf import settings
import qrcode

secretKey = settings.FLW_SECRET_KEY

# Create your views here.
def home(request):
    products = Product.objects.all()
    print (products)
    
    print (request)
    return render(request, 'home.html', {'products': products})

def checkout(request,):
    data = Carts.objects.get(user=request.user)
    print(f" Cart is: {data.total_amount}")
    pass
        
def add_to_cart(request, product_id):
    product = Product.objects.get(pk=product_id)
    cart, created = Carts.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(product=product, cart=cart)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart')

def remove_from_cart(request, cart_item_id):
    cart_item = CartItem.objects.get(pk=cart_item_id)
    cart_item.delete()
    return redirect('cart')

def cart(request):
    cart, created = Carts.objects.get_or_create(user = request.user)
    cart_items = cart.cartitem_set.all()
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            print ('valid')
            name = form.cleaned_data['customer_name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            #convert decimal to int so that json can serialize it
            amount = int(cart.total_amount)
                       
            request_body = request.body
            print(request_body)
            #Add the following variables here so that I can do run the checksum laater
            currency = "NGN"
            tx_ref = 'Order'+str(math.floor(1000000 + random.random()*9000000))
            
            print(amount)

            Tr = Transaction(customer_name = name, email=email,phone=phone, amount=amount, tx_ref=
                             tx_ref)
            Tr.save()
        # Process the payment with Flutterwave API
        return redirect (str(process_payment(name, email, amount, phone, currency, tx_ref)))
        # You'll need to integrate Flutterwave's API here
        # After successful payment, create an order record
        #return render(request, 'checkout_success.html')
    else:
        
        form = CheckoutForm()

        """qr = qrcode.make('http://localhost:8000/market/cart/')
        qr.save("media/qr.png", scale=10, fill_color = 'lightblue', dark_color = 'red')    
           """ 
    
    
    print (cart_items)
    print (cart.total_amount)
    return render(request, 'cart.html', {'cart_items': cart_items, 'cart': cart , 'form_keys': form})

def process_payment (name, email, amount, phone, currency, tx_ref):
    # leave no space and remove quotes in the .env file
    auth_token = secretKey 
    head = {'Authorization' : 'Bearer '+ auth_token}
    hashedSecretKey = shaEncryption(secretKey)
    StringToBeHashed = str(amount) + currency + email + tx_ref + hashedSecretKey
    payload_hash = shaEncryption(StringToBeHashed)
    print(payload_hash)

    data = {
                "tx_ref":tx_ref,
                "amount":amount,
                "currency":currency,
                "redirect_url":"http://localhost:8000/market/callback",
                "payment_options":"card",
                "meta":{
                    "consumer_id":23,
                    "consumer_mac":"92a3-912ba-1192a"
                },
                "customer":{
                    "email":email,
                    "phonenumber":phone,
                    "name":name
                },
                "customizations":{
                    "title":"Bello Electronics Store",
                    "description":"Best store in town",
                    "logo":"https://getbootstrap.com/docs/4.0/assets/brand/bootstrap-solid.svg"
                },
                "payload_hash" :  payload_hash
                }
    url = ' https://api.flutterwave.com/v3/payments'
    response = requests.post(url, json=data, headers=head)
    response=response.json()
    link=response['data']['link']
    return link

# function to hash checksum
def shaEncryption(input):
    encoded_bytes = input.encode()
    sha256 = hashlib.sha256()
    sha256.update(encoded_bytes)
    encryptedString = sha256.hexdigest()
    return encryptedString

@require_http_methods(['GET', 'POST'])
def payment_response(request):
    if request.GET.get ('status') == 'successful':
        auth_token = secretKey 
        head = {'Authorization' : 'Bearer '+ auth_token}
        status=request.GET.get('status', None)
        tx_ref=request.GET.get('tx_ref', None)
        id = request.GET.get('transaction_id', None)
        
        Transaction_detail = Transaction.objects.filter(tx_ref=tx_ref).first()   
        print (str(Transaction_detail))
        payload = {"id": id}
        
        url = f"https://api.flutterwave.com/v3/transactions/{payload['id']}/verify"
        response = requests.get(url, params=id, headers=head)
        if response.status_code == 200:
            data = response.json()['data']
                
            if (data['status'] == "successful" and data['amount'] == Transaction_detail.amount and data['currency'] == 'NGN'):
                    Transaction.objects.filter(tx_ref=tx_ref).update(status=data['status'],transaction_id =data['id'], payment_type=data['payment_type'] )
                    context = {'order_keys': data}
                    
                    # clear cart
                    user_cart = Carts.objects.filter(user=request.user)
                    user_cart.delete()
                    
                    return render(request, 'checkout_success.html',context, status=200)
                
            else:
                #return render(request, 'checkout_success.html', status=400)
                return JsonResponse({'message': 'Payment NOT successfull'}, status=400)
        else:
            return JsonResponse({'message': 'Error verifying transaction'}, status=500)
            #return render(request, 'checkout_success.html', status=500)   
    
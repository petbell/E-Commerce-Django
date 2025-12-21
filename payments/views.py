from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from .forms import CheckoutForm
from .models import Items, Cart, CartItem
import random, math, requests, hashlib, json
import logging
# pip install django-environ not "environ"
import environ
#initialise environment variables
env = environ.Env()
environ.Env.read_env()

secretKey = env('SECRET_KEY')
# Create your views here.

def checkoutView(request):
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            
            return redirect(detailCheckoutView)
    else:
        form = CheckoutForm()
    context = {
            
            'form_keys': form
        }
    return render(request, 'payments/checkout.html', context)

def cart (request):
    cart = None
    cartitems = []
    
    cartitems = cart.get
    
    
def detailCheckoutView(request, id):
    data = Items.objects.get(item_id = id) 
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            print ('valid')
            name = form.cleaned_data['customer_name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            amount = data.item_price
            #Add the following variables here so that I can do run the checksum laater
            currency = "NGN"
            tx_ref = 'Product'+str(math.floor(1000000 + random.random()*9000000))
            
            #print(name + ""+amount)
            #print (form)
            context = {
        'product_keys': data,
            'form_keys': form
            }
            return redirect (str(process_payment(name, email, amount, phone, currency, tx_ref)))
        
            #return HttpResponse(f"Form posted {name} {email} {phone} {amount}")
        #return redirect ('detailcheckout')
            #return render (request, '/payments/checkout.html', context)
    else:
        form = CheckoutForm()
    context = {
        'product_keys': data,
            'form_keys': form
        }
    print (data.item_price)
    return render(request, 'payments/detailcheckout.html', context)

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
                "redirect_url":"http://localhost:8000/payments/callback",
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
    auth_token = secretKey 
    head = {'Authorization' : 'Bearer '+ auth_token}
    status=request.GET.get('status', None)
    tx_ref=request.GET.get('tx_ref', None)
    id = request.GET.get('transaction_id', None)
    amount = request.GET.get ('amount', None)
    
    payload = {"id": id}
    print(status)
    print(tx_ref)
    # vverify transaction
    #if status == 'successful':
     #   url = f"https://api.flutterwave.com/v3/transactions/{payload['id']}/verify"
      #  response = requests.get(url, params=id, headers=head)
        
        #another method of getting unpacking the dict of the api path parameter above
        #url1= "https://api.flutterwave.com/v3/transactions/{id}/verify"
        #response1 = requests.get(url1.format(**payload), params = payload, headers = head)
       # print (response.json())
        #if response.status == 'success' and response.data.amount = 
            
       # transaction_details = 
    print (amount)
    #sup = json.loads(request.body)
    print (request)
    
    
    
    #print (sup)
    #print (type(sup))
    return HttpResponse(f'Finished {status} {tx_ref} : {id}')
    #return redirect(webhook_flw)

@require_POST
@csrf_exempt
def webhook_flw (request):
    secretHash = env("FLW_SECRET_HASH")
    signature = request.headers.get("Verif-Hash")
    print (secretHash)
    print (f"Signature : {signature}")
    print (request.headers.get("verifi-hash"))
    print (request.headers)
    
    if signature == None or (signature != secretHash):
        #  Not from flutterwave; discard
        return HttpResponse("Not from flutterwave", status = 401)
    payload = request.body
    #log(payload)
    print (payload)
    response = requests.post()
    
    return HttpResponse(payload, status=200)
    
    
    


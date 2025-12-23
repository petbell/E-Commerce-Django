from django.shortcuts import render, redirect
from market.models import Product, CartItem , Carts, Transaction, Order
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
import json
import math, random, requests, hashlib
from .forms import CheckoutForm
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import send_mail
import qrcode
from telegram import Bot

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags




secretKey = settings.FLW_SECRET_KEY
secretHash = settings.FLW_SECRET_HASH

# Create your views here.
def home(request):
    
        
    products = Product.objects.all()
    print (products)
    #cart_items = []
    cart, created = Carts.objects.get_or_create(user = request.user)
    cart_items = cart.cartitem_set.all()
    print (request)
    print (cart_items)
    print(cart)
    return render(request, 'home.html', {'products': products, 'cart_items': cart_items, 'cart':cart})

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
    #return redirect('cart')
    return redirect('home')

def remove_from_cart(request, cart_item_id):
    cart_item = CartItem.objects.get(pk=cart_item_id)
    cart_item.delete()
    #return redirect('cart')
    return redirect ('home')

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
            
            
            # Save Transaction
            for cart_item in cart_items:
                print (cart_item)
            request_body = request.body
            print(request_body)
            #Add the following variables here so that I can do run the checksum laater
            currency = "NGN"
            tx_ref = 'Order'+str(math.floor(1000000 + random.random()*9000000))
            
            print(amount)

            transaction = Transaction(customer_name = name, email=email,phone=phone, amount=amount, tx_ref=
                             tx_ref)
            transaction.save()
            
            # Save the order items for each cart item
            for cart_item in cart_items:
                product = cart_item.product
                quantity = cart_item.quantity
                total_price = product.price * quantity
                
                # Create an order item for each order
                order = Order(transaction = transaction,
                              product = product,
                              quantity = quantity,
                              total_price = total_price)
                order.save()
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
        
    #return render(request, 'cart.html', {'cart_items': cart_items, 'cart': cart })

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
        params = {"id": id}
        
        url = f"https://api.flutterwave.com/v3/transactions/{params['id']}/verify"
        response = requests.get(url, params=params, headers=head)
        if response.status_code == 200:
            data = response.json()['data']
            json.dump(data, open('data.json', 'w'), indent=4)
            print(f" This is from PAYMENT RESPONSE: {data}")
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
    else:
        return HttpResponseBadRequest("Invalid request: status not successful")
    
def send_transaction_email(
    recipient_email, 
    subject, 
    context,
    template_name='emails/transaction_email.html'
):
    try:
        # Render HTML content
        html_message = render_to_string(template_name, context)
        
        # Plain text version
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,
            ["petbell@live.com"],
            html_message=html_message,
            fail_silently=False
        )
    except Exception as e:
        print(f"Error sending email: {e}")
        

def send_test_email(custmer_email, amount):
    subject = 'Test Email'
    message = f'This is a test email sent from Django. Amount: {amount}'
    email_from = settings.EMAIL_HOST_USER  # or your desired sender email
    recipient_list = [custmer_email]  # List of recipients

    # Send the email
    send_mail(subject, message, email_from, recipient_list)

    return HttpResponse('Email sent successfully!')
    
@require_POST
@csrf_exempt
def webhook_flw (request):
    if request.method == 'POST':
        secretHash = settings.FLW_SECRET_HASH
        signature = request.headers.get("Verif-Hash")
        print (secretHash)
        print (f"Signature : {signature}")
        print (request.headers.get("verif-hash"))
    #print (request.headers)
    
    
        if signature == None or (signature != secretHash):
            #  Not from flutterwave; discard
            return HttpResponse("Not from flutterwave", status = 401)
        try:
            data = json.loads(request.body)
            # Log the incoming request
            print(f"Headers: {request.headers}")
            print(f"REQUEST Body: {request.body.decode('utf-8')}")
            
            if data.get('status') == 'successful':
                tx_ref = data.get('tx_ref')
                amount = data.get('amount') 
                currency = data.get('currency')
                print (f" Transaction reference is : {tx_ref} and amount is {amount} {currency}")
                
                #send_test_email(custmer_email="petbell@live.com", amount=amount)
                print("Test email sent successfully.")
                return HttpResponse("Webhook processed", status=200)
        # Further processing can be done here
                
        except json.JSONDecodeError:
            return HttpResponse("Invalid JSON", status=400)

    return HttpResponse("Invalid request method", status=405)
       
    
    

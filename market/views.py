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
    if request.GET.get ('status') == 'completed':
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
            print(data)
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
    
    
    
    
@require_POST
@csrf_exempt
def webhook_flw (request):
    #secretHash = settings.FLW_SECRET_HASH
    #signature = request.headers.get("Verif-Hash")
    #print (secretHash)
    #print (f"Signature : {signature}")
    #print (request.headers.get("verif-hash"))
    #print (request.headers)
    
    
    #if signature == None or (signature != secretHash):
        #  Not from flutterwave; discard
    #    return HttpResponse("Not from flutterwave", status = 401)
    try:
        # Log the incoming request
        print(f"Headers: {request.headers}")
        print(f"Body: {request.body.decode('utf-8')}")
        
        # Access and decode the raw payload
        raw_payload = request.body
        payload = json.loads(raw_payload.decode('utf-8'))

        # Log or save the payload (useful for debugging)
        print(f"Webhook payload: {payload}")
        with open("payload.json", "w") as out_file:
            json.dump(payload, out_file, indent=4)

        # Extract data from the payload
        dataload = payload.get('data', {})
        transaction_id = dataload.get('id')
        status = dataload.get('status')
        tx_ref = dataload.get('tx_ref')
        amount = dataload.get('amount')
        customer_name = dataload.get('customer', {}).get('name')
        email = dataload.get('customer', {}).get('email')
        phone = dataload.get('customer', {}).get('phone_number')
        currency = dataload.get('currency')
        payment_type = dataload.get('payment_type')

        if not transaction_id or not status:
            return JsonResponse({"error": "Missing transaction ID or status in payload"}, status=400)

        # Check if the transaction already exists
        existing_event = Transaction.objects.filter(transaction_id=str(transaction_id)).first()

        if existing_event:
            # If the status is already updated, no need to process again
            if existing_event.status == status:
                return JsonResponse({"message": "Duplicate event, already processed"}, status=200)

            # Update the transaction if needed
            existing_event.status = status
            existing_event.save()
         
            
        #else:
            #it is always duplicating my records so i omitted the else block
            # Create a new transaction record if it doesn't exist
            #transaction, created = Transaction.objects.get_or_create(
             #   transaction_id=transaction_id, defaults={
              #      'status': status, 'tx_ref':tx_ref,
               #     'amount': amount, 'customer_name': customer_name,
                #    'email': email, 'phone': phone,
                 #   'currency': currency, 'payment_type': payment_type
                #})
                
                #transaction.save()
            #if not created:
             #   print (f"Transaction {transaction_id} already exists")
            
        orders = Order.objects.filter(transaction=existing_event)
        order_details = []
        for order in orders:
            order_details.append({
                'product': order.product.name,
                'quantity': order.quantity,
                'total_price': order.total_price,
                })
        print (order_details)
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=f"New order received: {order_details}")
        
                

        return JsonResponse({"message": "Transaction processed successfully"}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)
    #try:
     #   existing_event = Transaction.objects.filter(transaction_id=str(dataload['id'])).first()
      #  current_transaction_id = existing_event.id

    #except Transaction.DoesNotExist:
    #    existing_event = None
        
    #if existing_event and existing_event.status == status:
     #   return JsonResponse({}, status=200)
    # the following unnecessary, transaction already verified
    #transaction, created = Transaction.objects.update_or_create(transaction_id = payload['id'], 
     #                                    defaults={
      #                                       'status' : status,
       #                                      'payment_type': payment_type,
        #                                     'amount' : amount
         #                                })
    
    #print(f"Existing: {current_transaction_id} ")
    #process_event(latest_id)
    #response = requests.post()
    #send_test_email(payload)
    # Get customer details
    #customer_name = existing_event.customer_name
    #customer_email = existing_event.email
    #customer_phone = existing_event.phone

    # Retrieve all orders related to the current transaction
    #orders = Order.objects.filter(transaction=existing_event)
    
    # Prepare order details (products and quantities)
  #  order_details = []
   # for order in orders:
    #    order_details.append({
     #       'product': order.product.name,
      #      'quantity': order.quantity,
       #     'total_price': order.total_price,
        #})
    
    # Print or log the details for testing purposes
    #print(f"Customer Name: {customer_name}")
    #print(f"Customer Email: {customer_email}")
    #print(f"Customer Phone: {customer_phone}")
    #print(f"Order Details: {order_details}")
    
    # Respond with a success message
    #return JsonResponse({
     #   'message': 'Webhook processed successfully',
      #  'customer': {
       #     'name': customer_name,
        #    'email': customer_email,
         #   'phone': customer_phone,
       # },
       #3 'orders': order_details,
    #}, status=200)
#def process_event(record_id):
    # print (f" It all worked with : {payload}") 
    #goods = Order.objects.get(transaction_id = record_id ) 
    #send_welcome_email('petbell@live.com')
    
    
def send_test_email(request):
    subject = 'Test Email'
    message = 'This is a test email sent from Django.'
    email_from = settings.EMAIL_HOST_USER  # or your desired sender email
    recipient_list = ['petbell@example.com']  # List of recipients

    # Send the email
    send_mail(subject, message, email_from, recipient_list)

    #return HttpResponse('Email sent successfully!')
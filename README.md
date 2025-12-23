# E-Commerce-Django
Django E-Commerce site with flutterwave payment gateway.

Django Flutterwave Integration
A robust Django implementation for processing payments using the Flutterwave API. This project demonstrates how to handle standard payments, subscription plans, and secure webhook verification.

🚀 **Features**
Standard Checkout: Integration with Flutterwave's Hosted Checkout.
Webhook Handling: Secure endpoint to listen for payment events (successful transactions, failed payments).
Transaction Verification: Server-side verification of transaction IDs.
Transaction Logging: Database tracking of all payment attempts and statuses.
🛠️ **Prerequisites**
Python 3.13+
Django 5.0+
A Flutterwave account (Sign up here)
python-dotenv (for environment variables)
requests library
⚙️ Installation
Clone the repository:

bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
Create and activate a virtual environment:

bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:

bash
pip install -r requirements.txt
Environment Variables:
Create a .env file in the root directory and add your Flutterwave credentials:

env
(see .env.example for guidance)
FLW_PUBLIC_KEY=FLWPUBK_TEST-xxxxxxxxxxxx
FLW_SECRET_KEY=FLWSECK_TEST-xxxxxxxxxxxx
FLW_ENCRYPTION_KEY=xxxxxxxxxxxx
FLW_SECRET_HASH=your_custom_webhook_secret_hash
Run Migrations:

bash
python manage.py migrate
Start the server:

bash
python manage.py runserver
💳 Usage
Initiating a Payment
The payment flow starts by sending a POST request to the checkout view, which generates a Flutterwave payment link and redirects the user.

python
# Example logic in views.py
def payment_process(request):
    # Logic to call https://api.flutterwave.com/v3/payments
    # Returns the 'data.link' for redirection
    pass
Webhooks
To handle asynchronous notifications (like successful bank transfers), configure your Flutterwave Dashboard to point to:
https://your-domain.com/payments/webhook/

Note: For local testing, use ngrok to expose your local server to the internet.

🔒 **Security**
Secret Hash: This app validates the verif-hash header in webhooks to ensure requests come only from Flutterwave.
Server-side Verification: Never trust the frontend status. This app always performs a final GET request to /v3/transactions/{id}/verify before fulfilling an order.

🧪 Testing
To run the test suite:
bash
python manage.py test payments


📝 License
Distributed under the MIT License. See LICENSE for more information.



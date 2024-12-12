import base64
import requests
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


class MPesaError(Exception):
    """Custom exception for MPesa-related errors"""
    pass


def get_mpesa_access_token():
    """
    Generate MPesa Access Token
    """
    try:
        consumer_key = settings.MPESA_CONSUMER_KEY
        consumer_secret = settings.MPESA_CONSUMER_SECRET

        # Combine consumer key and secret
        credentials = f"{consumer_key}:{consumer_secret}"

        # Base64 encode the credentials
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

        # Prepare headers
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }

        # Request access token
        response = requests.get(
            'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',
            headers=headers,
            timeout=10
        )

        # Validate response
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            logger.error(f"Access Token Error: {response.text}")
            raise MPesaError("Failed to generate MPesa access token")

    except Exception as e:
        logger.error(f"Access Token Generation Error: {str(e)}")
        raise MPesaError(f"Access token error: {str(e)}")


def validate_phone_number(phone_number):
    """
    Validate and format phone number for MPesa
    """
    # Remove any non-digit characters
    phone = ''.join(filter(str.isdigit, str(phone_number)))

    # Ensure it starts with 254
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif not phone.startswith('254'):
        phone = '254' + phone

    # Validate length
    if len(phone) != 12:
        raise MPesaError(f"Invalid phone number format: {phone}")

    return phone


def generate_mpesa_password():
    """
    Generate MPesa Password for STK Push
    """
    try:
        business_shortcode = settings.MPESA_BUSINESS_SHORTCODE
        passkey = settings.MPESA_PASSKEY
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

        # Create password by concatenating business shortcode, passkey, and timestamp
        password_str = f"{business_shortcode}{passkey}{timestamp}"

        # Base64 encode
        password = base64.b64encode(password_str.encode('utf-8')).decode('utf-8')

        return {
            'password': password,
            'timestamp': timestamp
        }
    except Exception as e:
        logger.error(f"Password Generation Error: {str(e)}")
        raise MPesaError(f"Password generation error: {str(e)}")
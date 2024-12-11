import base64
import datetime
import logging
import requests
import time
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger('mpesa')


class MPesaError(Exception):
    """Custom exception for MPesa-related errors"""
    pass


def validate_phone_number(phone_number):
    """
    Validate and standardize phone number to 254XXXXXXXXX format
    """
    try:
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, str(phone_number)))

        # Handle different phone number formats
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('7') or phone.startswith('1'):
            phone = '254' + phone

        # Validate final format
        if not (phone.startswith('254') and len(phone) == 12):
            raise ValueError(f"Invalid phone number format: {phone_number}")

        return phone
    except Exception as e:
        logger.error(f"Phone number validation error: {e}")
        raise MPesaError(f"Invalid phone number: {phone_number}")


def get_mpesa_access_token():
    """
    Retrieve MPesa API access token with comprehensive error handling
    """
    # Retrieve credentials securely
    consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', None)
    consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', None)

    if not consumer_key or not consumer_secret:
        logger.error("MPesa credentials are not configured in settings")
        return None

    try:
        # Determine correct URL based on environment
        url = (
            'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
            if settings.MPESA_ENVIRONMENT == 'sandbox'
            else 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        )

        # Detailed logging
        logger.info(f"Attempting to retrieve access token from {url}")
        logger.debug(f"Using Consumer Key (first 5 chars): {consumer_key[:5]}")

        # Make the request
        response = requests.get(
            url,
            auth=(consumer_key, consumer_secret),
            timeout=10,
            headers={
                'User-Agent': 'Django MPesa Integration',
                'Accept': 'application/json'
            }
        )

        # Log full response for debugging
        logger.debug(f"Response Status: {response.status_code}")
        logger.debug(f"Response Headers: {response.headers}")
        logger.debug(f"Response Content: {response.text}")

        # Raise an exception for bad responses
        response.raise_for_status()

        # Parse JSON response
        token_data = response.json()

        # Safely extract access token
        access_token = token_data.get('access_token')

        if not access_token:
            logger.error("No access token found in the response")
            return None

        logger.info("MPesa access token retrieved successfully")
        return access_token

    except requests.RequestException as e:
        logger.error(f"MPesa Access Token Request Failed: {str(e)}")
        return None
    except ValueError as e:
        logger.error(f"JSON Parsing Error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error retrieving access token: {str(e)}")
        return None


def process_mpesa_payment(booking_id):
    """
    Comprehensive payment processing with multiple error checks
    """
    try:
        # Retrieve access token with comprehensive error handling
        access_token = get_mpesa_access_token()

        if not access_token:
            logger.error(f"Failed to retrieve access token for booking {booking_id}")
            return False

        # Additional payment processing logic here
        # Ensure you have comprehensive error handling at each step

    except Exception as e:
        logger.error(f"Payment processing error for booking {booking_id}: {str(e)}")
        return False

def generate_mpesa_password():
    """
    Generate MPesa API password
    """
    # Retrieve from settings to avoid hardcoding
    passkey = getattr(settings, 'MPESA_PASSKEY', None)
    business_shortcode = getattr(settings, 'MPESA_BUSINESS_SHORTCODE', None)

    if not passkey or not business_shortcode:
        raise ImproperlyConfigured(
            "MPESA_PASSKEY and MPESA_BUSINESS_SHORTCODE must be set in settings"
        )

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    # Convert business_shortcode to string before concatenation
    password = base64.b64encode(
        f"{business_shortcode}{passkey}{timestamp}".encode('utf-8')
    ).decode('utf-8')

    return {
        'timestamp': timestamp,
        'password': password
    }
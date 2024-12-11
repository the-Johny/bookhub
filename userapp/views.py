import json
import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt

from bookapp.models import Book, BookGenre, CartItem, Cart, Order, OrderItem, Payment
from .mpesa_utils import (
    get_mpesa_access_token,
    validate_phone_number,
    generate_mpesa_password,
    MPesaError
)


# Create your views here.
def user_home(request):
    # Get the search query from the request
    search_query = request.GET.get('search', '')

    # Filter books based on the search query
    if search_query:
        books = Book.objects.filter(
            Q(title__icontains=search_query) |  # Search by title
            Q(author__icontains=search_query) |  # Search by author
            Q(genre__icontains=search_query)  # Search by genre title
        ).order_by('published_date')
    else:
        books = Book.objects.all().order_by('published_date')

    # Implement pagination
    paginator = Paginator(books, 8)
    page_no = request.GET.get('page')
    page_obj = paginator.get_page(page_no)

    # Pass the search query back to the template to maintain it in the search input
    return render(request, 'home.html', {'page_obj': page_obj, 'search_query': search_query})


def update_profile(request):
    if request.method == 'POST':
        user = request.user

        # Get form data
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        profile_picture = request.FILES.get('profile_picture')

        try:
            # Update user information
            user.fullname = fullname
            user.email = email
            user.phone_number = phone_number


            # Update profile picture if provided
            if profile_picture:
                user.profile_picture = profile_picture

            # Save the updated user
            user.save()

            # Add a success message
            messages.success(request, 'Profile updated successfully.',extra_tags='update_profile')

            # Redirect to the dashboard or a specific URL

            return redirect('profile')

        except ValidationError as e:
            # Handle validation errors
            messages.error(request, str(e))
        except Exception as e:
            # Handle any other unexpected errors
            messages.error(request, 'An error occurred while updating your profile.',extra_tags='update_profile')

    # If not a POST request, redirect to dashboard
    return redirect('dashboard')


logger = logging.getLogger(__name__)
@login_required
def view_cart(request):
    try:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = cart.items.select_related('book').all()

        logger.info(f"Cart created: {created}")
        logger.info(f"User: {request.user}")
        logger.info(f"Cart ID: {cart.id}")
        logger.info(f"Number of items: {cart_items.count()}")

        context = {
            'cart': cart,
            'cart_items': cart_items,
        }
        return render(request, 'view_cart.html', context)
    except Exception as e:
        logger.error(f"Error in view_cart: {str(e)}")
        messages.error(request, "An error occurred while loading your cart")
        return redirect('user-home')


@login_required
def add_to_cart(request):
    if request.method == "POST":
        book_id = request.POST.get('book_id')

        # Validate book_id
        if not book_id:
            messages.error(request, "Invalid book selection")
            return redirect('user-home')

        # Use get with a default of 1 if quantity is not provided
        quantity = int(request.POST.get('quantity', 1))

        # Fetch the book, return 404 if not found
        book = get_object_or_404(Book, id=book_id)

        # Ensure the book is in stock
        if book.stock < quantity:
            messages.error(request, f"Sorry, only {book.stock} copies of {book.title} available.")
            return redirect('user-home')

        # Get or create the user's cart
        cart, created = Cart.objects.get_or_create(user=request.user)

        # Check if the book is already in the cart
        existing_cart_item = cart.items.filter(book=book).first()

        if existing_cart_item:
            # Update quantity if book already exists
            existing_cart_item.quantity += quantity
            existing_cart_item.save()
        else:
            # Create a new cart item
            CartItem.objects.create(
                cart=cart,
                book=book,
                quantity=quantity
            )

        messages.success(request, f"{book.title} added to cart!")
        return redirect('view_cart')

    # Handle non-POST requests
    return redirect('user-home')

@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id)
        cart_item.quantity = int(request.POST.get('quantity', 1))
        cart_item.get_total_price()
        cart_item.save()
    return redirect('view_cart')

@login_required
def remove_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return redirect('view_cart')

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    order = Order.objects.create(user=request.user)
    total_amount = cart.get_total_price()
    for item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            book=item.book,
            quantity=item.quantity,
            price=item.book.price
        )
    cart.items.all().delete()  # Clear the cart after checkout
    return render(request,'process_payment.html',{'order':order,'total_amount':total_amount})


def order_summary(request, order_id):
    # Fetch the order by order_id
    order = get_object_or_404(Order, pk=order_id)

    cart = get_object_or_404(Cart, user=request.user)

    # Fetch associated items for the order (if needed)
    order_items = order.items.all()  # Assuming you have an OrderItem model

    # Render the order summary page
    return render(request, 'order_summary.html', {
        'order': order,
        'order_items': order_items,
    })


def user_profile(request):
    return render(request, 'user_profile.html')

@login_required
def initiate_payment(request, booking_id):
    """
    Initiate MPesa STK Push for payment
    """
    try:
        # Retrieve booking and validate
        booking = get_object_or_404(
            Booking,
            id=booking_id,
            user=request.user,
            status='CONFIRMED'
        )

        # Validate phone number
        phone_number = validate_phone_number(request.user.phone_number)

        # Get access token
        access_token = get_mpesa_access_token()

        # Generate password
        mpesa_credentials = generate_mpesa_password()

        # Prepare STK Push payload
        payload = {
            "BusinessShortCode": settings.MPESA_BUSINESS_SHORTCODE,
            "Password": mpesa_credentials['password'],
            "Timestamp": mpesa_credentials['timestamp'],
            "TransactionType": "CustomerPayBillOnline",
            "Amount": str(int(booking.total_price)),
            "PartyA": phone_number,
            "PartyB": settings.MPESA_BUSINESS_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": f"{settings.MPESA_CALLBACK_BASE_URL}/mpesa/callback/{booking_id}/",
            "AccountReference": f"Booking-{booking_id}",
            "TransactionDesc": f"Payment for Booking {booking_id}"
        }

        # Initiate STK Push
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        response = requests.post(
            'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
            json=payload,
            headers=headers,
            timeout=10
        )

        # Validate response
        if response.status_code == 200:
            payment_details = response.json()

            # Create payment record
            Payment.objects.create(

                booking=booking,
                user=request.user,
                amount=booking.total_price,
                payment_method='MPESA',
                status='PENDING',
                transaction_code=payment_details.get('CheckoutRequestID')
            )

            messages.success(request, "Payment request sent. Please complete payment on your phone.",extra_tags='payment')
            return render(request, 'payment_processing.html', {'booking': booking,'payment_response': payment_details})
        else:
            logger.error(f"STK Push failed: {response.text}")
            messages.error(request, "Payment initiation failed. Please try again.",extra_tags='payment')
            return redirect('my-bookings')

    except MPesaError as e:
        logger.error(f"MPesa Payment Error: {str(e)}")
        messages.error(request, f"Payment error: {str(e)}", extra_tags='payment')
        return redirect('my-bookings')
    except Exception as e:
        logger.error(f"Unexpected payment error: {str(e)}")
        messages.error(request, "An unexpected error occurred. Please try again.",extra_tags='payment')
        return redirect('my-bookings')


@csrf_exempt
def mpesa_payment_callback(request, booking_id):
    """
    Handle MPesa payment callback
    """
    if request.method == 'POST':
        try:
            # Log raw callback data
            raw_data = request.body.decode('utf-8')
            logger.debug(f"Raw Callback Data: {raw_data}")

            # Parse callback data
            callback_data = json.loads(raw_data)
            logger.info(f"Parsed Callback Data: {callback_data}")

            # Extract relevant information
            stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc', 'No description')
            checkout_request_id = stk_callback.get('CheckoutRequestID')

            # Retrieve booking and payment
            booking = get_object_or_404(Booking, id=booking_id)
            payment = get_object_or_404(Payment, booking=booking, transaction_code=checkout_request_id)

            # Process payment based on result code
            if result_code == 0:  # Successful payment
                payment.status = 'SUCCESS'
                payment.receipt_number = None  # Default value until extracted

                # Update booking status
                booking.status = 'PAID'

                # Extract additional transaction details
                metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                for item in metadata:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        payment.receipt_number = item.get('Value')
                    elif item.get('Name') == 'Amount':
                        payment.amount = item.get('Value')
                    elif item.get('Name') == 'TransactionDate':
                        payment.transaction_date = item.get('Value')  # Parse if required
            else:
                payment.status = 'FAILED'
                payment.error_message = result_desc

                # Revert tour availability
                if hasattr(booking, 'tour'):
                    booking.tour.available_slots = max(0, booking.tour.available_slots + booking.slots_booked)
                    booking.tour.save()

            # Save changes
            payment.save()
            booking.save()

            logger.info(f"Payment status updated: {payment.status}, Booking ID: {booking.id}")

            return JsonResponse({
                "status": "success",
                "message": "Callback processed successfully"
            })

        except Booking.DoesNotExist:
            logger.error(f"Booking with ID {booking_id} does not exist.")
            return JsonResponse({"status": "error", "message": "Booking not found."}, status=404)

        except Payment.DoesNotExist:
            logger.error(f"Payment with transaction code {checkout_request_id} does not exist.")
            return JsonResponse({"status": "error", "message": "Payment record not found."}, status=404)

        except json.JSONDecodeError:
            logger.error("Failed to decode JSON from callback data.")
            return JsonResponse({"status": "error", "message": "Invalid JSON format."}, status=400)

        except Exception as e:
            logger.error(f"Callback processing error: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)


def logout(request):
    return render(request, 'logout.html')
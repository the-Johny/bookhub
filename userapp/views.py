import json
import logging
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F
from django.http import JsonResponse
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
            Q(genre__name__icontains=search_query)  # Search by genre title
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
    # 1. Retrieve user's cart
    cart = get_object_or_404(Cart, user=request.user)

    # 2. Create a new order
    order = Order.objects.create(user=request.user)

    # 3. Calculate total amount
    total_amount = cart.get_total_price()

    # 4. Create order items from cart items
    for item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            book=item.book,
            quantity=item.quantity,
            price=cart.get_total_price(),
        )

    # 5. Clear the cart after checkout
    cart.items.all().delete()

    initiate_mpesa_payment(request, order.id)


    # 6. Render payment processing page
    return render(request, 'process_payment.html', {
        'order': order,
        'total_amount': total_amount,

    })


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
def initiate_mpesa_payment(request, order_id):
    try:
        # 1. Retrieve the specific order
        order = get_object_or_404(Order, id=order_id, user=request.user)

        # 2. Calculate total amount
        total_amount = order.items.aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or 0

        # 3. Validate phone number
        phone_number = validate_phone_number(request.user.phone_number)

        # 4. Get MPesa access token
        access_token = get_mpesa_access_token()

        # 5. Generate MPesa credentials (password)
        mpesa_credentials = generate_mpesa_password()

        # 6. Prepare STK Push payload
        payload = {
            "BusinessShortCode": settings.MPESA_BUSINESS_SHORTCODE,
            "Password": mpesa_credentials['password'],
            "Timestamp": mpesa_credentials['timestamp'],
            "TransactionType": "CustomerPayBillOnline",
            "Amount": str(int(total_amount)),
            "PartyA": phone_number,
            "PartyB": settings.MPESA_BUSINESS_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": f"{settings.MPESA_CALLBACK_BASE_URL}/mpesa/callback/{order_id}/",
            "AccountReference": f"Order-{order_id}",
            "TransactionDesc": f"Payment for Order {order_id}"
        }

        # 7. Send STK Push request to MPesa
        response = requests.post(
            'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
            json=payload,
            headers={'Authorization': f'Bearer {access_token}'}
        )

        # 8. If successful, create a payment record
        if response.status_code == 200:
            payment_details = response.json()
            Payment.objects.create(
                user=request.user,
                order=order,
                amount=total_amount,
                payment_method='mpesa',
                status='pending',
                mpesa_checkout_request_id=payment_details.get('CheckoutRequestID'),
                phone_number=phone_number
            )

            # 9. Render payment processing page
            return render(request, 'payment_processing.html', {
                'order': order,
                'payment_response': payment_details
            })

    except Exception as e:
        # Handle any errors during payment initiation
        messages.error(request, "Payment initiation failed")
        return redirect('order_summary', order_id=order_id)


@csrf_exempt
def mpesa_payment_callback(request, order_id):
    if request.method == 'POST':
        try:
            # 1. Receive callback data from MPesa
            callback_data = json.loads(request.body.decode('utf-8'))

            # 2. Extract payment result details
            stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
            result_code = stk_callback.get('ResultCode')
            checkout_request_id = stk_callback.get('CheckoutRequestID')

            # 3. Retrieve corresponding order and payment
            order = get_object_or_404(Order, id=order_id)
            payment = get_object_or_404(
                Payment,
                order=order,
                mpesa_checkout_request_id=checkout_request_id
            )

            # 4. Process payment based on result
            if result_code == 0:  # Successful payment
                payment.status = 'success'
                order.status = 'Paid'

                # Extract additional transaction details
                metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                for item in metadata:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        payment.mpesa_receipt_number = item.get('Value')
            else:
                payment.status = 'failed'
                order.status = 'Payment Failed'

            # 5. Save payment and order status
            payment.save()
            order.save()

            return JsonResponse({"status": "success"})

        except Exception as e:
            # Handle callback processing errors
            return JsonResponse({"status": "error"}, status=500)


def logout(request):
    return render(request, 'logout.html')
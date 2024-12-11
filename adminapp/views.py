from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from bookapp.models import Book, User, BookGenre, Order
from bookapp.forms import BookForm

# Create your views here.
def admin_home(request):
    recent_books = Book.objects.all().order_by('-id')[:5]
    books_count = Book.objects.all().count()
    genres_count = BookGenre.objects.all().count()
    orders_count = Order.objects.all().count()
    client_count = User.objects.all().count()
    context = {'recent_books': recent_books,'books_count':books_count,'genres_count':genres_count,'orders_count':orders_count,client_count:'client_count'}
    return render(request,'admin_home.html',context)

def books_list(request):
    # Search and filter
    query = request.GET.get('q', '')
    genre = request.GET.get('genre', '')

    # Base queryset
    books = Book.objects.all()


    # Apply search filters
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query)
        )

    if genre:
        books = books.filter(genre=genre)

    # Pagination
    paginator = Paginator(books, 5)  # 10 books per page
    page_number = request.GET.get('page', 1)
    books = paginator.get_page(page_number)

    context = {
        'books': books,
        'genres': Book.genre,
        'query': query,
        'selected_genre': genre
    }
    return render(request, 'books-list.html',context)


@login_required
def create_or_update_book(request, book_id=None):
    # If book_id is provided, we're updating an existing book
    if book_id:
        book = get_object_or_404(Book, id=book_id)
        page_title = 'Update Book'
        submit_text = 'Save'
    else:
        book = None
        page_title = 'Create New Book'
        submit_text = 'Submit'

    if request.method == 'POST':
        # Get data from form
        title = request.POST.get('title')
        author = request.POST.get('author')
        description = request.POST.get('description')
        genre_id = request.POST.get('genre')  # Get the genre ID from the form

        # Ensure the genre is selected
        if not genre_id:
            messages.error(request, 'Please select a genre.')
            return redirect(request.path)

        genre = get_object_or_404(BookGenre, id=genre_id)  # Fetch the BookGenre object
        isbn = request.POST.get('isbn')
        publisher = request.POST.get('publisher')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        published_date = request.POST.get('published_date')
        pages = request.POST.get('pages')
        cover_image = request.FILES.get('cover_image')

        # Create or update the book
        if book:
            # Update existing book
            book.title = title
            book.author = author
            book.description = description
            book.genre = genre  # Save the BookGenre object here
            book.isbn = isbn
            book.publisher = publisher
            book.price = price
            book.stock = stock
            book.published_date = published_date
            book.pages = pages

            # Only update image if a new one is provided
            if cover_image:
                book.cover_image = cover_image

            book.save()
            messages.success(request, 'Book updated successfully.')
        else:
            # Create new book
            Book.objects.create(
                title=title,
                author=author,
                description=description,
                genre=genre,  # Save the BookGenre object here
                isbn=isbn,
                publisher=publisher,
                price=price,
                stock=stock,
                published_date=published_date,
                pages=pages,
                cover_image=cover_image
            )
            messages.success(request, 'Book created successfully.')

        return redirect('books-list')

    # For GET request, render the form
    genres = BookGenre.objects.all()
    context = {
        'genres': genres,
        'book': book,
        'page_title': page_title,
        'submit_text': submit_text
    }
    return render(request, 'create_book.html', context)


@login_required
def delete_book(request, book_id):
    book = Book.objects.get(id=book_id)
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Book deleted successfully.')
        return redirect('books-list')

    # Render a confirmation page
    return render(request, 'book_confirm_delete.html', {'book': book})

def manage_customers(request):
    """View a list of customers."""
    customers = User.objects.all().filter(role='USER')
    return render(request, 'clients.html', {'customers': customers})

def view_customer(request, customer_id):
    """View the profile and purchased books of a customer."""
    customer = get_object_or_404(User, pk=customer_id)
    bought_books = User.books.all()
    return render(request, 'clients.html.html', {'customer': customer, 'bought_books': bought_books})


def view_statistics(request):
    """View statistics such as total sales, total customers, and most popular books."""
    total_books = Book.objects.count()
    total_customers = User.objects.count()
    most_popular_books = Book.objects.order_by('-rating')[:5]  # Top 5 popular books based on rating
    total_sales = sum(book.price for book in Book.objects.all())  # Example for total sales

    return render(request, 'admin_home.html', {
        'total_books': total_books,
        'total_customers': total_customers,
        'most_popular_books': most_popular_books,
        'total_sales': total_sales,
    })

def admin_logout(request):
    return render(request,'admin_logout.html')

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


# User Manager
class UserManager(BaseUserManager):
    def create_user(self, email, fullname, phone_number, password=None, role='USER'):
        if not email:
            raise ValueError("Users must have an email address")
        if not phone_number:
            raise ValueError("Users must have a phone number")

        user = self.model(
            email=self.normalize_email(email),
            fullname=fullname,
            phone_number=phone_number,
            role=role,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, fullname, phone_number, password=None):
        user = self.create_user(
            email=email,
            fullname=fullname,
            phone_number=phone_number,
            password=password,
            role='ADMIN',
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


# User Model
class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('USER', 'User'),
        ('ADMIN', 'Admin'),
    )

    fullname = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
            )
        ]
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        default='https://img.freepik.com/free-photo/portrait-father-his-backyard_23-2149489567.jpg'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='USER')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['fullname', 'phone_number']

    def __str__(self):
        return f"{self.email} ({self.role})"

    def has_perm(self, perm, obj=None):
        return self.is_staff or self.role == 'ADMIN' or super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        return self.is_staff or self.role == 'ADMIN' or super().has_module_perms(app_label)


# Book Model
class BookGenre(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Genre name (e.g., Fiction, Non-Fiction)
    genre_code = models.CharField(max_length=50)

    def __str__(self):
        return self.genre_code


def validate_isbn(value):
    isbn = value.replace('-', '')
    if not isbn.isdigit() or len(isbn) != 13:
        raise ValidationError(_('Enter a valid 13-digit ISBN (with optional hyphens).'))


class Book(models.Model):
    title = models.CharField(max_length=200, verbose_name=_('Book Title'), db_index=True)
    author = models.CharField(max_length=200, verbose_name=_('Author Name'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Book Description'))
    genre = models.ForeignKey(BookGenre, on_delete=models.CASCADE)  # Foreign Key to BookGenre
    isbn = models.CharField(max_length=17, unique=True, validators=[validate_isbn], verbose_name=_('ISBN'))
    publisher = models.CharField(max_length=200, verbose_name=_('Publisher'))
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.00)],
                                verbose_name=_('Book Price'))
    cover_image = models.ImageField(upload_to='images/', blank=True, null=True, verbose_name=_('Book Cover'))
    stock = models.PositiveIntegerField(default=0, verbose_name=_('Stock Quantity'))
    published_date = models.DateField(default=timezone.now, verbose_name=_('Publication Date'))
    pages = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5000)],
                                        verbose_name=_('Number of Pages'))
    is_featured = models.BooleanField(default=False, verbose_name=_('Featured Book'))
    rating = models.DecimalField(max_digits=3, decimal_places=1,
                                 validators=[MinValueValidator(0.0), MaxValueValidator(5.0)], null=True, blank=True,
                                 verbose_name=_('Book Rating'))

    class Meta:
        ordering = ['id']
        verbose_name = _('Book')
        verbose_name_plural = _('Books')

    def __str__(self):
        return f"{self.title} by {self.author}"

    def clean(self):
        if self.published_date > timezone.now().date():
            raise ValidationError({'published_date': _('Publication date cannot be in the future.')})

    def is_in_stock(self):
        return self.stock > 0

    def get_discounted_price(self, discount_percentage):
        if not 0 <= discount_percentage <= 100:
            raise ValueError(_("Discount percentage must be between 0 and 100"))
        return round(self.price * (1 - discount_percentage / 100), 2)


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def __str__(self):
        return f"Cart for {self.user.fullname}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)  # Using auto_now_add for consistency

    def get_total_price(self):
        return self.book.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.book.title} in cart"


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')

    def __str__(self):
        return f"Order {self.id} by {self.user.fullname}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total_price(self):
        return self.quantity * self.price


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed')
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    order = models.OneToOneField('Order', on_delete=models.CASCADE,null=True,default=None)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    mpesa_checkout_request_id = models.CharField(max_length=100, null=True, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=20)

    def __str__(self):
        return f"Payment for Order {self.order_id} - {self.status}"
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, fullname, phone_number, password=None, role='USER'):
        if not email:
            raise ValueError("Users must have an email address")

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
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")]
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        default='profile_pictures/default_avatar.jpg'
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='USER')

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='adventure_user_groups',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='adventure_user_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['fullname', 'phone_number']

    def __str__(self):
        return f"{self.email} ({self.role})"

    def has_perm(self, perm, obj=None):
        if self.is_staff or self.role == 'ADMIN':
            return True
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        if self.is_staff or self.role == 'ADMIN':
            return True
        return super().has_module_perms(app_label)


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    cover_image = models.ImageField(upload_to='images/', default='images/default_cover.jpg')
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    published_date = models.DateField()

    def __str__(self):
        return self.title

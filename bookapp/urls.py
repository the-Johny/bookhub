from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('featured-books/', views.featured_books, name='featured'),
    path('popular/', views.popular, name='popular'),
    path('offers/', views.offers, name='offers'),
    path('articles/', views.articles, name='articles'),
    path('register/', views.user_register, name='register'),
    path('login/', views.user_login, name='login'),

]

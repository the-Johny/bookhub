from django.urls import path
from . import views
urlpatterns = [
   path('',views.admin_home,name='admin-home' ),
   path('books-list/', views.books_list, name='books-list'),
   path('create-book/', views.create_or_update_book, name='create-book'),
   path('update-book/<int:book_id>/', views.create_or_update_book, name='update-book'),
   path('delete-book/<int:book_id>/', views.delete_book, name='delete-book'),
   path('manage-customers/', views.manage_customers, name='users-list'),
   path('view-customer/<int:customer_id>/', views.view_customer, name='view-customer'),
   path('statistics/', views.view_statistics, name='statistics'),
   path('admin-logout/', views.admin_logout, name='admin-logout'),
]
from django.urls import path
from . import views

urlpatterns = [
   path('',views.user_home,name='user-home' ),

   path('cart/', views.view_cart, name='view_cart'),
   path('user-home/add-to-cart/', views.add_to_cart, name='add_to_cart'),
   path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
   path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
   path('checkout/', views.checkout, name='checkout'),  # Define checkout functionality separately

   path('initiate-payment/<int:order_id>/', views.initiate_mpesa_payment, name='initiate_mpesa_payment'),
   path('mpesa/callback/<int:order_id>/', views.mpesa_payment_callback, name='mpesa_payment_callback'),

   path('orders/<int:order_id>/', views.order_summary, name='order_summary'),
   path('profile',views.user_profile,name='profile' ),
   path('update-profile/', views.update_profile, name='update_profile'),
   path('logout',views.logout,name='logout' ),
]

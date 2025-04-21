from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('category/<slug:slug>/', views.category_products, name='category_products'),

    # Admin CRUD sản phẩm
    path('admin/products/',views.admin_product_list,   name='admin_product_list'),
    path('admin/products/add/',views.admin_product_create, name='admin_product_create'),
    path('admin/products/<int:pk>/edit/', views.admin_product_update, name='admin_product_update'),
    path('admin/products/<int:pk>/delete/',views.admin_product_delete, name='admin_product_delete'),
    path('orders/',views.order_list,name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
]

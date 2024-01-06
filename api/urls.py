from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('home/', views.home ), 
    path('login/', views.login), 
    path('signup/', views.signup ),
    path('product_description/<int:pk>/', views.product_description),
    path('add_product/', views.add_product),
    path('return_form/', views.return_form),
    path('return_all/<int:item_id>/', views.return_all),
    
]



"""
    #Admin-and-superadmin
    path('admin_views/', views.admin_view, name='admin_views'),
    path('add_product/', views.add_product ,name="Add_product"), 
    path('add_category/', views.add_category, name="Add_category"),
    path('wastage_render/', views.wastage, name='wastage_render'),
    
    #access-denied-page
    path('no_permisson/', views.no_permission, name='no_permission'),
    path('forbidden/', views.custom_forbidden, name='custom_forbidden'),

    #superadmin
    path('users/', views.users_list, name='users_list'),
    # path('appoint_admin/<int:user_id>/', views.appoint_admin, name='appoint_admin'),
    path('remove_role/<int:user_id>/', views.remove_role, name='remove_role'),

    #cart
    path('cart/', views.view_cart, name='view_cart'),

    #Return-form
    path('add_wastage/<int:item_id>/', AddWastageView.as_view(), name="Add_wastage"),
    path('return/<int:item_id>/', AddReturnView.as_view(), name="return"),
    """
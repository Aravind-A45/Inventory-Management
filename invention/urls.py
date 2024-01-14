from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from .views import return_form, AddWastageView, AddReturnView

urlpatterns = [
    #authentication
    path('login/', views.login ,name="login"), 
    path('signup/', views.signup ,name="Register"), 
    path('complete/azuread-tenant-oauth2/home/', views.home ,name="Home"),
    path('logout/', LogoutView.as_view() , name="logout"),

    #Home-Page-And-navbar-page-For-Users
    path('', views.home ,name="Home"), 
    path('about/', views.about , name="About"),
    path('product_description/<int:pk>/', views.product_description, name="Product_description"),

    #Admin-and-superadmin
    path('admin_views/', views.admin_view, name='admin_views'),
    path('wastage_render/', views.wastage, name='wastage_render'),
    
    #Product
    path('add_product/', views.add_product ,name="Add_product"), 
    path('product/', views.view_product, name="product"),
    path('remove_product/<int:pk>/', views.remove_product, name="delete_product"),
    path('edit_product_view/<int:product_id>/', views.edit_product_view , name="edit_product_view"),
 

    #Category
    path('add_category/', views.add_category, name="Add_category"),
    path('category/', views.category, name= "category"),
    path('delete_category/<int:category_id>/', views.remove_category, name="delete_category"),
    path('edit_category/<int:category_id>/', views.edit_category, name="edit_category"),
    

    #Sub-Category
    path('add_subcategory/', views.add_subcategory, name="Add_subcategory"),
    path('delte_subcategory/<int:subcategory_id>/', views.remove_subcategory, name="delete_subcategory"),
    path('edit_subcategory/<int:subcategory_id>/', views.edit_subcategory, name="edit_subcategory"),
    path('sub_category/', views.sub_category, name="sub_category"),

    #access-denied-page
    path('no_permisson/', views.no_permission, name='no_permission'),
    path('forbidden/', views.custom_forbidden, name='custom_forbidden'),

    #superadmin
    path('users/', views.users_list, name='users_list'),
    # path('appoint_admin/<int:user_id>/', views.appoint_admin, name='appoint_admin'),
    path('remove_role/<int:user_id>/', views.remove_role, name='remove_role'),

    #cart
    path('cart/', views.view_cart, name='view_cart'),
    path('add/<int:product_id>', views.add_to_cart, name="add_to_cart"),
    path('remove_from_cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/submit/', views.submit_cart, name='submit_cart'),

    #Return-form
    path('return_form/', views.return_form, name="return_form"),
    path('return_all/<int:item_id>/', views.return_all, name='return_all'),
    path('add_wastage/<int:item_id>/', AddWastageView.as_view(), name="Add_wastage"),
    path('return/<int:item_id>/', AddReturnView.as_view(), name="return"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.contrib import admin
from django.urls import path, include
from . import views
from .views import *

urlpatterns = [
    path('v1/login/', LoginAPIView.as_view(), name='api-v1-login'),

    path('v1/signup/', SignupAPIView.as_view(), name='api-v1-signup'),

    path('v1/home/', HomeAPIView.as_view(), name='api-v1-home'),

    path('v1/product_description/<int:pk>/', ProductDescriptionAPIView.as_view(), name='api-v1-product-description'),

    path('v1/about/', AboutAPIView.as_view(), name="api-v1-about"),

    path('v1/no_permission/', NoPermissionAPIView.as_view(), name='api-v1-no-permission'),

    path('v1/add_to_cart/<int:product_id>/', AddToCartAPIView.as_view(), name='api-v1-add-to-cart'),

    path('v1/view_cart/', ViewCartAPIView.as_view(), name='api-v1-view-cart'),

    path('v1/remove_cart/<int:product_id>/', RemoveCartAPIView.as_view(), name='api-v1-remove-cart'),

    path('v1/submit_cart/', SubmitCartAPIView.as_view(), name='api-v1-submit-cart'),

    path('v1/return_form/', ReturnFormAPIView.as_view(), name='api-v1-return-form'),

    path('v1/return_all/<int:item_id>/', ReturnAllFormAPIView.as_view(), name='api-return-all'),

    path('v1/return_view/<int:item_id>/', AddReturnFormAPIView.as_view(), name='api-return-view'),

    path('v1/return_wastage/<int:item_id>/', AddWastageFormAPIView.as_view(), name='api-wastage-view'),

    path('v1/user_list/', UserlistAPIView.as_view(), name='api-user-list'),

    path('v1/remove_user_list/<int:user_id>/', RemoveAdminAPIView.as_view(), name='api-v1-reomve-admin'),

    path('v1/admin_view/', AdminAPIView.as_view(), name='api-v1-admin-view'),

    path('v1/wastage_view/', WastageAPIView.as_view(), name='api-wastage-view'),

    path('v1/view_product/', ViewProductAPIView.as_view(), name='api-view-product'),

    path('v1/remove_product/<int:pk>/', RemoveProductAPIView.as_view(), name='api-remove-product'),

    path('v1/category_view/', CategoryAPIView.as_view(), name='api-category-view'),

    path('v1/remove_category/<int:category_id>/', RemoveCategoryAPIView.as_view(), name='api-remove-category'),

    path('v1/edit_category/<int:category_id>/', EditCategoryAPIView.as_view(), name='api-edit-category'),

    path('v1/view_sub_category/', ViewSubCategoryAPIView.as_view(), name='api-subcategory-view'),

    path('v1/remove_sub_category/<int:subcategory_id>/', RemoveSubCategoryAPIView.as_view(), name='api-remove-subcategory'),

    path('v1/edit_sub_category/<int:subcategory_id>/', EditSubCategoryAPIView.as_view(), name='api-edit-sub-category'),

    path('v1/edit_product/<int:product_id>/', EditProductAPIView.as_view(), name='api-edit-product-view'),

    path('v1/add_product/', AddProductAPIView.as_view(), name='api-add-product'),

    path('v1/add_category/', AddCategoryAPIView.as_view(), name='api-add-category'),

    path('v1/add_sub_category/', AddSubCategoryAPIView.as_view(), name='api-add-sub-category'),

    path('v1/logout/', LogoutView.as_view(), name='api-logout-view'),
]
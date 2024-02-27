from django.contrib.auth.models import Group,User
from rest_framework import serializers
from invention.models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email']
        
class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model=Group
        fields=['name','permissions']
        
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model=Product
        fields=['name','decription','actual_count','available_count','dummy_count','category','created_at','image']


class LogSerializer(serializers.ModelSerializer):
    product=ProductSerializer()
    class Meta:
        model=Log
        fields=['product','quantity','created_at','status','acting','due_date']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'created_by', 'created_at']
class SubCategorySerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    class Meta:
        models = SubCategory
        fields = ['name_sub', 'category', 'created_by', 'created_at']
class CartSerializer(serializers.ModelSerializer):
    product_name = ProductSerializer()
    class Meta:
        model = Cart
        fields = ['product_name', 'quantity', 'created_by']

    
    
from django.contrib.auth.models import Group,User
from rest_framework import serializers
from invention.models import *


class LoginSerializer(serializers.Serializer):
    rollno = serializers.CharField(required = True)
    password = serializers.CharField(required = True)
    email = serializers.CharField(required = True)

class SignupSerializer(serializers.Serializer):
    rollno = serializers.CharField(required = True)
    password = serializers.CharField(required = True)
    email = serializers.CharField(required = True)
    con_password = serializers.CharField(required = True)



class CategorySerializer(serializers.ModelSerializer):
     class Meta:
          model = Category
          fields = "__all__"

class SubCategorySerializer(serializers.ModelSerializer):
     class Meta:
          model = SubCategory
          fields = "__all__"

class ProductSerializer(serializers.ModelSerializer):
        category = CategorySerializer()
        sub_category = SubCategorySerializer()
        class Meta:
             model = Product
             fields = "__all__"


class CartSerializer(serializers.ModelSerializer):
     product_name = ProductSerializer()
    
     class Meta:
          model = Cart
          fields = "__all__"


class SubmitCartSerializer(serializers.Serializer):
    due_date = serializers.DateField()





class LogSerializer(serializers.ModelSerializer):
     class Meta:
          model = Log
          fields = "__all__"

class AdminSerializer(serializers.ModelSerializer):
     class Meta:
          model = AdminMail
          fields = "__all__"


class PurchasedItemSerializer(serializers.ModelSerializer):
     class Meta:
          model = PurchasedItem
          fields = "__all__"


class CheckedOutLogSerializer(serializers.ModelSerializer):
     class Meta:
          model = CheckedOutLog
          fields = "__all__"
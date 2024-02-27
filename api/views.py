from django.shortcuts import render
from . import serializers
from api.serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User,Group
from rest_framework import status
from invention.models import *
from tablib import Dataset
import pandas as pd
from django.contrib import messages


#login-api
@api_view(['GET','POST'])
def login(request ):
   if request.method == 'GET':
      users = User.objects.all()
      serializer = UserSerializer(users, many=True)
      return Response(serializer.data )
   if request.method=='POST':
      serializer = UserSerializer(data=request.data)
      if serializer.is_valid():
         serializer.save()
         return Response(serializer.data,status=status.HTTP_201_CREATED)
      return Response(serializer.data,status=status.HTTP_400_BAD_REQUEST) 


#Register-api   
@api_view(['GET'])
def signup(request):
   if request.method == 'GET':
      users = User.objects.all()
      group = Group.objects.get(name="student_user")
      serializer1 = UserSerializer(users, many=True)
      serializer2 = GroupSerializer(group)
      serializer ={
         'users':serializer1.data,
         'group':serializer2.data
      }
      return Response(serializer)
   




#Home-page-api
@api_view(['GET'])
def home(request):
   if request.method=='GET':
      products = Product.objects.all()
      serializer= ProductSerializer(products,many=True)
      return Response(serializer.data)
   

#Product-description-api
@api_view(['GET'])
def product_description(request, pk):
   if request.method =="GET":
      item = Product.objects.get(id=pk)
      serializer=ProductSerializer(item)
      return Response(serializer.data)
   

#Add-product-api
@api_view(['POST'])
def add_product(request):
   if request.method=="POST":
      serializer = ProductSerializer(data=request.data)
      if serializer.is_valid():
         serializer.save()
         return Response(serializer.data,status=status.HTTP_201_CREATED)
      return Response(serializer.data,status=status.HTTP_400_BAD_REQUEST)


#return-form-api
@api_view(['GET'])
def return_form(request):
   if request.method == "GET":
      log = Log.objects.all()
      serializer=LogSerializer(log ,many=True)
      return Response(serializer.data)
   

#return-all-api  
@api_view(['GET','POST'])
def return_all(request, item_id):
       
   if request.method=="GET":
      # log=Log.objects.get(id=item_id)
      log=Log.objects.all()
      serializer =LogSerializer(log ,many=True)
      return Response(serializer.data)
        
   if request.method=="POST":
      serializer = LogSerializer(data=request.data)
      if serializer.is_valid():
         serializer.save()
         return Response(serializer.data,status=status.HTTP_201_CREATED)
      return Response(serializer.data,status=status.HTTP_400_BAD_REQUEST)
   

#cart-api
@api_view(['GET', 'POST'])
def cart(request):
   if request.method == "GET":
         cart = Cart.objects.all()
         serializer = CartSerializer(cart, many=True)
         return Response(serializer.data)
   

#own-cart-api
@api_view(['GET', 'POST', 'DELETE'])
def own_cart(request):
    user = request.user
    if request.method == "GET":
        cart = Cart.objects.filter(created_by=user)
        serializer = CartSerializer(cart, many=True)
        return Response(serializer.data)

    elif request.method == "POST":
        serializer = CartSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        item_id = request.data.get('item_id')
        if not item_id:
            return Response({"detail": "Item ID is required for deletion."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cart_item = Cart.objects.get(id=item_id, created_by=user)
            cart_item.delete()
            return Response({"detail": "Item removed from the cart."}, status=status.HTTP_204_NO_CONTENT)
        except Cart.DoesNotExist:
            return Response({"detail": "Item not found in the cart."}, status=status.HTTP_404_NOT_FOUND)
        

#Admin-Add-product-api
# @api_view(['GET','POST'])
# def admin_product(request):
#    if request.method == "GET":
#       product = Product.objects.all()
#       serializer = ProductSerializer(product, many=True)
#       return Response(serializer.data)

#    elif request.method == "POST":
#          if 'form1' in request.data:
#                     file = request.FILES.get('file')
#                     if file.name.endswith('.xlsx'):
#                         try:
#                             df = pd.read_excel(file, sheet_name="Sheet1") 
#                             df = df.drop_duplicates(subset=["name"], keep='first')
#                             for index, row in df.iterrows():
#                                     try:
#                                         try:
#                                                 if not row.isnull().any():
#                                                     category, created = Category.objects.get_or_create(created_by=request.user,name = row['category'])
#                                                     sub_category,created = SubCategory.objects.get_or_create(category = category, name_sub= row['sub_category'], created_by = request.user)

#                                                     product, created = Product.objects.update_or_create(
#                                                         name = row['name'],
#                                                         decription = row['description'],
#                                                         actual_count = row['actual_count'],
#                                                         available_count = row['available_count'],
#                                                         unit_price = row['unit_price'],
#                                                         category = category,
#                                                         sub_category = sub_category,
#                                                         created_by = request.user,
#                                                         actual_price = row['unit_price'] * row['actual_count'],
#                                                         available_price = row['unit_price'] * row['available_count'],
#                                                     )
#                                                     if not created:
#                                                                 return Response({"detail": f'Updated {product}'}, status=status.HTTP_201_CREATED)

#                                                 else:
#                                                     return Response({"detail": f'Error on row {index + 2}: Look up the {row}'}, status=status.HTTP_201_CREATED)
                
#                                         except Exception as e:
#                                                 return Response({"detail": f'Error on row {index + 2}: Look up the {row}'}, status=status.HTTP_201_CREATED)

#                                     except Exception as e:
#                                         return Response({"detail": f'Error on row {index + 2}: Look up the {row}'}, status=status.HTTP_201_CREATED)
#                             return Response({"detail": "Bulk import successful."}, status=status.HTTP_201_CREATED)
                        
#                         except Exception as e:
#                             return Response(f'Error reading the Excel file: {str(e)}', status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
#                     else:
#                         return Response({"detail": "No file provided for bulk import."}, status=status.HTTP_400_BAD_REQUEST)


   



from django.shortcuts import render
from . import serializers
from api.serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User,Group
from rest_framework import status
from invention.models import *


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


@api_view(['GET'])
def home(request):
   if request.method=='GET':
      products = Product.objects.all()
      serializer= ProductSerializer(products,many=True)
      return Response(serializer.data)
   
@api_view(['GET'])
def product_description(request, pk):
   if request.method =="GET":
      item = Product.objects.get(id=pk)
      serializer=ProductSerializer(item)
      return Response(serializer.data)
   
@api_view(['POST'])
def add_product(request):
   if request.method=="POST":
      serializer = ProductSerializer(data=request.data)
      if serializer.is_valid():
         serializer.save()
         return Response(serializer.data,status=status.HTTP_201_CREATED)
      return Response(serializer.data,status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def return_form(request):
   if request.method == "GET":
      log = Log.objects.all()
      serializer=LogSerializer(log ,many=True)
      return Response(serializer.data)
   
   
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


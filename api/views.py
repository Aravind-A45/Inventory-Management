from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import auth
from .serializers import *
import re
from django.contrib.auth.models import Group, User
from invention.models import *
from django.db import transaction
from rest_framework.decorators import api_view
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from invention.decorators import *

@unauthenticated_user
@api_view(['POST'])
def LoginAPIView(request):
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                rollno = serializer.validated_data['rollno']
                password = serializer.validated_data['password']
                email = serializer.validated_data['email']

                try:
                    user = authenticate(username=rollno, password=password, email=email)
                    if user is not None:
                        auth.login(request, user)
                        return Response({'detail': 'logined successful'}, status=status.HTTP_201_CREATED)
                    else:
                        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
                except:
                    return Response({'detail': 'Authentication failed'}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@unauthenticated_user
@api_view(['POST'])
def SignupAPIView(request):
        try:
            serializer = SignupSerializer(data=request.data)
            if serializer.is_valid():
                rollno = serializer.validated_data['rollno']
                password = serializer.validated_data['password']
                con_password = serializer.validated_data['con_password']
                email = serializer.validated_data['email']

                pattern = r'(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[*.!@#$%^&(){}[\]:;<>,.?/~_+-=|\\]).{8,}'


                if re.match(pattern, password):
                        if password == con_password:
                            if User.objects.filter(username = rollno).exists():
                                return Response(f'User with roll numner {rollno} already exits', status=status.HTTP_400_BAD_REQUEST)
                            
                            user = User.objects.create_user(username = rollno, password = password, email = email)
                            admin_group = Group.objects.get(name = 'student_user')
                            user.groups.add(admin_group)
                            return Response({'detail': 'Signed up successfully'}, status=status.HTTP_200_OK)
                        else:
                            return Response({'details': 'Password and confirm Password are not matching.'},status=status.HTTP_400_BAD_REQUEST)
                else:
                        return Response({'details': 'Password not matching the pattern'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=500)

class HomeAPIView(APIView):
    def get(self, request):
        try:
            if request.user.is_authenticated:
                if len(request.user.username)>9:
                    user = get_object_or_404(User, id=request.user.id)
                    admin_group = Group.objects.get(name = 'admin')
                    user.groups.add(admin_group)
                
                products = Product.objects.all()

                cart = Cart.objects.filter(created_by = request.user.id)
                count = cart.count()

                serializer = ProductSerializer(products, many = True)
                return Response({'products': serializer.data, 'count':count}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'You have not correct credential'}, status = status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'detail':str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ProductDescriptionAPIView(APIView):
    def get(self, request, pk):
        try:
            item = Product.objects.get(pk = pk)
            cart = Cart.objects.filter(created_by = request.user)
            count = cart.count()

            serializer = ProductSerializer(item)
            return Response({'item':serializer.data, 'count':count}, status=status.HTTP_200_OK)
               
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class AboutAPIView(APIView):
      def get(self, request):
          try:
              cart = Cart.objects.filter(created_by = request.user)
              count = cart.count()
              
              return Response({'count':count}, status=status.HTTP_200_OK)
          except Exception as e:              
               return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
          

class NoPermissionAPIView(APIView):
   def get(self, request):   
      try:
          return render(request, 'core/no_permission.html')
      except:
          return render(request, 'core/no_permission.html')
      

class AddToCartAPIView(APIView):
    def get(self, request, product_id):
        try:
            products = Product.objects.all()
            cart = Cart.objects.filter(created_by = request.user)
            count = cart.count()
            if products:
                product_serializer = ProductSerializer(products, many = True)
                return Response({'detail': 'Product details', 'Products': product_serializer.data}) 
            else:
                return Response({'detail': 'There is No products'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self, request, product_id):
         try:
             product = Product.objects.select_for_update().get(id = product_id)
             if product.available_count == 0:
                 return Response({'detail': 'Invalid Available Count'}, status=status.HTTP_400_BAD_REQUEST)
             
             quantity = request.data.get('count')
             if quantity is not None:
                 try:
                     quantity_int = int(quantity)
                     if 0 < quantity_int <= product.available_count:
                         with transaction.atomic():
                             add = 0
                             try:
                                 cart = Cart.objects.get(product_name = product, created_by = request.user)
                                 add = cart.quantity
                                 add += quantity_int
                                 cart.quantity = add
                                 if add > product.available_count:
                                     return Response({'detail': 'Not Enough Quantity'}, status=status.HTTP_400_BAD_REQUEST)
                                 cart = Cart.objects.get(product_name = product, created_by = request.user).delete()
                                 Cart.objects.create(product_name = product, quantity = add, created_by = request.user)
                                 return Response({'detail':'Added to the Cart'}, status=status.HTTP_200_OK)
                             except:
                                 Cart.objects.create(product_name = product, quantity = quantity_int, created_by = request.user)
                     else:
                        return Response({'detail':'Look up the Quantity'}, status=status.HTTP_204_NO_CONTENT)
                 except:
                    return Response({'detail': 'Invalid Quantity'}, status=status.HTTP_400_BAD_REQUEST)
                 return Response({'detail': 'Add to the cart'}, status=status.HTTP_200_OK)
                
                 
         except Exception as e:
             return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    


class ViewCartAPIView(APIView):
    def get(self, request):
        try:
            cart = Cart.objects.filter(created_by = request.user)
            print(cart)
            product = Product.objects.all()
            category = Category.objects.all()
            count = cart.count()

            cart_serializer = CartSerializer(cart, many = True)
            product_serializer = ProductSerializer(product, many = True)
            category_serializer = CategorySerializer(category, many = True)
            print(cart_serializer, product_serializer,category_serializer )

            return Response({'cart_items':cart_serializer.data, 'count':count}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RemoveCartAPIView(APIView):
    def get(self, request,product_id):
        try:
            cart = Cart.objects.filter(created_by = request.user)
            if cart:
                count = cart.count()
                cart_serializer = CartSerializer(cart, many = True)
                return Response({'cart_items':cart_serializer.data, 'count':count}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'There is no items to remove in cart'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def delete(self, request, product_id):
        try:
            cart = Cart.objects.get(id=product_id, created_by=request.user.id)
            cart.delete()
            return Response({'detail': 'Successfully removed from the cart'}, status=status.HTTP_200_OK)

        except Cart.DoesNotExist:
            return Response({'detail': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 

class SubmitCartAPIView(APIView):
    def get(self, request):
        try:
            permission_classes = [IsAuthenticated]
            cart = Cart.objects.filter(created_by = request.user)
            count = cart.count()

            cart_serializer = CartSerializer(cart, many = True)

            return Response({'cart_items':cart_serializer.data,'count':count}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request):
        try:
            serializer = SubmitCartSerializer(data = request.data)
            if serializer.is_valid():
                due_date = serializer.validated_data['due_date']
                cart_items = Cart.objects.filter(created_by=request.user.id)
                with transaction.atomic():
                    if cart_items:
                        for cart_item in cart_items:
                            statuss = 'checked_in'
                            product = Product.objects.get(name = cart_item.product_name)
                            if(product.available_count - cart_item.quantity) < 0:
                                Cart.objects.filter(created_by = request.user).delete()
                                return Response({'detail': 'Not Enough Quantity'}, status=status.HTTP_400_BAD_REQUEST)
                            else:
                                Product.objects.filter(name = cart_item.product_name).update(available_count =F('available_count')-cart_item.quantity)
                                PurchasedItem.objects.create(product = cart_item.product_name, quantity = cart_item.quantity, user = request.user, status = statuss, date_added = datetime.datetime.now(), due_date = due_date)
                                Log.objects.create(product = cart_item.product_name, quantity = cart_item.quantity, user = request.user, status = status, created_at = datetime.datetime.now(), due_date = due_date)
                                Cart.objects.filter(created_by = request.user).delete()
                        cart_items.delete()    
                        return Response({'detail': 'Cart submitted successfully'}, status=status.HTTP_200_OK)
                    else:
                        return Response({'detail': 'Cart has zero items'}, status=status.HTTP_400_BAD_REQUEST)

            else:
                return Response({'detail': 'Give the date correctly'}, status=status.HTTP_400_BAD_REQUEST) 
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ReturnFormAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            purchased_items = Log.objects.filter(user = user) 
            if purchased_items:
               
                serializer = LogSerializer(purchased_items, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'There is no items are to be return'}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ReturnAllFormAPIView(APIView):
      def get(self, request,item_id):
        try:
            user = request.user
            purchased_items = Log.objects.filter(user = user) 
            if purchased_items:
               
                serializer = LogSerializer(purchased_items, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'There is no items are to be return'}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
      
      def post(self, request,item_id):
        try:
            item = Log.objects.get(pk = item_id)
            if item:
                product = item.product

                item.status = 'checked_in'
                item.save()

                CheckedOutLog.objects.create(product = product, quantity = item.quantity, user = request.user, status = "checked_out")
                product.available_count += item.quantity
                product.save()
                item.delete()
                return Response({'detail': 'All Items are Returned'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail':'There is no item to return'}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class AddReturnFormAPIView(APIView):
    def get(self, request,item_id):
        try:
            user = request.user
            purchased_items = Log.objects.filter(user = user) 
            if purchased_items:
               
                serializer = LogSerializer(purchased_items, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'There is no items are to be return'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self, request, item_id):
        try:
            item = get_object_or_404(Log, id=item_id)
            if item:
                return_quantity = request.data.get("return_qty")
                if (return_quantity is not None and str(return_quantity).isdigit() and int(return_quantity) <= item.quantity and int(return_quantity) > 0):
                    product = item.product
                    return_quantity = int(return_quantity)
                    quantity = return_quantity
                    item.quantity -= return_quantity
                    item.save()
                    product.available_count += quantity
                    product.save()
                    if item.quantity == 0:
                        item.delete()
                        return Response({'detail': 'Item returned successfully'}, status=status.HTTP_200_OK)  
                    return Response({'detail': 'Item returned successfully'}, status=status.HTTP_200_OK)
                else:
                    return Response({'detail': 'Invalid return quantity'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'detail': 'Items are not found'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AddWastageFormAPIView(APIView):
    def get(self, request,item_id):
        try:
            user = request.user
            purchased_items = Log.objects.filter(user = user) 
            if purchased_items:
               
                serializer = LogSerializer(purchased_items, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'There is no items are to be return'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request, item_id):
        try:
            item = Log.objects.get(id = item_id)
            if item:
                damaged_quantity = request.data.get('damaged_qty')
                reason = request.data.get('reason')
                products  = Product.objects.all()
                if damaged_quantity is not None and str(damaged_quantity).isdigit() and int(damaged_quantity) <= item.quantity and int(damaged_quantity) > 0 and reason:
                    damaged_quantity = int(damaged_quantity)
                    item.quantity -= damaged_quantity
                    item.save()
                    Wastage.objects.create(user=request.user,product_name=item.product,quantity=damaged_quantity,reason=reason,category=item.product.category)

                    for product in products:
                        if item.product.name == product.name:
                            s = damaged_quantity * product.unit_price
                            product.available_price = product.available_price - s
                            product.save()
                        if item.quantity == 0:
                            item.delete()
                            return Response({'detail':'Items are deleted'}, status=status.HTTP_100_CONTINUE)
                    return Response({'detail': 'Items are deleted'}, status=status.HTTP_200_OK)
                else:
                    return Response({'detail': 'Invalid Input'},  status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'detail': 'There is No items'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserlistAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            if user.groups.filter(name = 'superadmin').exists():
                admin = AdminMail.objects.all()

                serializers = AdminSerializer(admin, many = True)

                return Response({'detail': 'Admin Mail Ids', 'admins':serializers.data}, status=status.HTTP_200_OK)
               
            else:
                return Response({'detail': 'You are not belongs to this group'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self, request):
        try:
            users = User.objects.all()
            admins = AdminMail.objects.all()
            pattern= r"^[a-zA-Z0-9_.]+@(kct\.)+(ac\.)+in$"
            email = request.data.get("email")
            if re.match(pattern, email):
                for i in admins:
                    if email == i.mail:
                        return Response({'detail': 'Microsoft Mail-id already exists'}, status=status.HTTP_100_CONTINUE)
                admin_group = Group.objects.get(name = 'admin')
                user  = User.objects.get(email = email)
                student_user_group = Group.objects.get(name = 'student_user')
                user.groups.remove(student_user_group)
                user.groups.add(admin_group)
                AdminMail.objects.create(mail = email)
            cart=Cart.objects.filter(created_by=request.user)
            count = cart.count()
            return Response({'detail':'Admin is added'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class RemoveAdminAPIView(APIView):
    def get(self, request, user_id):
        try:
            user = request.user
            if user.groups.filter(name = 'superadmin').exists():
                admin = AdminMail.objects.all()
                serializers = AdminSerializer(admin, many = True)

                return Response({'detail': 'Admin Mail Ids', 'admins':serializers.data}, status=status.HTTP_200_OK)
               
            else:
                return Response({'detail': 'You are not belongs to this group'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request, user_id):
        try:
            user = request.user
            if user.groups.filter(name = 'superadmin').exists():
                AdminMail.objects.filter(id = user_id).delete()
                return Response({'detail': 'Admin is removed from the role'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'You are not belongs to this group'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class AdminAPIView(APIView):
    def get(self, request):
        try:
            log  = Log.objects.all()
            purchased_items = PurchasedItem.objects.all()
            checked_out_log = CheckedOutLog.objects.all()
            cart = Cart.objects.filter(created_by = request.user)
            count = cart.count()
            user = request.user
            if log or purchased_items and user.groups.filter(name = 'admin').exists():

                log_serializer = LogSerializer(log, many = True)
                Purchased_items_serializer = PurchasedItemSerializer(purchased_items, many=True)
                checked_out_log_serialzer = CheckedOutLogSerializer(checked_out_log, many = True)

                return Response({'detail': "Log details", 'Checked_in_logs': Purchased_items_serializer.data, 'Checked_out_log': checked_out_log_serialzer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': "Log details doesn't Exist"},status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class WastageAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            purchased_items = Log.objects.filter(user = user) 
            if purchased_items:
                serializer = LogSerializer(purchased_items, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'There is no items are to be return'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   

class ViewProductAPIView(APIView):
    def get(self, request):
        try:
            products = Product.objects.all()
            cart = Cart.objects.filter(created_by = request.user)
            count = cart.count()
            if products:
                product_serializer = ProductSerializer(products, many = True)
                return Response({'detail': 'Product details', 'Products': product_serializer.data}) 
            else:
                return Response({'detail': 'There is No products'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class RemoveProductAPIView(APIView):
    def get(self, request, pk):
        try:
            products = Product.objects.all()
            cart = Cart.objects.filter(created_by = request.user)
            count = cart.count()
            if products:
                product_serializer = ProductSerializer(products, many = True)
                return Response({'detail': 'Product details', 'Products': product_serializer.data}) 
            else:
                return Response({'detail': 'There is No products'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, pk):
        try:
            product = Product.objects.get(pk = pk)
            user = request.user
            if product and user.groups.filter(Q(name = 'admin') |Q(name = 'superadmin')):
                product.delete()
                return Response({'detail': 'The Product is deleted'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': "The Product is dosn't exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class CategoryAPIView(APIView):
    def get(self, request):
        try:
            categories = Category.objects.all()
            cart = Cart.objects.filter(created_by = request.user)
            count = cart.count()

            category_serializer = CategorySerializer(categories, many = True)
            return Response({'detail': 'Category view', 'categories': category_serializer.data},status= status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RemoveCategoryAPIView(APIView):
     def get(self, request, category_id):
        try:
            categories = Category.objects.all()
            cart = Cart.objects.filter(created_by = request.user)
            count = cart.count()

            category_serializer = CategorySerializer(categories, many = True)
            return Response({'detail': 'Category view', 'categories': category_serializer.data},status= status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
     def delete(self, request, category_id):
         try:
             category = Category.objects.get(id = category_id)
             if category:
                category.delete()
                return Response({'detail': 'Category is removed'}, status=status.HTTP_200_OK)
             else:
                 return Response({'detail': "Category doesn't Exist."}, status=status.HTTP_400_BAD_REQUEST)
         except Exception as e:
             return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EditCategoryAPIView(APIView):
    def get(self, request, category_id):
        try:
            categories = Category.objects.all()
            cart = Cart.objects.filter(created_by = request.user)
            count = cart.count()

            category_serializer = CategorySerializer(categories, many = True)
            return Response({'detail': 'Category view', 'categories': category_serializer.data},status= status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, category_id):
        try:
            category = Category.objects.get(id = category_id)
            new_category_name = request.data.get('name')
            if new_category_name:
                category.name = new_category_name
                category.save()
                return Response({'detail': 'Category Updated.'}, status=status.HTTP_200_OK)
            cart = Cart.objects.filter(created_by = request.user)
            count = cart.count()
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ViewSubCategoryAPIView(APIView):
        def get(self, request):
            try:
                sub_categories = SubCategory.objects.all()
                cart = Cart.objects.filter(created_by = request.user)
                count = cart.count()

                sub_category_serializer = SubCategorySerializer(sub_categories, many = True)
                return Response({'detail': 'Sub Category view', 'categories': sub_category_serializer.data},status= status.HTTP_200_OK)
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RemoveSubCategoryAPIView(APIView):
    def get(self, request, subcategory_id):
            try:
                sub_categories = Category.objects.all()
                cart = Cart.objects.filter(created_by = request.user)
                count = cart.count()

                sub_category_serializer = SubCategorySerializer(sub_categories, many = True)
                return Response({'detail': 'Sub Category view', 'categories': sub_category_serializer.data},status= status.HTTP_200_OK)
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    def delete(self, request, subcategory_id):
         try:
             sub_category = SubCategory.objects.get(id = subcategory_id)
             if sub_category:
                sub_category.delete()
                return Response({'detail': 'SubCategory is removed'}, status=status.HTTP_200_OK)
             else:
                 return Response({'detail': "SubCategory doesn't Exist."}, status=status.HTTP_400_BAD_REQUEST)
         except Exception as e:
             return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
         
class EditSubCategoryAPIView(APIView):
    def get(self, request, subcategory_id):
            try:
                sub_categories = SubCategory.objects.all()
                cart = Cart.objects.filter(created_by = request.user)
                count = cart.count()

                sub_category_serializer = SubCategorySerializer(sub_categories, many = True)
                return Response({'detail': 'Sub Category view', 'categories': sub_category_serializer.data},status= status.HTTP_200_OK)
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self, request, subcategory_id):
        try:
            sub_category = SubCategory.objects.get(id = subcategory_id)
            new_sub_category_name = request.data.get('name') 
            print(new_sub_category_name)
            if new_sub_category_name:
                cat=request.data.get("category")
                category=Category.objects.get(name=cat)
                sub_category.name_sub = new_sub_category_name
                sub_category.category = category
                sub_category.save()
                return Response({'detail':'SubCategory Updated'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'SubCategory Not Created'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class AddProductAPIView(APIView):
    def get(self, request):
        try:
            products = Product.objects.all()
            cart = Cart.objects.filter(created_by = request.user)
            count = cart.count()
            if products:
                product_serializer = ProductSerializer(products, many = True)
                return Response({'detail': 'Product details', 'Products': product_serializer.data}) 
            else:
                return Response({'detail': 'There is No products'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request):
        try:
            product_name = request.data.get("name")
            decription = request.data.get("description")
            actual_count = request.data.get("actual_quantity")
            available_count = request.data.get("available_quantity")
            image = request.data.get("image")
            cat=request.data.get("category")
            print(cat)
            category=Category.objects.get(name=cat)
            sub = request.data.get('sub_category')
            print(sub)
            sub_category = SubCategory.objects.get(name_sub=sub) 
            unit_price = request.data.get('unit_price')
            print("Category", cat, "sub_category", sub)
            a_price = int(unit_price) * int(available_count)
            ac_price = int(unit_price) * int(actual_count)
            if int(actual_count) >= int(available_count):
                try:
                    if Product.objects.filter(name = product_name).exists():
                         return Response({'detail': 'Product was Already Exists'}, status=400)
                    else:
                        Product.objects.create(created_by = request.user, name = product_name, decription = decription, actual_count = actual_count, available_count = available_count,image = image, category = category, sub_category = sub_category, unit_price = unit_price, actual_price = ac_price, available_price = a_price)

                        return Response({'detail'
                                        : 'Product was Created', }, status=status.HTTP_200_OK)
                       
                except Exception as e:
                    return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            else:

                return Response({'detail': 'Look up the Available Quantity'}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EditProductAPIView(APIView):
    def get(self, request, product_id):
        try:
            products = Product.objects.all()
            cart = Cart.objects.filter(created_by = request.user)
            count = cart.count()
            if products:
                product_serializer = ProductSerializer(products, many = True)
                return Response({'detail': 'Product details', 'Products': product_serializer.data}) 
            else:
                return Response({'detail': 'There is No products'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request, product_id):
        try:
            product = Product.objects.get(pk = product_id)
            print(product)
            cart = Cart.objects.filter(created_by = request.user)
            count = cart.count()

            if product:
                product_name = request.data.get('name')
                decription = request.data.get('description')
                unit_price = request.data.get('unit_price')
                curr_qty = request.data.get('current_quantity')
                available_qty = request.data.get('available_quantity')
                actual_qty = request.data.get('actual_quantity')

                product.is_active = not product.is_active
                if curr_qty is not None:
                    c_qty = int(curr_qty)
                else:
                    c_qty = 0

                if unit_price is not None:
                    unit_price = unit_price
                else:
                    unit_price = product.unit_price

                if actual_qty is not None:
                    actual_Q = int(actual_qty)
                else:
                    actual_Q = product.actual_count

                if available_qty is not None:
                    available_Q = int(available_qty)
                else:
                    available_Q = product.available_count
            
                product.actual_count = actual_Q
                product.available_count = available_Q

                a_stock = c_qty + product.available_count
                actual_stock = c_qty + product.actual_count

                a_price = float(unit_price) * float(a_stock) 
                ac_price = float(unit_price) * float(actual_stock)

                cat=request.data.get("category")
                category=Category.objects.get(name=cat)
                sub = request.data.get('sub_category')
                sub_category = SubCategory.objects.get(name_sub=sub) 
                
                if(a_stock <= actual_stock):
                        product.name = product_name
                        product.decription = decription
                        product.unit_price = unit_price
                        product.available_count = a_stock
                        product.available_price = a_price
                        product.actual_count = actual_stock
                        product.actual_price = ac_price
                        product.category = category
                        product.sub_category = sub_category
                        product.is_active = True
                        product.save()

                        return Response({'detail': 'Product is Updated'}, status=status.HTTP_200_OK)
                else:
                    return Response({'detail': 'Product is not updated and look up the quantity'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'detail': 'Product Does not Exist'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)},  status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class AddCategoryAPIView(APIView):
     def get(self, request):
        try:
            categories = Category.objects.all()
            cart = Cart.objects.filter(created_by = request.user)
            count = cart.count()

            category_serializer = CategorySerializer(categories, many = True)
            return Response({'detail': 'Category view', 'categories': category_serializer.data},status= status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
     def post(self, request):
         try:
             name = request.data.get('name')
             if Category.objects.filter(name = name).exists():
                return Response({'detail': 'The Category Already Exists'}, status=status.HTTP_400_BAD_REQUEST)
             else:
                 Category.objects.create(name = name, created_by = request.user)
                 return Response({'detial': 'Category is Created'}, status=status.HTTP_200_OK)
         except Exception as e:
             return Response({'detail': str(e)}, status=500)


class AddSubCategoryAPIView(APIView):
    def get(self, request):
        try:
            categories = SubCategory.objects.all()
            cart = Cart.objects.filter(created_by = request.user)
            count = cart.count()

            sub_category_serializer = SubCategorySerializer(categories, many = True)
            return Response({'detail': 'Category view', 'categories': sub_category_serializer.data},status= status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
         try:
             name = request.data.get('name')
             if SubCategory.objects.filter(name_sub = name).exists():
                
                return Response({'detail': 'The SubCategory Already Exists'}, status=status.HTTP_400_BAD_REQUEST)
             else:
                cat=request.data.get("category")
                category=Category.objects.get(name=cat)
                SubCategory.objects.create(name_sub = name, category = category, created_by = request.user)
                return Response({'detial': 'SubCategory is Created'}, status=status.HTTP_200_OK)
         except Exception as e:
             return Response({'detail': str(e)}, status=500)
         

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            logout(request)
            return Response({'detail': 'Logout Successfull'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
        
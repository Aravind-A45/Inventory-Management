import re
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.shortcuts import render,redirect, get_object_or_404
from .models import *
import sweetify
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .decorators import *
from django.contrib.auth.models import Group, User
from django.http import HttpResponseRedirect, JsonResponse
from collections import defaultdict
from django.views import View
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from .tasks import send_notification_mail
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.http import HttpResponse
from .tasks import send_notification_mail
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import datetime
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.decorators import api_view, APIView
from django.db import transaction
from django_ratelimit.decorators import ratelimit
from django.conf import settings
from tablib import Dataset
import pandas as pd
from django.core.exceptions import *
from django.utils.decorators import method_decorator
from .models import *
from django.utils import timezone
from django import template


#rest_api
from rest_framework.decorators import api_view
from rest_framework.response import Response    
# Create your views here.

#bulk import
from .tasks import *



def new_login(request):
    return render(request, 'credential/new_login.html')

def excel(request):
    print("hii")
    error_message = None
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        file_obj = File.objects.create(file=uploaded_file)
        messages.info(request, "File uploaded")
        task_result = process_excel_file.delay(file_obj.id)
        if isinstance(task_result.result, str):
            error_message = task_result.result

    return render(request, 'adminview/add_product.html', {'error_message': error_message})

  
def form_valid(self, form):
        email = form.cleaned_data["email"]
        message = form.cleaned_data["message"]
        send_notification_mail.delay(email,message)
        return HttpResponse('We have sent you a confirmation mail!')

# Microsoft-Authentication-View-Only-For-Admin
def restrict_user_pipeline(strategy, details, user=None, is_new=False, *args, **kwargs):
    email=AdminMail.objects.all()
    allowed_emails = []
    for e in email:
        allowed_emails.append(e.mail)
        
    if user:
         return ('')
    return {'details': details, 'user': user, 'is_new': is_new}

def custom_forbidden(request):
    if request.method=="POST":
        return redirect('login')
    return render(request, 'custom_forbidden.html')


#Home-Page
@login_required(login_url= 'login')
def home(request):
    try:
        products = Product.objects.all()
        cart = Cart.objects.filter(created_by=request.user)
        count = cart.count()
        admin_group = request.user.groups.filter(name="admin").exists()
        super_admin_group = request.user.groups.filter(name='superadmin').exists()
        name = request.user.username
        user = name[-8:]
        if not admin_group or not super_admin_group:
            customer = request.user
            admin = Group.objects.get(name = 'student_user')
            customer.groups.add(admin)
        return render(request, 'core/home.html', {'products': products, 'count': count, 'admin_group': admin_group, 'super_admin_group': super_admin_group, 'name': user})
    
    except ObjectDoesNotExist:
        return render(request, 'core/home.html', {'detail':'There is No Product here!..'})
    
    


#View-Product-Details-As-View-Details
@login_required(login_url='login')
def product_description(request, pk):
    try:
        item = Product.objects.get(pk =pk)
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        return render(request, 'core/product_description.html', {'item':item, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})
    
    except ObjectDoesNotExist:
         return render(request, 'core/product_description.html', {'detail': 'There is No Product here!..'})


#About-Page
@login_required(login_url='login')
def about(request):
    try:
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()    
        name = request.user.username
        user = name[-8:]
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        return render(request, 'core/about.html', {'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})
    except ObjectDoesNotExist:
         return render(request, 'core/about.html', {})
    


#Access-Denied-Page
def no_permission(request):
        return render(request, 'core/no_permission.html')

#Cart Functionality

#Add-To-Cart
# temporary_cart = defaultdict(int)
@login_required(login_url='login')
def add_to_cart(request, product_id):
    try:
        with transaction.atomic():
            product = Product.objects.select_for_update().get(id=product_id)
            if product.available_count == 0:
                messages.info(request, 'There is no available stock for this product.')
                return redirect('Home')
                
            if request.method == "POST":
                quantity = request.POST.get("count")
                if quantity is not None: 
                    try:
                        quantity_int = int(quantity)
                        if 0 < quantity_int <= product.available_count:
                            add = 0
                            try:
                                cart = Cart.objects.select_for_update().get(product_name=product, created_by=request.user)
                                add = cart.quantity
                                add += quantity_int
                                if add > product.available_count:
                                    messages.warning(request, "Not enough quantity available.")
                                    return redirect('Home')
                                cart.quantity = add
                                cart.save()
                            except Cart.DoesNotExist:
                                Cart.objects.create(product_name=product, quantity=quantity_int, created_by=request.user)
                        else:
                            messages.warning(request, "Please choose a valid quantity.")
                    except ValueError:
                        return HttpResponse("Invalid quantity")
                    sweetify.success(request, 'You are successfully added to the cart', button="OK") 
            return redirect('Home')
    except Product.DoesNotExist:
        messages.error(request, 'The product does not exist.')
        return redirect('Home')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('Home')

#View-Cart
@login_required(login_url='login')
def view_cart(request):
    try:
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        product=Product.objects.all()
        category=Category.objects.all()
        name = request.user.username
        user = name[-8:]
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        return render(request, 'cart/cart.html', {'cart_items':cart,'product':product,'category':category, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})
    except ObjectDoesNotExist:
         return render(request, 'cart/cart.html', {})
    
#Remove-Cart
@login_required(login_url='login')
def remove_from_cart(request, product_id):
    try:
        cart=Cart.objects.get(id=product_id,created_by=request.user)
        cart.delete()
        sweetify.success(request, 'The Item is removed from your cart.',button="OK")
    except cart.DoesNotExist:
        sweetify.warning(request, 'The Item is not found in the Cart', button = "OK")

    return redirect('view_cart')



#Submit-In-Cart
@login_required(login_url='login')
def submit_cart(request):
    if request.method == "POST":
        due_date = request.POST.get('due_date')
        try:
            with transaction.atomic():
                for cart in Cart.objects.filter(created_by=request.user):
                    status = 'checked_in'
                    item = Product.objects.get(name=cart.product_name)
                    if (item.available_count - cart.quantity) < 0:
                        messages.warning(request, "Not enough quantity available for " + cart.product_name + ". Please remove it from your cart.")
                        return redirect('view_cart')
                    else:
                        Product.objects.filter(name=cart.product_name).update(available_count=F('available_count') - cart.quantity)
                        PurchasedItem.objects.create(product=cart.product_name, quantity=cart.quantity, user=request.user, status=status, date_added=timezone.now(), due_date=due_date)
                        Log.objects.create(product=cart.product_name, quantity=cart.quantity, user=request.user, status=status, created_at=timezone.now(), due_date=due_date)
                Cart.objects.filter(created_by=request.user).delete()
                messages.success(request, "Cart submitted successfully.")
        except Product.DoesNotExist:
            messages.error(request, "Product does not exist.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    return redirect("Home")



#Return-Form-View
@login_required(login_url='login')
def return_form(request):
    try:
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        purchased_items = Log.objects.filter(user = request.user) 
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        return render(request, 'cart/return_form.html', {'purchased_items':purchased_items, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})
    except ObjectDoesNotExist:
         return render(request, 'cart/return_form.html', {})



#Return-All
@login_required(login_url='login')
def return_all(request, item_id):
    try:
        item = get_object_or_404(Log, pk=item_id)
        product = item.product
        item.status = 'checked_in'
        item.save()
        CheckedOutLog.objects.create(product=product, quantity=item.quantity, user=request.user, status="checked_out")
        product.available_count += item.quantity
        product.save()
        item.delete()

        messages.success(request, "Item returned successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        messages.error(request, "An error occurred while processing your request. Please try again later.")

    return redirect('return_form')
    

#Return One-By-One Form
@method_decorator(login_required, name="dispatch")
class AddReturnView(View):
    def get(self, request, item_id):
        try:
            categories = Category.objects.all()
            products = Log.objects.all()
            cart = Cart.objects.filter(created_by=request.user)
            count = cart.count()
            item = get_object_or_404(Log, id=item_id)
            admin_group = request.user.groups.filter(name="admin").exists()
            name = request.user.username
            user = name[-8:]
            super_admin_group = request.user.groups.filter(name="superadmin").exists()
            return render(
                request,
                'cart/return.html',
                {'categories': categories, 'products': products, 'item': item, 'count': count, 'admin_group': admin_group, 'super_admin_group': super_admin_group, 'name': user}
            )
        except ObjectDoesNotExist:
             messages.error(request,"An error occurred while processing your request. Please try again later.")
             return render(request, 'error.html')
        except Exception as e:
            print(f"An error occurred: {e}")
            return render(request, 'error.html')
        
    def post(self, request, item_id):

            categories = Category.objects.all()
            products = Log.objects.all()
            item = get_object_or_404(Log, id=item_id)
            
            return_quantity = request.POST.get("return_qty")

            if return_quantity is not None and return_quantity.isdigit() and int(return_quantity) <= item.quantity and int(return_quantity) > 0:
                product = item.product
                return_quantity = int(return_quantity)
                quantity =  return_quantity
                item.quantity -= return_quantity
                item.save()
                product.available_count += quantity
                product.save()

                CheckedOutLog.objects.create(product=product, quantity=return_quantity, user=request.user, status="checked_out")

                if item.quantity == 0:
                    item.delete()
                    return redirect('return_form')
                if item:
                    return redirect('return_form')
            else:
                pass
            
            cart=Cart.objects.filter(created_by=request.user)
            count = cart.count()
            admin_group = request.user.groups.filter(name = "admin").exists()
            super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
            name = request.user.username
            user = name[-8:]
            return render(
                request,
                'cart/return.html',
                {'categories': categories, 'products': products, 'item': item, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user}
            )



#Damaged-Form
@method_decorator(login_required, name="dispatch")
class AddWastageView(View):
    def get(self, request, item_id):
        try:
            categories = Category.objects.all()
            products = Log.objects.all()
            item = Log.objects.get(id = item_id)
            cart = Cart.objects.filter(created_by=request.user)
            count = cart.count()
            admin_group = request.user.groups.filter(name="admin").exists()
            super_admin_group = request.user.groups.filter(name="superadmin").exists()
            name = request.user.username
            user = name[-8:]

            return render(
                request,
                'cart/wastage.html',
                {'categories': categories, 'products': products, 'item': item, 'count': count, 'admin_group': admin_group, 'super_admin_group': super_admin_group, 'name': user}
            )

        except ObjectDoesNotExist:
            messages.error(request, "Requested item does not exist.")
            return redirect('return_form')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('return_form')
    

    def post(self, request, item_id):
        try:
            categories = Category.objects.all()
            products = Log.objects.all()
            item = get_object_or_404(Log, id=item_id)
            products = Product.objects.all()
            damaged_quantity = request.POST.get("damaged_qty")
            reason = request.POST.get("reason")

            if damaged_quantity is not None and damaged_quantity.isdigit() and int(damaged_quantity) <= item.quantity and int(damaged_quantity) > 0:
                damaged_quantity = int(damaged_quantity)
                item.quantity -= damaged_quantity
                item.save()
                WastageAdminDashboard.objects.create(user = request.user, product = item.product, quantity = damaged_quantity, reason = reason, category = item.product.category, status = 'pending')
                for product in products:
                    if item.product.name == product.name:
                        damaged_price = damaged_quantity * product.unit_price
                        product.available_price = product.available_price - damaged_price
                        product.save()

                if item.quantity == 0:
                    item.delete()

                return redirect('return_form')
            else:
                messages.error(request, "Invalid damaged quantity.")
                return redirect('return_form')

        except ObjectDoesNotExist:
            messages.error(request, "Requested item does not exist.")
            return redirect('return_form')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('return_form')
        


@login_required(login_url='login')
@allowed_user(allowed_roles=['superadmin'])
def users_list2(request):
    try:
        users = User.objects.all()
        admins = AdminMail.objects.all()
        cart = Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user1 = name[-8:]
        admin_group = request.user.groups.filter(name="admin").exists()
        super_admin_group = request.user.groups.filter(name='superadmin').exists()

        return render(request, 'superadmin_view/users.html', {'users': users, 'admins': admins, 'count': count, 'admin_group': admin_group, 'super_admin_group': super_admin_group, 'name': user1})

    except ObjectDoesNotExist:
        return render(request, 'superadmin_view/users.html', {'error_message': 'Requested object does not exist.'})

    except Exception as e:
        print(f"An error occurred: {e}")
        return render(request, 'superadmin_view/users.html', {'error_message': 'An error occurred while processing your request.'})

@login_required(login_url='login')
def add_admin(request, user_id):
    try:
        users = User.objects.all()
        admins = AdminMail.objects.all()
        cart = Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        admin_group = request.user.groups.filter(name="admin").exists()
        super_admin_group = request.user.groups.filter(name='superadmin').exists()

        user = User.objects.get(id=user_id)

        if AdminMail.objects.filter(mail=user.email).exists():
            sweetify.warning(request, 'This Mail Id already been admin!', button="OK")
            return render(request, 'superadmin_view/users.html', {'users': users, 'admins': admins})

        admin_group = Group.objects.get(name='admin')
        user2 = User.objects.get(email=user.email)
        student_user_group = Group.objects.get(name='student_user')
        user2.groups.remove(student_user_group)
        user2.groups.add(admin_group)
        AdminMail.objects.create(mail=user2.email)

        return redirect('users_list')

    except ObjectDoesNotExist:
        sweetify.error(request, 'User does not exist!', button="OK")
        return redirect('users_list')

    except Exception as e:
        print(f"An error occurred: {e}")
        sweetify.error(request, 'An error occurred while processing your request!', button="OK")
        return redirect('users_list')

@login_required(login_url='login')
def user_list1(request):
    try:
        users = User.objects.all()
        admins=AdminMail.objects.all()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user1 = name[-8:]
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()

        return render(request, 'superadmin_view/users1.html', {'users': users,'admins':admins, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user1})
    
    except ObjectDoesNotExist:
        sweetify.error(request, 'User does not exist!', button="OK")
        return redirect('users_list')
    
    except Exception as e:
        print(f"An error occurred: {e}")
        sweetify.error(request, 'An error occurred while processing your request!', button="OK")
        return redirect('users_list')   


#Super-Admin-Remove-The-Admin-Role
@login_required(login_url='login')
def remove_role(request, user_id):
    try:
        admin_mail = AdminMail.objects.get(id=user_id)
        admin_mail.delete()
    except AdminMail.DoesNotExist:
        print("AdminMail object does not exist.")
    return redirect('users_list1')


#Log-For-Admin-SuperAdmin
@login_required(login_url='login')
@allowed_user(allowed_roles=['admin', 'superadmin'])
def admin_view(request):
    try:
        log = Log.objects.all()
        purchased_items = PurchasedItem.objects.all()
        checked_out = CheckedOutLog.objects.all()
        cart = Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        admin_group = request.user.groups.filter(name="admin").exists()
        super_admin_group = request.user.groups.filter(name="superadmin").exists()

        return render(request, 'adminview/admin.html', {'log': log, 'checked_out': checked_out, 'purchased_items': purchased_items, 'count': count, 'admin_group': admin_group, 'super_admin_group': super_admin_group, 'name': user})

    except ObjectDoesNotExist:
        messages.warning(request, 'An error occurred while processing your request!, Try again Later')
        return render(request, 'adminview/admin.html', {'error_message': 'Requested object does not exist.'})

    except Exception as e:
        print(f"An error occurred: {e}")
        messages.warning(request, 'An error occurred while processing your request!, Try again Later')
        return render(request, 'adminview/admin.html', {'error_message': 'An error occurred while processing your request.'})
    

@login_required(login_url='login')
@allowed_user(allowed_roles=['admin', 'superadmin'])
def admin_view1(request): 
    try:
        log = Log.objects.all()
        purchased_items = PurchasedItem.objects.all()
        checked_out = CheckedOutLog.objects.all()
        cart = Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        admin_group = request.user.groups.filter(name="admin").exists()
        super_admin_group = request.user.groups.filter(name="superadmin").exists()

        return render(request, 'adminview/admin1.html', {'log': log, 'checked_out': checked_out, 'purchased_items': purchased_items, 'count': count, 'admin_group': admin_group, 'super_admin_group': super_admin_group, 'name': user})

    except ObjectDoesNotExist:
        messages.warning(request, 'An error occurred while processing your request!, Try again Later')
        return render(request, 'adminview/admin1.html', {'error_message': 'Requested object does not exist.'})

    except Exception as e:
        print(f"An error occurred: {e}")
        messages.warning(request, 'An error occurred while processing your request!, Try again Later')
        return render(request, 'adminview/admin.html', {'error_message': 'An error occurred while processing your request.'})


#Wastage-Record-View-For-Admin-SuperAdmin
@allowed_user(allowed_roles=(['admin', 'superadmin']))
@login_required(login_url='login')
def wastage(request):
    try:
        wastage = Wastage.objects.all()
        print(wastage)
        cart = Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        admin_group = request.user.groups.filter(name="admin").exists()
        super_admin_group = request.user.groups.filter(name="superadmin").exists()
        total = 0

        for item in wastage:
            mul = item.wastage_user.product.unit_price * item.wastage_user.quantity
            total += mul

        return render(request, 'adminview/wastage_render.html', {'total': total, 'wastages': wastage, 'count': count, 'admin_group': admin_group, 'super_admin_group': super_admin_group, 'name': user})

    except ObjectDoesNotExist:
        messages.warning(request, 'An error occurred while processing your request!, Try again Later')
        return render(request, 'adminview/admin.html', {'error_message': 'Requested object does not exist.'})

    except Exception as e:
        print(f"An error occurred: {e}")
        messages.warning(request, 'An error occurred while processing your request!, Try again Later')
        return render(request, 'adminview/admin.html', {'error_message': 'An error occurred while processing your request.'})

    


#Add-Product-For-Admin-SuperAdmin
@allowed_user(allowed_roles=(['admin', 'superadmin']))
@login_required(login_url='login')
def add_product(request):
    try:
        categories = Category.objects.all()
        products = Product.objects.all()
        sub_categories = SubCategory.objects.all()
        admin_group = request.user.groups.filter(name="admin").exists()
        super_admin_group = request.user.groups.filter(name='superadmin').exists()
        cart = Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]

        if request.method == "POST":
            if 'form2' in request.POST and request.FILES.get('image'):
                product_name = request.POST.get("name")
                description = request.POST.get("description")
                actual_count = request.POST.get("actual")
                available_count = request.POST.get("avail")
                img = request.FILES["image"]
                cat = request.POST.get("category")
                category = Category.objects.get(name=cat)
                sub = request.POST.get('sub_category')
                sub_category = SubCategory.objects.get(name_sub=sub)
                unit_price = request.POST.get('unit_price')
                a_price = int(unit_price) * int(available_count)
                ac_price = int(unit_price) * int(actual_count)

                if int(actual_count) >= int(available_count):
                    Product.objects.create(created_by=request.user, name=product_name, decription=description, actual_count=actual_count, available_count=available_count, category=category, image=img, sub_category=sub_category, unit_price=unit_price, actual_price=ac_price, available_price=a_price)
                    sweetify.success(request, 'Product added successfully', button="OK")
                    return redirect("Add_product")
                else:
                    sweetify.error(request, 'The available quantity cannot be greater than the actual quantity', button="OK")
                    return redirect("Add_product")

        return render(request, "adminview/add_product.html", {"categories": categories, "products": products, 'sub_categories': sub_categories, 'admin_group': admin_group, 'super_admin_group': super_admin_group, 'count': count, 'name': user})

    except ObjectDoesNotExist:
        messages.warning(request, 'An error occurred while processing your request!, Try again Later')
        return render(request, 'adminview/add_product.html', {'error_message': 'Requested object does not exist.'})

    except Exception as e:
        print(f"An error occurred: {e}")
        messages.warning(request, 'An error occurred while processing your request!, Try again Later')
        return render(request, 'adminview/add_product.html', {'error_message': 'An error occurred while processing your request.'})    
    
#View-Product-For-Admin-SuperAdmin
@allowed_user(allowed_roles=(['admin', 'superadmin']))
@login_required(login_url='login')
def view_product(request):
    try:
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        products = Product.objects.all()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        return render(request, 'adminview/product.html', {'products':products, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})
    except ObjectDoesNotExist:
        messages.warning(request, 'An error occurred while processing your request!, Try again Later')
        return render(request, 'adminview/product.html', {})

#Remove-Product-For-Admin-SuperAdmin
@allowed_user(allowed_roles=(['admin', 'superadmin']))
@login_required(login_url='login')
def remove_product(request, pk):
    try:
        product = Product.objects.get(pk = pk)
        product.delete()
    except:
        print("Product doesNot exists")
        messages.warning(request, 'An error occurred while processing your request!, Try again Later')
    return redirect('product')

#Add-Category-For-Admin-SuperAdmin
@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def add_category(request):
    try:
        admin_group = request.user.groups.filter(name="admin").exists()
        super_admin_group = request.user.groups.filter(name='superadmin').exists()
        categories = Category.objects.all()
        sub_categories = SubCategory.objects.all()
        existing_categories = Category.objects.values_list('name', flat=True)
        existing_sub_categories = SubCategory.objects.values_list('name_sub', flat=True)
        name = request.user.username
        user = name[-8:]

        if request.method == "POST":
            if 'form1' in request.POST:
                name = request.POST.get('form1')
                cat = request.POST.get("category")
                category = Category.objects.get(name=cat)
                if SubCategory.objects.filter(name_sub=name).exists():
                    sweetify.warning(request, f'The Sub Category already exists', button="OK")
                    return redirect('Add_category')
                SubCategory.objects.create(name_sub=name, created_by=request.user, category=category)
                return redirect('Add_category')
            elif 'form2' in request.POST:
                name = request.POST.get('form2')
                if Category.objects.filter(name=name).exists():
                    sweetify.warning(request, f'The Category already exists', button="OK")
                    return redirect('Add_category')
                Category.objects.create(name=name, created_by=request.user)
                return redirect('Add_category')

        cart = Cart.objects.filter(created_by=request.user)
        count = cart.count()
        return render(request, 'adminview/add_category.html', {'sub_categories': sub_categories, 'categories': categories, 'existing_categories': list(existing_categories), 'count': count, 'existing_sub_categories': list(existing_sub_categories), 'admin_group': admin_group, 'super_admin_group': super_admin_group, 'name': user})

    except ObjectDoesNotExist:
        messages.warning(request, 'An error occurred while processing your request!, Try again Later')
        return render(request, 'adminview/add_category.html', {'error_message': 'Requested object does not exist.'})

    except Exception as e:
        print(f"An error occurred: {e}")
        messages.warning(request, 'An error occurred while processing your request!, Try again Later')
        return render(request, 'adminview/add_category.html', {'error_message': 'An error occurred while processing your request.'})   



#View-Category-For-Admin-SuperAdmin
@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def category(request):
    try:
        admin_group = request.user.groups.filter(name="admin").exists()
        super_admin_group = request.user.groups.filter(name='superadmin').exists()
        categories = Category.objects.all()
        cart = Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        return render(request, 'adminview/editCategory.html', {'categories': categories, 'count': count, 'admin_group': admin_group, 'super_admin_group': super_admin_group, 'name': user})

    except Exception as e:
        print(f"An error occurred: {e}")
        return render(request, 'error.html', {'error_message': 'An error occurred while processing your request.'})
    


#Remove-Category-For-Admin-SuperAdmin
@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def remove_category(request, category_id):
    try:
        category = Category.objects.get(id = category_id)
        category.delete()
    except Exception as e:
        print(f"An error occurred: {e}")
        
    return redirect('Add_category')


#Edit-Category-For-Admin-SuperAdmin
@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def edit_category(request, category_id):
    try:
        admin_group = request.user.groups.filter(name="admin").exists()
        super_admin_group = request.user.groups.filter(name='superadmin').exists()
        category = get_object_or_404(Category, id=category_id)
        name = request.user.username
        user = name[-8:]

        if request.method == "POST":
            new_category_name = request.POST.get('new_category_name')

            if new_category_name:
                category.name = new_category_name
                category.save()
                return redirect('Add_category')

        cart = Cart.objects.filter(created_by=request.user)
        count = cart.count()

        return render(request, 'adminview/edit_category.html', {"category": category, 'count': count, 'admin_group': admin_group, 'super_admin_group': super_admin_group})

    except Exception as e:
        print(f"An error occurred: {e}")
        return render(request, 'adminview/edit_category.html', {'error_message': 'An error occurred while processing your request.'})



@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def remove_subcategory(request, subcategory_id):
    try:
        category = SubCategory.objects.get(id = subcategory_id)
        category.delete()
    except Exception as e:
        print(f"An error occured: {e}")

    return redirect('Add_category')  



@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def edit_subcategory(request, subcategory_id):
    try:
        admin_group = request.user.groups.filter(name="admin").exists()
        super_admin_group = request.user.groups.filter(name='superadmin').exists()
        category = get_object_or_404(SubCategory, id=subcategory_id)
        name = request.user.username
        user = name[-8:]

        if request.method == "POST":
            new_category_name = request.POST.get('new_category_name')

            if new_category_name:
                category.name_sub = new_category_name
                category.save()
                return redirect('Add_category')

        cart = Cart.objects.filter(created_by=request.user)
        count = cart.count()

        return render(request, 'adminview/edit_sub_category.html', {"category": category, 'count': count, 'admin_group': admin_group, 'super_admin_group': super_admin_group})

    except Exception as e:
        print(f"An error occurred: {e}")
        return render(request, 'adminview/edit_sub_category.html', {'error_message': 'An error occurred while processing your request.'})
   

@method_decorator(login_required, name="dispatch")
class edit_product_view(View):
     def get(self, request, product_id):
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        cart = Cart.objects.filter(created_by = request.user)
        count = cart.count()
        product = Product.objects.get(id = product_id)
        categories = Category.objects.all()
        sub_categories = SubCategory.objects.all()
        name = request.user.username
        user = name[-8:]
        
        return render(request, 'adminview/edit_product.html', {'product':product, 'count':count, 'categories': categories, 'sub_categories': sub_categories,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})
    
     def post(self, request, product_id):
            try:
                product = Product.objects.get(id = product_id)
                product_name=request.POST.get("name")
                decription=request.POST.get("description") 
                unit_price = request.POST.get('unit_price')
                available_qty = request.POST.get('available_qu')
                actual_qty = request.POST.get('actual_qu')
                cat=request.POST.get('cat')
                sub = request.POST.get('sub_category')
                category=Category.objects.get(name=cat)
                sub_category = SubCategory.objects.get(name_sub=sub)
                value = request.POST.get('booleanfield')
                product.is_active = value == 'on'


                product.category = category
                product.sub_category = sub_category
                actual_Q = int(actual_qty)
                product.actual_count = actual_Q

                available_Q = int(available_qty)
                product.available_count = available_Q

                a_stock =  product.available_count
                actual_stock = product.actual_count

                a_price = float(unit_price) * float(a_stock) 
                ac_price = float(unit_price) * float(actual_stock)

                
                if(a_stock <= actual_stock):
                        product.name = product_name
                        product.decription = decription
                        product.unit_price = unit_price
                        product.available_count = a_stock
                        product.available_price = a_price
                        product.actual_count = actual_stock
                        product.actual_price = ac_price
                        product.save()
                        
                        sweetify.success(request, f'You are successfully Edited the {product.name}',button="OK")
                        return redirect('product')
                else:
                    messages.warning(request, 'Give the correct insight of that!')
                    return redirect('product')  
            except Exception as e:
                 return Response(str(e))
                


#Electrical 
@login_required(login_url='login')
def electrical_view(request):
    try:
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        products = Product.objects.all()
        return render(request, 'core/electrical.html', {'products': products, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})
    
    except ObjectDoesNotExist:
        messages.warning(request, 'An error occurred while processing your request.Try on Later')
        return render(request, 'core/electrical.html', {'error_message': 'An error occurred while processing your request.'})

#Mechanical
@login_required(login_url='login')
def mechanical_view(request):
    try:
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        products = Product.objects.all()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        return render(request, 'core/mechanical.html', {'products': products, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})
    except ObjectDoesNotExist:
        messages.warning(request, 'An error occured during request!, Try on Later')
        return render(request, 'core/mechanical.html')


#mechanical Product
@login_required(login_url='login')
def mechanical_product_view(request):
    try: 
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        products = Product.objects.all()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        return render(request, 'adminview/mechanicalproduct.html', {'products': products, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})
    except ObjectDoesNotExist:
        messages.warning(request, 'An error occurred while processing your request!, Try on Later.')
        return render(request, 'adminview/mechanicalproduct.html')


#electrical Product
@login_required(login_url='login')
def electrical_product_view(request):
    try: 
        name = request.user.username
        user = name[-8:]
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        products = Product.objects.all()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        return render(request, 'adminview/electricalproduct.html', {'products': products, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group, 'name':user})
    except ObjectDoesNotExist:
        messages.warning(request, 'An error Occured during Request Try Later on')
        return render(request, 'adminview/electricalproduct.html')
    
@allowed_user(allowed_roles=['admin', 'superadmin', 'wastage_admin'])
@login_required(login_url='login')
def wastage_admin_dashboard(request):
    try:
        waste_product = WastageAdminDashboard.objects.all()
        name = request.user.username
        user = name[-8:]
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        return render(request, 'wastage_admin/dashboard.html', {'products': waste_product, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group, 'name':user})

    except WastageAdminDashboard.DoesNotExist:
        error_message = "No wastage products found."
        return render(request, 'adminview/admin.html', {'error_message': error_message})

    except Exception as e:
        error_message = f"An error occurred: {e}"
        return render(request, '404.html', {'error_message': error_message})

@allowed_user(allowed_roles=['admin', 'superadmin', 'wastage_admin'])
@login_required(login_url='login')
def accept_order(request, wastage_id):
    try:
        order = get_object_or_404(WastageAdminDashboard, id=wastage_id)
        order.status = 'approved'
        order.save()
        Wastage.objects.create(created_by=request.user, wastage_user=order)
        return redirect('wastage_admin_dashboard')

    except WastageAdminDashboard.DoesNotExist:
        error_message = "The order does not exist."
        return render(request, 'adminview/admin.html', {'error_message': error_message})

    except Exception as e:
        error_message = f"An error occurred: {e}"
        return render(request, '404.html', {'error_message': error_message})

@allowed_user(allowed_roles=['admin', 'superadmin', 'wastage_admin'])
@login_required(login_url='login')
def reject_order(request, wastage_id):
    try:
        order = get_object_or_404(WastageAdminDashboard, id=wastage_id)
        order.status = 'rejected'
        order.delete()
        return redirect('wastage_admin_dashboard')

    except WastageAdminDashboard.DoesNotExist:
        error_message = "The order does not exist."
        return render(request, 'adminview/admin.html', {'error_message': error_message})

    except Exception as e:
        error_message = f"An error occurred: {e}"
        return render(request, '404.html', {'error_message': error_message})

@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def users_list(request):
    try:
        users = User.objects.all()
        admin_group = request.user.groups.filter(name="admin").exists()
        super_admin_group = request.user.groups.filter(name='superadmin').exists()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        
        if request.method == "POST":
            action = request.POST.get("action")
            if action == 'approve':
                application_id = request.POST.get('id')
                application = User.objects.get(id=application_id)
                admin_group = Group.objects.get(name='admin')
                user2 = User.objects.get(email=application.email)
                student_user_group = Group.objects.get(name='student_user')
                user2.groups.remove(student_user_group)
                user2.groups.add(admin_group)
                AdminMail.objects.create(mail=user2.email)
                application.save()
                sweetify.success(request, 'You are successfully added the User as a admin', button="OK") 
            elif action == 'reject':
                application_id = request.POST.get('id')
                application = User.objects.get(id=application_id)
                user2 = User.objects.get(email=application.email)
                admin_user_group = Group.objects.get(name='admin')
                user2.groups.remove(admin_user_group)
                admin_mail = AdminMail.objects.get(mail=application.email)
                admin_mail.delete()
                sweetify.success(request, 'You are successfully removed the User from the admin Role', button="OK")
            return redirect('users_list')
        
        return render(request, 'superadmin_view/users.html', {'users': users, 'admin_group': admin_group, 'super_admin_group': super_admin_group, 'count':count, 'name':user})
    
    except User.DoesNotExist:
        error_message = "The user does not exist."
        return render(request, 'adminview/admin.html', {'error_message': error_message})
    
    except Exception as e:
        error_message = f"An error occurred: {e}"
        return render(request, '404.html', {'error_message': error_message})



    
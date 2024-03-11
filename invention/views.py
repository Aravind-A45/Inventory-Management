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


#rest_api
from rest_framework.decorators import api_view
from rest_framework.response import Response    
# Create your views here.

#bulk import
from .tasks import import_products_from_excel



def new_login(request):
    return render(request, 'credential/new_login.html')

def bulk_import(request):
    file_path = 'D:\\inv1.xlsx'
    import_products_from_excel.delay(file_path)
    return HttpResponse('Products import task has been scheduled.')

  
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
        
    for i in allowed_emails:
        print(i)
    if user:
         return ('')
    return {'details': details, 'user': user, 'is_new': is_new}

def custom_forbidden(request):
    if request.method=="POST":
        return redirect('login')
    return render(request, 'custom_forbidden.html')


#Home-Page
@ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
@login_required(login_url= 'login')
def home(request):
        products = Product.objects.all()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        name = request.user.username
        user = name[-8:]

        
        return render(request, 'core/home.html', {'products': products, 'count':count, 'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})
    
    


#View-Product-Details-As-View-Details
@login_required(login_url='login')
def product_description(request, pk):
        item = Product.objects.get(pk =pk)
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        return render(request, 'core/product_description.html', {'item':item, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})


#About-Page
@login_required(login_url='login')
def about(request):
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()    
        name = request.user.username
        user = name[-8:]
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        return render(request, 'core/about.html', {'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})
    


#Access-Denied-Page
def no_permission(request):
        return render(request, 'core/no_permission.html')

#Cart Functionality

#Add-To-Cart
# temporary_cart = defaultdict(int)
@login_required(login_url='login')
def add_to_cart(request, product_id):
    try:
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
                        with transaction.atomic():
                                add=0
                                try:
                                    cart=Cart.objects.get(product_name=product,created_by=request.user)
                                    add=cart.quantity
                                    add += quantity_int
                                    cart.quantity=add
                                    if add > product.available_count:
                                        messages.warning(request, "Not Enough quantity available.")
                                        return redirect('Home')
                                    cart=Cart.objects.get(product_name=product,created_by=request.user).delete()
                                    Cart.objects.create(product_name=product,quantity=add,created_by=request.user) 
                                    sweetify.success(request, 'You are successfully added to the cart',button="OK") 
                                except:
                                    Cart.objects.create(product_name=product,quantity=quantity_int,created_by=request.user)
                    else:
                        messages.warning(request, "look up a valid quantity.")
                except ValueError:
                    return HttpResponse("Invalid quantity")
                sweetify.success(request, 'You are successfully added to the cart',button="OK") 
        return redirect('Home')
    except:
         cart=Cart.objects.filter(created_by=request.user)
         count = cart.count()
         name = request.user.username
         user = name[-8:]
         admin_group = request.user.groups.filter(name = "admin").exists()
         super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
         return render(request, 'core/home.html', {'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})

#View-Cart
@login_required(login_url='login')
def view_cart(request):
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        product=Product.objects.all()
        category=Category.objects.all()
        name = request.user.username
        user = name[-8:]
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        return render(request, 'cart/cart.html', {'cart_items':cart,'product':product,'category':category, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})
    
#Remove-Cart
@login_required(login_url='login')
def remove_from_cart(request, product_id):
        cart=Cart.objects.get(id=product_id,created_by=request.user)
        cart.delete()
        return redirect('view_cart')



#Submit-In-Cart
@login_required(login_url='login')
def submit_cart(request):
        if request.method == "POST":
            due_date = request.POST.get('due_date')
            for cart in Cart.objects.filter(created_by=request.user):
                status='checked_in'
                item=Product.objects.get(name=cart.product_name)
                if (item.available_count - cart.quantity) < 0:
                    Cart.objects.filter(created_by=request.user).delete()
                    messages.warning(request, "Not Enough quantity available..")
                else:
                    Product.objects.filter(name=cart.product_name).update(available_count=F('available_count')-cart.quantity)
                    PurchasedItem.objects.create(product=cart.product_name, quantity=cart.quantity, user=request.user,status=status,date_added=datetime.datetime.now(), due_date=due_date)
                    Log.objects.create(product=cart.product_name, quantity=cart.quantity, user=request.user, status=status, created_at=datetime.datetime.now(), due_date=due_date)
                    Cart.objects.filter(created_by=request.user).delete()
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
    except:
         return render(request, 'cart/return_form.html', {'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})


#Return-All
@login_required(login_url='login')
def return_all(request, item_id):
        item = get_object_or_404(Log, pk=item_id)
        product = item.product

        item.status = 'checked_in'
        item.save()

        CheckedOutLog.objects.create(product=product,quantity=item.quantity,user=request.user,status="checked_out")
        product.available_count += item.quantity
        product.save()
        item.delete()
        return redirect('return_form')
    
#Return One-By-One Form
class AddReturnView(View):
    def get(self, request, item_id):
            categories = Category.objects.all()
            products = Log.objects.all()
            cart=Cart.objects.filter(created_by=request.user)
            count = cart.count()
            item = get_object_or_404(Log, id=item_id)
            admin_group = request.user.groups.filter(name = "admin").exists()
            name = request.user.username
            user = name[-8:]
            super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
            return render(
                request,
                'cart/return.html',
                {'categories': categories, 'products': products, 'item': item, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user}
            )
        
    def post(self, request, item_id):
        try:
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
        except:
            
             return render(request, 'cart/return.html', {'categories':categories, 'products':products, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})



#Damaged-Form
class AddWastageView(View):
    def get(self, request, item_id):
            categories = Category.objects.all()
        
            products = Log.objects.all()
            item = get_object_or_404(Log, id=item_id)
            cart=Cart.objects.filter(created_by=request.user)
            count = cart.count()
            admin_group = request.user.groups.filter(name = "admin").exists()
            super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
            name = request.user.username
            user = name[-8:]
            return render(
                request,
                'cart/wastage.html',
                {'categories': categories, 'products': products, 'item': item, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user}
            )
    

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
                Wastage.objects.create(user=request.user,product_name=item.product,quantity=damaged_quantity,reason=reason,category=item.product.category)
                for product in products:
                    if item.product.name == product.name:
                        damaged_price = damaged_quantity * product.unit_price
                        product.available_price = product.available_price - damaged_price
                        product.save()
                    if item.quantity == 0:
                        item.delete()
                        return redirect('return_form')

                return redirect('return_form') 
                
            cart=Cart.objects.filter(created_by=request.user)
            count = cart.count()
            admin_group = request.user.groups.filter(name = "admin").exists()
            super_admin_group = request.user.groups.filter(name = 'superadmin').exists()    
            name = request.user.username
            user = name[-8:]
            return render(
                request,
                'cart/wastage.html',
                {'categories': categories, 'products': products, 'item': item, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user}
            )
        except:
             return render(request,'cart/wastage.html',{'categories': categories, 'products': products, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})
        
#User-Groups

#Super-Admin-Only-view
@login_required(login_url='login')
@allowed_user(allowed_roles=['superadmin'])
# def users_list(request):
#         users = User.objects.all()
#         admins=AdminMail.objects.all()
#         pattern= r"^[a-zA-Z0-9_.]+@(kct\.)+(ac\.)+in$"
#         if request.method=="POST":
#             email=request.POST.get("email")
#             if re.match(pattern,email):
                
#                 if AdminMail.objects.filter(mail = email).exists():
#                     sweetify.warning(request, 'Microsoft mail-id already exists ',button="OK")
#                     return render(request, 'superadmin_view/users.html', {'users': users,'admins':admins})
                
#                 admin_group = Group.objects.get(name = 'admin')
#                 user = User.objects.get(email = email)
#                 student_user_group = Group.objects.get(name = 'student_user')
#                 user.groups.remove(student_user_group)
#                 user.groups.add(admin_group)
#                 AdminMail.objects.create(mail = email)

#             users = User.objects.all()
#             return redirect('users_list')
#         cart=Cart.objects.filter(created_by=request.user)
#         count = cart.count()
#         name = request.user.username
#         user = name[-8:]
#         admin_group = request.user.groups.filter(name = "admin").exists()
#         super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        
#         return render(request, 'superadmin_view/users.html', {'users': users,'admins':admins, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})

def users_list(request):
        users = User.objects.all()
        admins=AdminMail.objects.all()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user1 = name[-8:]
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()

        return render(request, 'superadmin_view/users.html', {'users': users,'admins':admins, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user1})

def add_admin(request, user_id):
        users = User.objects.all()
        admins=AdminMail.objects.all()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()

        user = User.objects.get(id = user_id)
        if AdminMail.objects.filter(mail = user.email).exists():
                    sweetify.warning(request, 'Microsoft mail-id already exists ',button="OK")
                    return render(request, 'superadmin_view/users.html', {'users': users,'admins':admins})
        admin_group = Group.objects.get(name = 'admin')
        user2 = User.objects.get(email = user.email)
        student_user_group = Group.objects.get(name = 'student_user')
        user2.groups.remove(student_user_group)
        user2.groups.add(admin_group)
        AdminMail.objects.create(mail = user2.email)

        return redirect('users_list')


def user_list1(request):
        users = User.objects.all()
        admins=AdminMail.objects.all()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user1 = name[-8:]
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()

        return render(request, 'superadmin_view/users1.html', {'users': users,'admins':admins, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user1})



#Super-Admin-Remove-The-Admin-Role
def remove_role(request, user_id):
        print(user_id)
        print(AdminMail.objects.filter(id = user_id))
        AdminMail.objects.filter(id=user_id).delete()
        return redirect('users_list1')


#Log-For-Admin-SuperAdmin
@login_required(login_url='login')
@allowed_user(allowed_roles=['admin', 'superadmin'])
def admin_view(request): 
        log = Log.objects.all()
        purchased_items = PurchasedItem.objects.all()
        checked_out = CheckedOutLog.objects.all()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        return render(request, 'adminview/admin.html', {'log':log, 'checked_out':checked_out, 'purchased_items': purchased_items,'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})

@login_required(login_url='login')
@allowed_user(allowed_roles=['admin', 'superadmin'])
def admin_view1(request): 
        log = Log.objects.all()
        purchased_items = PurchasedItem.objects.all()
        checked_out = CheckedOutLog.objects.all()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        return render(request, 'adminview/admin1.html', {'log':log, 'checked_out':checked_out, 'purchased_items': purchased_items,'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})


#Wastage-Record-View-For-Admin-SuperAdmin
@allowed_user(allowed_roles=(['admin', 'superadmin']))
@login_required(login_url='login')
def wastage(request):
        wastage = Wastage.objects.all()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        return render(request, 'adminview/wastage_render.html', {'wastage': wastage, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})
    


#Add-Product-For-Admin-SuperAdmin
@allowed_user(allowed_roles=(['admin', 'superadmin']))
@login_required(login_url='login')
def add_product(request):
    try:
        categories=Category.objects.all()
        products = Product.objects.all()
        sub_categories = SubCategory.objects.all()
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        if request.method=="POST":
                if 'form2' in request.POST and request.FILES.get('image'):
                        
                        product_name=request.POST.get("name")
                        decription=request.POST.get("description")
                        actual_count=request.POST.get("actual")
                        available_count=request.POST.get("avail")
                        img=request.FILES["image"]   
                        cat=request.POST.get("category")
                        category=Category.objects.get(name=cat)
                        sub = request.POST.get('sub_category')
                        sub_category = SubCategory.objects.get(name_sub=sub) 
                        unit_price = request.POST.get('unit_price')
                        a_price = int(unit_price) * int(available_count)
                        ac_price = int(unit_price) * int(actual_count)
                        if int(actual_count) >= int(available_count):
                            print("exec add product")
                            Product.objects.create(created_by=request.user,name=product_name,decription=decription,actual_count=actual_count,available_count=available_count,category=category,image=img,sub_category = sub_category, unit_price = unit_price, actual_price=ac_price , available_price = a_price )
                            sweetify.success(request, 'Product added successfully',button="OK")
                           
                            return redirect("Add_product")
                        else:
                            sweetify.success(request, 'Look Up the Available Quantity',button="OK")
                            return redirect("Add_product")
        return render (request,"adminview/add_product.html",{"category":categories, "products":products, 'sub_category':sub_categories,'admin_group': admin_group, 'super_admin_group':super_admin_group,'count':count,'name':user}) 
    except:
         return render(request, "adminview/add_product.html",{"category":categories, "products":products, 'sub_category':sub_categories,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})    

#View-Product-For-Admin-SuperAdmin
@allowed_user(allowed_roles=(['admin', 'superadmin']))
@login_required(login_url='login')
def view_product(request):
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        products = Product.objects.all()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        return render(request, 'adminview/product.html', {'products':products, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})

#Remove-Product-For-Admin-SuperAdmin
@allowed_user(allowed_roles=(['admin', 'superadmin']))
@login_required(login_url='login')
def remove_product(request, pk):
        product = Product.objects.get(pk = pk)
        product.delete()
        return redirect('product')

#Add-Category-For-Admin-SuperAdmin
@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def add_category(request):
    try:
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        categories = Category.objects.all()
        sub_category = SubCategory.objects.all()
        existing_categories = Category.objects.values_list('name', flat=True)
        existing_sub_categories = SubCategory.objects.values_list('name_sub', flat=True)
        name = request.user.username
        user = name[-8:]
        if request.method == "POST":
            if 'form1' in request.POST:
                name = request.POST.get('form1')
                cat=request.POST.get("category")
                category=Category.objects.get(name=cat)
                SubCategory.objects.create(name_sub = name, created_by = request.user,category=category)
                return redirect('Add_category')
            elif 'form2' in request.POST:
                name = request.POST.get('form2')
                Category.objects.create(name = name, created_by = request.user)
                return redirect('Add_category')
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()     
        return render(request, 'adminview/add_category.html', {'sub_category': sub_category,'categories': categories,'existing_categories': list(existing_categories), 'count':count,'existing_sub_categoryies': list(existing_sub_categories),'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user}) 
    except:
         return render(request, 'adminview/add_category.html', {'sub_category': sub_category,'categories': categories,'existing_categories': list(existing_categories), 'count':count,'existing_sub_categoryies': list(existing_sub_categories),'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})   



#View-Category-For-Admin-SuperAdmin
@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def category(request):
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        categories = Category.objects.all()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        name = request.user.username
        user = name[-8:]
        return render(request, 'adminview/editCategory.html', {'categories': categories, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})
    


#Remove-Category-For-Admin-SuperAdmin
@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def remove_category(request, category_id):
        category = Category.objects.get(id = category_id)
        category.delete()
        return redirect('Add_category')


#Edit-Category-For-Admin-SuperAdmin
@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def edit_category(request, category_id):
    try:
            admin_group = request.user.groups.filter(name = "admin").exists()
            super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
            category = Category.objects.get(id = category_id)
            name = request.user.username
            user = name[-8:]
            if request.method == "POST":
                new_category_name = request.POST.get('new_category_name')

                if new_category_name:
                        category.name = new_category_name
                        category.save()
                        return redirect('Add_category')
                cart=Cart.objects.filter(created_by=request.user)
                count = cart.count()
            return render(request, 'adminview/edit_category.html', {"category":category, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,})
    except:
         return render(request, 'adminview/edit_category.html', {'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})



@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def remove_subcategory(request, subcategory_id):
        category = SubCategory.objects.get(id = subcategory_id)
        category.delete()
        return redirect('Add_category')  



@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def edit_subcategory(request, subcategory_id):
    try:
        admin_group = request.user.groups.filter(name = "admin").exists()
        super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
        category = SubCategory.objects.get(id = subcategory_id)
        name = request.user.username
        user = name[-8:]
        if request.method == "POST":
            new_category_name = request.POST.get('new_category_name')
            if new_category_name:
                    category.name_sub = new_category_name
                    category.save()
                    return redirect('Add_category')
            cart=Cart.objects.filter(created_by=request.user)
            count = cart.count()
        return render(request, 'adminview/edit_sub_category.html', {"category":category, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,})   
    except:
         cart = Cart.objects.filter(created_by = request.user)
         count = cart.count()
         return render(request, 'adminview/edit_sub_category.html', {'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})   


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
                curr_qty = request.POST.get('curr_qty')
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
                c_qty = int(curr_qty)
                actual_Q = int(actual_qty)
                product.actual_count = actual_Q

                available_Q = int(available_qty)
                product.available_count = available_Q

                a_stock = c_qty + product.available_count
                actual_stock = c_qty + product.actual_count

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
     admin_group = request.user.groups.filter(name = "admin").exists()
     super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
     products = Product.objects.all()
     cart=Cart.objects.filter(created_by=request.user)
     count = cart.count()
     name = request.user.username
     user = name[-8:]
     return render(request, 'core/electrical.html', {'products': products, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})

#Mechanical
@login_required(login_url='login')
def mechanical_view(request):
     admin_group = request.user.groups.filter(name = "admin").exists()
     super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
     products = Product.objects.all()
     cart=Cart.objects.filter(created_by=request.user)
     count = cart.count()
     name = request.user.username
     user = name[-8:]
     return render(request, 'core/mechanical.html', {'products': products, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})


#mechanical Product
@login_required(login_url='login')
def mechanical_product_view(request):
     admin_group = request.user.groups.filter(name = "admin").exists()
     super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
     products = Product.objects.all()
     cart=Cart.objects.filter(created_by=request.user)
     count = cart.count()
     name = request.user.username
     user = name[-8:]
     return render(request, 'adminview/mechanicalproduct.html', {'products': products, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group,'name':user})


#electrical Product
@login_required(login_url='login')
def electrical_product_view(request):
     name = request.user.username
     user = name[-8:]
     admin_group = request.user.groups.filter(name = "admin").exists()
     super_admin_group = request.user.groups.filter(name = 'superadmin').exists()
     products = Product.objects.all()
     cart=Cart.objects.filter(created_by=request.user)
     count = cart.count()
     return render(request, 'adminview/electricalproduct.html', {'products': products, 'count':count,'admin_group': admin_group, 'super_admin_group':super_admin_group, 'name':user})

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


# def schedule_mail(request):
#   schedule, created = CrontabSchedule.objects.get_or_create(hour = 18, minute = 30)
#   task = PeriodicTask.objects.create(crontab=schedule, name="schedule_mail_task_"+"1", task="mail.tasks.send_mail_func" )
#   return HttpResponse("Done")

  
def form_valid(self, form):
        email = form.cleaned_data["email"]
        message = form.cleaned_data["message"]
        send_notification_mail.delay(email,message)
        return HttpResponse('We have sent you a confirmation mail!')

#Microsoft-Authentication-View-Only-For-Admin
def restrict_user_pipeline(strategy, details, user=None, is_new=False, *args, **kwargs):
    email=AdminMail.objects.all()
    allowed_emails = ['nagulesh.22cs@kct.ac.in']
    for e in email:
        allowed_emails.append(e.mail)
        
    for i in allowed_emails:
        print(i)
    if user and user.email not in allowed_emails:
        return redirect('custom_forbidden')
    return {'details': details, 'user': user, 'is_new': is_new}

def custom_forbidden(request):
    if request.method=="POST":
        return redirect('login')
    return render(request, 'custom_forbidden.html')


#Login-And-Register
@ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
@unauthenticated_user
def login(request):
    if request.user.is_authenticated:
        return redirect('Home')
    
    if request.method=='POST':
        rollno=request.POST.get('rollno')
        password="iqube@kct"
        try:
            user=auth.authenticate(username=rollno,password=password)
            if user != None:
                auth.login(request,user)
                return redirect('Home')
            else:
                return redirect('Register')
        except:
            return redirect('no_permission')
 
    return render(request,'credential/login.html')

@ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
@unauthenticated_user
def signup(request):
    details=User.objects.all()   
    if request.user.is_authenticated:
        return redirect('Home')

    if request.method == "POST":
        rollno = request.POST.get('rollno')
        password='iqube@kct'
        user = User.objects.create_user(username=rollno,password=password)
        user=auth.authenticate(username=rollno,password=password)           
        
        #New user in student_user group
        group = Group.objects.get(name='student_user')
        user.groups.add(group)
            
        if user!=None:
            auth.login(request,user)
            sweetify.success(request, 'You are successfully created',button="OK")
            messages.success(request, f"Account Successfully Created for {rollno}")
            return redirect('Home')

    return render(request, 'credential/register.html')


#Home-Page
@ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
@login_required(login_url= 'login')
def home(request):
    if len(request.user.username)>9:
        user = get_object_or_404(User, id=request.user.id)
        admin_group = Group.objects.get(name='admin') 
        user.groups.add(admin_group)

    products = Product.objects.all()
    query = request.GET.get('query', '')
    if query:
       products = products.filter(name__icontains = query)
    
    cart=Cart.objects.filter(created_by=request.user)
    count = cart.count()
    
    return render(request, 'core/home.html', {'products': products, 'count':count,})
    


#View-Product-Details-As-View-Details
@ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
@login_required(login_url='login')
def product_description(request, pk):
    item = Product.objects.get(pk =pk)
    cart=Cart.objects.filter(created_by=request.user)
    count = cart.count()
    return render(request, 'core/product_description.html', {'item':item, 'count':count,})


#About-Page
@login_required(login_url='login')
@ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
def about(request):
    cart=Cart.objects.filter(created_by=request.user)
    count = cart.count()
    
    return render(request, 'core/about.html', {'count':count,})


#Access-Denied-Page
def no_permission(request):
    return render(request, 'core/no_permission.html')


#Cart Functionality

#Add-To-Cart
# temporary_cart = defaultdict(int)
@ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
def add_to_cart(request, product_id):
    print(product_id)
    product = Product.objects.select_for_update().get(id=product_id)
    if product.available_count == 0:
        messages.info(request, 'There is no available stock for this product.')
        return redirect('Home')
    if request.method == "POST":
        quantity = request.POST.get("count")
        # print(quantity)
        if quantity is not None: 
            try:
                # print(quantity)
                quantity_int = int(quantity)
                # print(quantity_int)
                if 0 < quantity_int <= product.available_count:
                    # print(quantity_int)
                    with transaction.atomic():
                            # print(quantity_int)
                            a=0
                            try:
                                cart=Cart.objects.get(product_name=product,created_by=request.user)
                                print(cart)
                                print(cart.quantity)
                                a=cart.quantity
                                a += quantity_int
                                cart.quantity=a
                                if a > product.dummy_count:
                                    messages.warning(request, "Not Enough quantity available.")
                                    return redirect('Home')
                                cart=Cart.objects.get(product_name=product,created_by=request.user).delete()
                                Cart.objects.create(product_name=product,quantity=a,created_by=request.user)  
                            except:
                                Cart.objects.create(product_name=product,quantity=quantity_int,created_by=request.user)
                else:
                    messages.warning(request, "look up a valid quantity.")
            except ValueError:
                return HttpResponse("Invalid quantity")
    return redirect('Home')

#View-Cart
def view_cart(request):
        cart=Cart.objects.filter(created_by=request.user)
        product=Product.objects.all()
        category=Category.objects.all()
        count = cart.count()
        return render(request, 'cart/cart.html', {'cart_items':cart,'product':product,'category':category, 'count':count,})

#Remove-Cart
def remove_from_cart(request, product_id):
    cart=Cart.objects.get(id=product_id,created_by=request.user)
    cart.delete()
    return redirect('view_cart')



#Submit-In-Cart
@ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
def submit_cart(request):
    if request.method == "POST":
        due_date = request.POST.get('due_date')
        for i in Cart.objects.filter(created_by=request.user):
            status='checked_in'
            p=Product.objects.get(name=i.product_name)
            if (p.available_count - i.quantity) < 0:
                Cart.objects.filter(created_by=request.user).delete()
                messages.warning(request, "Not Enough quantity available..")
            else:
                Product.objects.filter(name=i.product_name).update(available_count=F('available_count')-i.quantity)
                PurchasedItem.objects.create(product=i.product_name, quantity=i.quantity, user=request.user,status=status,date_added=datetime.datetime.now(), due_date=due_date)
                Log.objects.create(product=i.product_name, quantity=i.quantity, user=request.user, status=status, created_at=datetime.datetime.now(), due_date=due_date)
                Cart.objects.filter(created_by=request.user).delete()
    return redirect("Home")



def update_quantity(request, product_id, quantity):
    product = get_object_or_404(Product, id=product_id)
    if product.available_count >= quantity:
        product.available_count -= quantity
        product.save()
        updated_available_quantity = product.available_count
        return JsonResponse({'success': True, 'updatedAvailableQuantity': updated_available_quantity})
    else:
        return JsonResponse({'success': False})  


#Return-Form-View
def return_form(request):
    cart=Cart.objects.filter(created_by=request.user)
    count = cart.count()
    purchased_items = Log.objects.filter(user = request.user) 
    return render(request, 'cart/return_form.html', {'purchased_items':purchased_items, 'count':count,})

#Return-All
@ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
def return_all(request, item_id):
    item = get_object_or_404(Log, pk=item_id)
    product = item.product

    item.status = 'checked_in'
    item.save()

    CheckedOutLog.objects.create(product=product,quantity=item.quantity,user=request.user,status="checked_out")
    product.available_count += item.quantity
    product.dummy_count += item.quantity
    product.save()
    item.delete()
    return redirect('return_form')


#Return One-By-One Form
class AddReturnView(View):
    def get(self, request, item_id):
        categories = Category.objects.all()
        products = Log.objects.all()
        item = get_object_or_404(Log, id=item_id)
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        return render(
            request,
            'cart/return.html',
            {'categories': categories, 'products': products, 'item': item, 'count':count}
        )
    
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
            product.dummy_count += quantity
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
        return render(
            request,
            'cart/return.html',
            {'categories': categories, 'products': products, 'item': item, 'count':count,}
        )



#Damaged-Form
class AddWastageView(View):
    def get(self, request, item_id):
        categories = Category.objects.all()
       
        products = Log.objects.all()
        item = get_object_or_404(Log, id=item_id)
        cart=Cart.objects.filter(created_by=request.user)
        print(item.product.name)
        count = cart.count()
        return render(
            request,
            'cart/wastage.html',
            {'categories': categories, 'products': products, 'item': item, 'count':count,}
        )

    def post(self, request, item_id):
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
                s = damaged_quantity * product.unit_price
                product.available_price = product.available_price - s
                product.save()
            if item.quantity == 0:
                item.delete()
                return redirect('return_form')

            return redirect('return_form')
            
        else:
            pass
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        return render(
            request,
            'cart/wastage.html',
            {'categories': categories, 'products': products, 'item': item, 'count':count,}
        )
        
#User-Groups

#Super-Admin-Only-view
@login_required(login_url='login')
@allowed_user(allowed_roles=['superadmin'])
def users_list(request):
    users = User.objects.all()
    admins=AdminMail.objects.all()
    pattern= r"^[a-zA-Z0-9_.]+@(kct\.)+(ac\.)+in$"
    if request.method=="POST":
        email=request.POST.get("email")
        print(email)
        if re.match(pattern,email):
            print("valid")
            for i in admins:
                if email==i.mail:
                    sweetify.warning(request, 'Microsoft mail-id already exists ',button="OK")
                    return render(request, 'superadmin_view/users.html', {'users': users,'admins':admins})
            
            admin_group = Group.objects.get(name = 'admin')

            user = User.objects.get(email = email)

            student_user_group = Group.objects.get(name = 'student_user')

            user.groups.remove(student_user_group)

            user.groups.add(admin_group)

            AdminMail.objects.create(mail = email)

        users = User.objects.all()
        return redirect('users_list')
    cart=Cart.objects.filter(created_by=request.user)
    count = cart.count()
    return render(request, 'superadmin_view/users.html', {'users': users,'admins':admins, 'count':count,})


#Super-Admin-Remove-The-Admin-Role

def remove_role(request, user_id):
    emails=AdminMail.objects.all()
    AdminMail.objects.filter(id=user_id).delete()
    return redirect('users_list')

#Log-For-Admin-SuperAdmin
@login_required(login_url='login')
@allowed_user(allowed_roles=['admin', 'superadmin'])
def admin_view(request):
    log = Log.objects.all()
    purchased_items = PurchasedItem.objects.all()
    checked_out = CheckedOutLog.objects.all()
    cart=Cart.objects.filter(created_by=request.user)
    count = cart.count()
    return render(request, 'adminview/admin.html', {'log':log, 'checked_out':checked_out, 'purchased_items': purchased_items,'count':count,})


#Wastage-Record-View-For-Admin-SuperAdmin
@ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
@allowed_user(allowed_roles=(['admin', 'superadmin']))
@login_required(login_url='login')
def wastage(request):
    wastage = Wastage.objects.all()
    cart=Cart.objects.filter(created_by=request.user)
    count = cart.count()
    return render(request, 'adminview/wastage_render.html', {'wastage': wastage, 'count':count,})


#Add-Product-For-Admin-SuperAdmin
@ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
@allowed_user(allowed_roles=(['admin', 'superadmin']))
@login_required(login_url='login')
def add_product(request):
   category=Category.objects.all()
   products = Product.objects.all()
   sub_category = SubCategory.objects.all()
   if request.method=="POST":
        if 'form1' in request.POST:
            file = request.FILES.get('file')
            if file.name.endswith('.xlsx'):
                try:
                    df = pd.read_excel(file, sheet_name="Sheet1") 
                    df = df.drop_duplicates(subset=["name"], keep='first')
                    for index, row in df.iterrows():
                            try:
                                try:
                                        if not row.isnull().any():
                                            category, created = Category.objects.get_or_create(created_by=request.user,name = row['category'])
                                            sub_category,created = SubCategory.objects.get_or_create(category = category, name_sub= row['sub_category'], created_by = request.user)

                                            product, created = Product.objects.update_or_create(
                                                name = row['name'],
                                                decription = row['description'],
                                                actual_count = row['actual_count'],
                                                available_count = row['available_count'],
                                                unit_price = row['unit_price'],
                                                category = category,
                                                sub_category = sub_category,
                                                created_by = request.user,
                                                actual_price = row['unit_price'] * row['actual_count'],
                                                available_price = row['unit_price'] * row['available_count'],
                                            )
                                            
                                            print(product)
                                            if not created:
                                                        messages.success(request, f'Updated {product}')
                                        else:
                                            print("HI Hello")
                                            print("row",row)
                                            messages.error(request, f'Error on row {index + 2}: Look up the {row}')
        
                                except Exception as e:
                                        messages.error(request, f'Error on row {index + 2}: Look up the {row}')

                            except Exception as e:
                                messages.error(request, f'Error on row {index + 2}: {str(e)}')
                    messages.success(request, 'Import completed successfully')
                    return redirect('Add_product')
                
                except Exception as e:
                    messages.error(request, f'Error reading the Excel file: {str(e)}')
            else:
                messages.error(request, 'Invalid file format. Please upload a valid Excel file.')

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
                    Product.objects.create(created_by=request.user,name=product_name,decription=decription,actual_count=actual_count,available_count=available_count,category=category,image=img, dummy_count = available_count,sub_category = sub_category, unit_price = unit_price, actual_price=ac_price , available_price = a_price )
                    sweetify.success(request, 'Look Up the Available Quantity',button="OK")
                    return redirect("Add_product")
                else:
                    sweetify.warning(request, 'Product added successfully',button="OK")
                    return redirect("Add_product")
   cart=Cart.objects.filter(created_by=request.user)
   count = cart.count()
   return render (request,"adminview/add_product.html",{"category":category, "products":products,'count':count, 'sub_category':sub_category,})     

#View-Product-For-Admin-SuperAdmin
@ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
@allowed_user(allowed_roles=(['admin', 'superadmin']))
@login_required(login_url='login')
def view_product(request):
    products = Product.objects.all()
    cart=Cart.objects.filter(created_by=request.user)
    count = cart.count()
    return render(request, 'adminview/product.html', {'products':products, 'count':count,})


#Remove-Product-For-Admin-SuperAdmin
@ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
@allowed_user(allowed_roles=(['admin', 'superadmin']))
@login_required(login_url='login')
def remove_product(request, pk):
    product = Product.objects.get(pk = pk)
    product.delete()
    return redirect('product')


#Add-Category-For-Admin-SuperAdmin
# @ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def add_category(request):
    categories = Category.objects.all()
    sub_category = SubCategory.objects.all()
    existing_categories = Category.objects.values_list('name', flat=True)
    existing_sub_categories = SubCategory.objects.values_list('name_sub', flat=True)
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
    return render(request, 'adminview/add_category.html', {'sub_category': sub_category,'categories': categories,'existing_categories': list(existing_categories), 'count':count,'existing_sub_categoryies': list(existing_sub_categories)})     





#View-Category-For-Admin-SuperAdmin
# @ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def category(request):
        categories = Category.objects.all()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        return render(request, 'adminview/editCategory.html', {'categories': categories, 'count':count,})


#Remove-Category-For-Admin-SuperAdmin
@ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def remove_category(request, category_id):
    category = Category.objects.get(id = category_id)
    category.delete()
    return redirect('Add_category')


#Edit-Category-For-Admin-SuperAdmin
@ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def edit_category(request, category_id):
    category = Category.objects.get(id = category_id)
    if request.method == "POST":
       new_category_name = request.POST.get('new_category_name')

       if new_category_name:
            category.name = new_category_name
            category.save()
            return redirect('Add_category')
    cart=Cart.objects.filter(created_by=request.user)
    count = cart.count()
    return render(request, 'adminview/edit_category.html', {"category":category, 'count':count,})

@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def sub_category(request):
        categories = SubCategory.objects.all()
        cart=Cart.objects.filter(created_by=request.user)
        count = cart.count()
        return render(request, 'adminview/edit_subCategory.html', {'categories': categories, 'count':count,})  

@ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def remove_subcategory(request, subcategory_id):
    category = SubCategory.objects.get(id = subcategory_id)
    category.delete()
    return redirect('Add_category')  


@ratelimit(key='ip', rate='10/m', method=ratelimit.ALL, block=True)
@allowed_user(allowed_roles=['admin', 'superadmin'])
@login_required(login_url='login')
def edit_subcategory(request, subcategory_id):
    category = SubCategory.objects.get(id = subcategory_id)
    print(subcategory_id)
    if request.method == "POST":
       new_category_name = request.POST.get('new_category_name')
       print(new_category_name)

       if new_category_name:
            category.name_sub = new_category_name
            category.save()
            return redirect('Add_category')
    cart=Cart.objects.filter(created_by=request.user)
    count = cart.count()
    return render(request, 'adminview/edit_sub_category.html', {"category":category, 'count':count,})      

def edit_product_view(request, product_id):     
    product = Product.objects.get(id = product_id)
    if request.method=="POST":
         product_name=request.POST.get("name")
         decription=request.POST.get("description") 
         unit_price = request.POST.get('unit_price')
         curr_qty = request.POST.get('curr_qty')
         c_qty = int(curr_qty)
         a_stock = c_qty + product.available_count
         actual_stock = c_qty + product.actual_count

         a_price = float(unit_price) * float(a_stock) 
         ac_price = float(unit_price) * float(actual_stock)
         print(c_qty)
         print(a_stock)
         print(unit_price)

     
         if(a_stock <= product.actual_count):
                product.name = product_name
                product.decription = decription
                product.unit_price = unit_price
                product.available_count = a_stock
                product.available_price = a_price
                product.actual_count = actual_stock
                product.actual_price = ac_price
                product.save()
                return redirect('product')
         else:
             messages.warning(request, 'Give the correct insight of that!')
             return redirect('product')
              
    

    return render(request, 'adminview/edit_product.html', {'product':product})


def import_data_to_db(request):
    if request.method == "POST":
        file = request.FILES.get('file')
        if file.name.endswith('.xlsx'):
            try:
                df = pd.read_excel(file, sheet_name="Sheet1") 
                for index, row in df.iterrows():
                        try:
                            try:
                                    if not row.isnull().any():
                                        category, created = Category.objects.get(created_by=request.user,name = row['category'])
                                        sub_category,created = SubCategory.objects.get(category = category, name_sub= row['sub_category'], created_by = request.user)

                                        product, created = Product.objects.update_or_create(
                                            name = row['name'],
                                            decription = row['description'],
                                            actual_count = row['actual_count'],
                                            available_count = row['available_count'],
                                            unit_price = row['unit_price'],
                                            category = category,
                                            sub_category = sub_category,
                                            created_by = request.user,
                                            actual_price = row['unit_price'] * row['actual_count'],
                                            available_price = row['unit_price'] * row['available_count'],
                                        )
                                        
                                        print(product)
                                        if not created:
                                                    messages.success(request, f'Updated {product}')
                                    else:
                                        print("HI Hello")
                                        messages.error(request, f'Error on row {index + 2}: Look up the {row}')
    
                            except Exception as e:
                                    messages.error(request, f'Error on row {index + 2}: Look up the {row}')

                        except Exception as e:
                            messages.error(request, f'Error on row {index + 2}: {str(e)}')
                messages.success(request, 'Import completed successfully')
                return redirect('import')
            
            except Exception as e:
                messages.error(request, f'Error reading the Excel file: {str(e)}')
        else:
            messages.error(request, 'Invalid file format. Please upload a valid Excel file.')
            
                    
    return render(request, 'excel.html')



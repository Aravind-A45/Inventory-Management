from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from .models import AdminMail

def unauthenticated_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('Home')
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_func

def allowed_user(allowed_roles = []):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            group = None
            mail=AdminMail.objects.all()
            p=0
            for i in mail:
                if request.user.email==i.mail:
                    p=10
                    
            if request.user.groups.exists():
                group = request.user.groups.all()[0].name
            if (group in allowed_roles) or (p==10):
            # if group in allowed_roles:
              return view_func(request, *args, **kwargs)
            else:
                return render(request, 'core/no_permission.html')
                # return HttpResponse("Hello")
        return wrapper_func
    return decorator

# def admin_only(view_func):
#     def wrapper_func(request, *args, **kwargs):
#         group = None
#         if request.user.groups.exists():
#             group = request.user.groups.all()[0].name
#         if group == 'student_user':
#             return redirect('Home')
#         if group == 'admin':
#             return view_func(request, *args, **kwargs)
#     return wrapper_func

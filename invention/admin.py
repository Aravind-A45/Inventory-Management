from django.contrib import admin

from . models import *
from rest_framework.authtoken.models import Token

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(Log)
admin.site.register(AdminMail)
admin.site.register(Wastage)
admin.site.register(PurchasedItem)
admin.site.register(CheckedOutLog)
admin.site.register(SubCategory)
admin.site.register(Token)
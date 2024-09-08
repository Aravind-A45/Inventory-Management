from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import *
from celery import shared_task
from datetime import datetime, timedelta
from django.utils import timezone
import os
import xlrd
import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
import logging
from django.contrib.auth.models import User
from django.contrib import messages
from openpyxl import load_workbook
from django.core.files.base import ContentFile
import base64
from io import BytesIO
from PIL import Image as PILImage
import imghdr

@shared_task(bind=True)
def send_notification_mail(self):
    try:
        users = get_user_model().objects.all()

        for user in users:
            purchased_items = PurchasedItem.objects.filter(user=user, due_date__date=timezone.now().date())

            for item in purchased_items:
                mail_subject = "Due mail"
                message = "Your due_date has been crossed. So, return your products today."
                to_email = user.email

                send_mail(
                    subject=mail_subject,
                    message=message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[to_email],
                    fail_silently=False,
                )
                print(f"Due mail sent to {to_email}")

                item.email_sent = True
                item.save()

        return "Done"
    except Exception as e:
        print(f"An error occurred in send_notification_mail: {e}")
        return "Error"

@shared_task(bind=True)
def send_warning_mail(self):
    try:
        users = get_user_model().objects.all()

        for user in users:
            purchased_items = PurchasedItem.objects.filter(
                user=user,
                due_date__date=timezone.now().date() + timedelta(days=2),
            )

            for item in purchased_items:
                warning_date = item.due_date - timedelta(days=2)
                if timezone.now().date() >= warning_date.date():
                    mail_subject = "Warning mail"
                    message = "Your due date is going to reach in 2 days. Please return your respective products."
                    to_email = user.email

                    send_mail(
                        subject=mail_subject,
                        message=message,
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[to_email],
                        fail_silently=True,
                    )
                    print(f"Warning mail sent to {to_email}")
                    
                    item.email_sent = True
                    item.save()

        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

@shared_task(bind=True)
def send_stock_mail(self):
    try:
        low_stock_products = Product.objects.filter(available_count__lte=20)

        for i in low_stock_products:
            product_creator = i.created_by

            mail_subject = "Low Stock Warning"
            message = f"Low Stock Alert!!! The available stock for {i.name} is {i.available_count}, Update the stock"
            to_email = product_creator.email

            send_mail(
                subject=mail_subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[to_email],
                fail_silently=True,
            )
            print(f"Low stock warning mail sent to {to_email}")

        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


@shared_task
def process_excel_file(id):
    try:
        file_obj = File.objects.get(id=id)
        df = pd.read_excel(file_obj.file)

        for index, row in df.iterrows():
            category, _ = Category.objects.get_or_create(name=row['Category'])
            sub_category, _ = SubCategory.objects.get_or_create(name_sub=row['Sub_category'])
            created_by, _ = User.objects.get_or_create(username=row['Created_by'])

            product_name = row['Name']
            actual_count = row['Actual_count']
            available_count = row['Available_count']
            unit_price = row['Unit_price']

            existing_product = Product.objects.filter(name=product_name).first()

            if existing_product:
                existing_product.actual_count += actual_count
                existing_product.available_count += available_count
                existing_product.actual_price = existing_product.actual_count * unit_price
                existing_product.available_price = existing_product.available_count * unit_price
                existing_product.save()
            else:
                Product.objects.create(
                    name=product_name,
                    decription=row['Decription'],
                    actual_count=actual_count,
                    available_count=available_count,
                    category=category,
                    sub_category=sub_category,
                    unit_price=unit_price,
                    actual_price=actual_count * unit_price,
                    available_price=available_count * unit_price,
                    created_by=created_by
                )

        return "Success"
    except Exception as e:
        return f"An error occurred: {e}"







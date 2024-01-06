from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import PurchasedItem
from celery import shared_task
from datetime import datetime, timedelta

@shared_task(bind=True)
def send_notification_mail(self):
    users = get_user_model().objects.all()

    for user in users:
        purchased_items = PurchasedItem.objects.filter(user=user, due_date__date=timezone.now().date())

        for item in purchased_items:
            mail_subject = "Celery Testing"
            message = "hello"
            to_email = user.email

            send_mail(
                subject=mail_subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[to_email],
                fail_silently=False,
            )

    return "Done"

@shared_task(bind=True)
def send_warning_mail(self):
    users = get_user_model().objects.all()
    warning_date = timezone.now().date() - timedelta(days=2)

    for user in users:
        purchased_items = PurchasedItem.objects.filter(user=user)

        for item in purchased_items:
            mail_subject = "Warning mail"
            message = "Your due date is going to reach on 2 days. So, return your respective products"
            to_email = user.email

            send_mail(
                subject=mail_subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[to_email],
                fail_silently=False,
            )

    return "Done"

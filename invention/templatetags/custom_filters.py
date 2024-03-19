from django import template

register = template.Library()

@register.filter(name='user_belongs_to_admin_group')
def user_belongs_to_admin_group(user):
    return user.groups.filter(name='admin').exists()
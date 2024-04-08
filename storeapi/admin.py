from django.contrib import admin
from .models import Store, Status, BusinessHour, Report
# Register your models here.
admin.site.register(Store)
admin.site.register(Status)
admin.site.register(BusinessHour)
admin.site.register(Report)
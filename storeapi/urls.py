from django.urls import path
from . import views
from django.contrib import admin
urlpatterns = [
    path('', views.getRoute),
    path('admin/', admin.site.urls),
    path('insert/', views.insertData),
    path('trigger_report/', views.trigger_report),
    path('get_report/<str:pk>', views.getReport),

]
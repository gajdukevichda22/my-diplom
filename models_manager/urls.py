from django.urls import path
from . import views

app_name = 'models_manager'

urlpatterns = [
    path('', views.model_list, name='model_list'),
    path('upload/', views.upload_model, name='upload'),
    path('<int:pk>/', views.model_detail, name='model_detail'),
    path('<int:pk>/set_active/', views.set_active_version, name='set_active'),
    path('<int:pk>/delete_version/', views.delete_version, name='delete_version'),
    path('delete_group/<str:name>/', views.delete_model_group, name='delete_model_group'),
    path('<int:pk>/change_status/', views.change_status, name='change_status'),
    path('<int:pk>/change_material/', views.change_material, name='change_material'),
    path('<int:pk>/change_customer_name/', views.change_customer_name, name='change_customer_name'),
    path('<int:pk>/change_customer_phone/', views.change_customer_phone, name='change_customer_phone'),
    path('<int:pk>/change_customer_email/', views.change_customer_email, name='change_customer_email'),
    path('customer/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/', views.category_detail, name='category_detail'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('move_model/<int:pk>/', views.move_model_to_category, name='move_model'),
    path('logs/', views.log_list, name='log_list'),
    path('notifications/', views.get_notifications, name='notifications'),
    path('notifications/mark/<int:pk>/', views.mark_notification_read, name='mark_notification_read'),
    path('<int:pk>/add_comment/', views.add_comment, name='add_comment'),
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
]
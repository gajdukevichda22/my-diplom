from django.contrib import admin
from .models import Model3D, Category, LogEntry

@admin.register(Model3D)
class Model3DAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'material', 'status', 'customer_name', 'uploaded_by', 'uploaded_at', 'is_active')
    list_filter = ('status', 'material', 'is_active')
    search_fields = ('name', 'comment', 'customer_name', 'customer_phone', 'customer_email')
    readonly_fields = ('uploaded_at',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'author', 'created_at')
    list_filter = ('parent',)
    search_fields = ('name',)

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name', 'model_version')
    list_filter = ('action', 'user')
    search_fields = ('model_name', 'details')
    readonly_fields = ('timestamp',)
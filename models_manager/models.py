from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название папки')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Родительская папка')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Папка'
        verbose_name_plural = 'Папки'
        ordering = ['name']

    def __str__(self):
        return self.name

class Model3D(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('review', 'На проверке'),
        ('ready', 'Готов к печати'),
        ('printed', 'Напечатано'),
    ]
    name = models.CharField(max_length=200, db_index=True, verbose_name='Название модели')
    file = models.FileField(
        upload_to='models/',
        validators=[FileExtensionValidator(allowed_extensions=['stl', 'obj', 'step', '3mf'])],
        verbose_name='Файл'
    )
    version = models.CharField(max_length=20, default='1.0', db_index=True, verbose_name='Версия')
    material = models.CharField(max_length=50, blank=True, verbose_name='Материал')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    is_active = models.BooleanField(default=True, verbose_name='Активная версия')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Папка')
    customer_name = models.CharField(max_length=200, blank=True, verbose_name='Заказчик')
    customer_phone = models.CharField(max_length=50, blank=True, verbose_name='Телефон')
    customer_email = models.CharField(max_length=100, blank=True, verbose_name='Email')

    class Meta:
        unique_together = [['name', 'version']]
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.name} v{self.version}"

class LogEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_logs', verbose_name='Пользователь')
    action = models.CharField(max_length=100, verbose_name='Действие')
    model_name = models.CharField(max_length=200, blank=True, verbose_name='Модель')
    model_version = models.CharField(max_length=20, blank=True, verbose_name='Версия')
    details = models.TextField(blank=True, verbose_name='Детали')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Время')

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Запись лога'
        verbose_name_plural = 'Логи'

    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=200, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}"


class Comment(models.Model):
    model_version = models.ForeignKey(Model3D, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    text = models.TextField(verbose_name='Текст комментария')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author}: {self.text[:50]}"
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.http import JsonResponse
from .models import Model3D, Category, LogEntry, Notification, Comment
from .forms import Model3DUploadForm, CategoryForm, CommentForm

def get_next_version(name):
    last = Model3D.objects.filter(name=name).order_by('-version').first()
    if not last:
        return '1.0'
    parts = last.version.split('.')
    major = int(parts[0])
    minor = int(parts[1]) + 1
    return f"{major}.{minor}"

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '_', name)

def log_action(user, action, model_obj=None, details=''):
    LogEntry.objects.create(
        user=user,
        action=action,
        model_name=model_obj.name if model_obj else '',
        model_version=model_obj.version if model_obj else '',
        details=details
    )

def create_notification_for_technologists(message, link=None):
    groups = Group.objects.filter(name__in=['Технолог', 'Администратор'])
    users = User.objects.filter(groups__in=groups).distinct()
    for user in users:
        Notification.objects.create(user=user, message=message, link=link)

@login_required
def model_list(request):
    all_models = Model3D.objects.all().order_by('name', '-version')
    unique_models = {}
    for m in all_models:
        if m.name not in unique_models:
            unique_models[m.name] = m
    final_models = []
    for name, default_model in unique_models.items():
        ready_version = Model3D.objects.filter(name=name, status='ready').order_by('-version').first()
        if ready_version:
            final_models.append(ready_version)
        else:
            final_models.append(default_model)

    # Фильтры
    q = request.GET.get('q', '')
    if q:
        final_models = [m for m in final_models if q.lower() in m.name.lower() or q.lower() in m.comment.lower()]
    material = request.GET.get('material', '')
    if material:
        final_models = [m for m in final_models if material.lower() in m.material.lower()]
    status = request.GET.get('status', '')
    if status:
        final_models = [m for m in final_models if m.status == status]
    category_id = request.GET.get('category', '')
    if category_id:
        final_models = [m for m in final_models if m.category_id == int(category_id)]
    customer_name = request.GET.get('customer_name', '')
    if customer_name:
        final_models = [m for m in final_models if customer_name.lower() in m.customer_name.lower()]

    # Фильтр по первой букве алфавита
    letter = request.GET.get('letter', '')
    if letter and letter != 'all':
        final_models = [m for m in final_models if m.name and m.name[0].upper() == letter.upper()]

    # Сортировка
    sort_by = request.GET.get('sort', 'name')
    direction = request.GET.get('dir', 'asc')
    reverse = (direction == 'desc')
    if sort_by == 'name':
        final_models.sort(key=lambda x: x.name.lower(), reverse=reverse)
    elif sort_by == 'version':
        final_models.sort(key=lambda x: tuple(map(int, x.version.split('.'))), reverse=reverse)
    elif sort_by == 'material':
        final_models.sort(key=lambda x: x.material.lower(), reverse=reverse)
    elif sort_by == 'status':
        status_order = {'draft':0, 'review':1, 'ready':2, 'printed':3}
        final_models.sort(key=lambda x: status_order.get(x.status, 0), reverse=reverse)
    elif sort_by == 'customer_name':
        final_models.sort(key=lambda x: x.customer_name.lower(), reverse=reverse)
    elif sort_by == 'category':
        final_models.sort(key=lambda x: x.category.name.lower() if x.category else '', reverse=reverse)

    # Статистика для дашборда (уникальные модели, а не версии)
    total_models_count = Model3D.objects.values('name').distinct().count()
    ready_models_count = Model3D.objects.filter(status='ready').values('name').distinct().count()
    review_models_count = Model3D.objects.filter(status='review').values('name').distinct().count()

    # Текущая буква для подсветки в шаблоне
    current_letter = request.GET.get('letter', 'all')

    return render(request, 'models_manager/list.html', {
        'models': final_models,
        'categories': Category.objects.all(),
        'sort': sort_by,
        'dir': direction,
        'status_choices': Model3D.STATUS_CHOICES,
        'total_models_count': total_models_count,
        'ready_models_count': ready_models_count,
        'review_models_count': review_models_count,
        'current_letter': current_letter,
    })

@login_required
def model_detail(request, pk):
    model = get_object_or_404(Model3D, pk=pk)
    versions = Model3D.objects.filter(name=model.name).order_by('-version')
    return render(request, 'models_manager/detail.html', {
        'model': model,
        'versions': versions,
        'categories': Category.objects.all(),
        'comment_form': CommentForm(),
    })

@login_required
def upload_model(request):
    if request.method == 'POST':
        form = Model3DUploadForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name']
            file = form.cleaned_data['file']
            material = form.cleaned_data.get('material', '')
            comment = form.cleaned_data.get('comment', '')
            category = form.cleaned_data.get('category')
            customer_name = form.cleaned_data.get('customer_name', '')
            customer_phone = form.cleaned_data.get('customer_phone', '')
            customer_email = form.cleaned_data.get('customer_email', '')
            version = request.POST.get('version', '').strip()
            if not version:
                version = get_next_version(name)
            elif Model3D.objects.filter(name=name, version=version).exists():
                messages.error(request, f'Версия {version} уже существует')
                return render(request, 'models_manager/upload.html', {'form': form})
            ext = file.name.split('.')[-1]
            file.name = f"{sanitize_filename(name)}_v{version}.{ext}"
            Model3D.objects.filter(name=name).update(is_active=False)
            new = Model3D(
                name=name, file=file, version=version,
                material=material, comment=comment,
                uploaded_by=request.user, is_active=True, category=category,
                customer_name=customer_name, customer_phone=customer_phone, customer_email=customer_email
            )
            new.save()
            log_action(request.user, 'Загрузка модели', new, f'Версия {version}')
            create_notification_for_technologists(
                f'Новая версия {version} модели "{name}" загружена пользователем {request.user.username}.',
                link=f'/models/{new.pk}/'
            )
            messages.success(request, f'Модель "{name}" версия {version} загружена')
            return redirect('models_manager:model_detail', pk=new.pk)
    else:
        form = Model3DUploadForm()
    return render(request, 'models_manager/upload.html', {'form': form})

@login_required
def set_active_version(request, pk):
    version = get_object_or_404(Model3D, pk=pk)
    Model3D.objects.filter(name=version.name).update(is_active=False)
    version.is_active = True
    version.save()
    log_action(request.user, 'Смена активной версии', version, f'Активна v{version.version}')
    create_notification_for_technologists(
        f'Модель "{version.name}" версия {version.version} помечена как "Готов к печати".',
        link=f'/models/{version.pk}/'
    )
    messages.success(request, f'Активна версия {version.name} v{version.version}')
    return redirect('models_manager:model_detail', pk=version.pk)

@login_required
def delete_version(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Нет прав на удаление')
        return redirect('models_manager:model_list')
    version = get_object_or_404(Model3D, pk=pk)
    name = version.name
    version.delete()
    log_action(request.user, 'Удаление версии', version, f'Удалена версия {name} v{version.version}')
    messages.success(request, f'Версия {name} v{version.version} удалена')
    remaining = Model3D.objects.filter(name=name).exists()
    if remaining:
        any_version = Model3D.objects.filter(name=name).first()
        return redirect('models_manager:model_detail', pk=any_version.pk)
    else:
        return redirect('models_manager:model_list')

@login_required
def delete_model_group(request, name):
    if not request.user.is_superuser:
        messages.error(request, 'Нет прав на удаление')
        return redirect('models_manager:model_list')
    Model3D.objects.filter(name=name).delete()
    log_action(request.user, 'Удаление группы моделей', None, f'Удалена модель "{name}" (все версии)')
    messages.success(request, f'Модель "{name}" (все версии) удалена')
    return redirect('models_manager:model_list')

@login_required
def change_status(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Нет прав')
        return redirect('models_manager:model_detail', pk=pk)
    model = get_object_or_404(Model3D, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Model3D.STATUS_CHOICES):
            model.status = new_status
            model.save()
            log_action(request.user, 'Изменение статуса', model, f'Статус изменён на {new_status}')
            messages.success(request, f'Статус изменён на {model.get_status_display()}')
            if new_status == 'ready':
                create_notification_for_technologists(
                    f'Модель "{model.name}" версия {model.version} помечена как "Готов к печати" (изменение статуса).',
                    link=f'/models/{model.pk}/'
                )
    return redirect('models_manager:model_detail', pk=pk)

@login_required
def change_material(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Нет прав')
        return redirect('models_manager:model_list')
    model = get_object_or_404(Model3D, pk=pk)
    if request.method == 'POST':
        new_material = request.POST.get('material', '').strip()
        model.material = new_material
        model.save()
        log_action(request.user, 'Изменение материала', model, f'Материал изменён на {new_material}')
        messages.success(request, f'Материал модели "{model.name}" изменён')
    return redirect('models_manager:model_list')

@login_required
def change_customer_name(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Нет прав')
        return redirect('models_manager:model_list')
    model = get_object_or_404(Model3D, pk=pk)
    if request.method == 'POST':
        model.customer_name = request.POST.get('customer_name', '').strip()
        model.save()
        messages.success(request, f'Заказчик изменён')
    return redirect('models_manager:model_list')

@login_required
def change_customer_phone(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Нет прав')
        return redirect('models_manager:model_list')
    model = get_object_or_404(Model3D, pk=pk)
    if request.method == 'POST':
        model.customer_phone = request.POST.get('customer_phone', '').strip()
        model.save()
        messages.success(request, f'Телефон изменён')
    return redirect('models_manager:model_list')

@login_required
def change_customer_email(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Нет прав')
        return redirect('models_manager:model_list')
    model = get_object_or_404(Model3D, pk=pk)
    if request.method == 'POST':
        model.customer_email = request.POST.get('customer_email', '').strip()
        model.save()
        messages.success(request, f'Email изменён')
    return redirect('models_manager:model_list')

@login_required
def customer_detail(request, pk):
    model = get_object_or_404(Model3D, pk=pk)
    if request.method == 'POST':
        model.customer_name = request.POST.get('customer_name', '').strip()
        model.customer_phone = request.POST.get('customer_phone', '').strip()
        model.customer_email = request.POST.get('customer_email', '').strip()
        model.save()
        messages.success(request, 'Данные заказчика сохранены.')
        return redirect('models_manager:model_list')
    return render(request, 'models_manager/customer_detail.html', {'model': model})

@login_required
def category_list(request):
    if not request.user.is_staff:
        messages.error(request, 'Доступ запрещён')
        return redirect('models_manager:model_list')
    categories = Category.objects.filter(parent__isnull=True)
    return render(request, 'models_manager/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    if not request.user.is_staff:
        messages.error(request, 'Доступ запрещён')
        return redirect('models_manager:model_list')
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.author = request.user
            cat.save()
            log_action(request.user, 'Создание папки', None, f'Создана папка "{cat.name}"')
            messages.success(request, f'Папка "{cat.name}" создана')
            return redirect('models_manager:category_list')
    else:
        form = CategoryForm()
    return render(request, 'models_manager/category_form.html', {'form': form})

@login_required
def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    all_models = Model3D.objects.filter(category=category).order_by('name', '-version')
    unique_models = {}
    for m in all_models:
        if m.name not in unique_models:
            unique_models[m.name] = m
    models_list = []
    for name, default_model in unique_models.items():
        ready_version = Model3D.objects.filter(name=name, status='ready', category=category).order_by('-version').first()
        if ready_version:
            models_list.append(ready_version)
        else:
            models_list.append(default_model)
    q = request.GET.get('q', '')
    if q:
        models_list = [m for m in models_list if q.lower() in m.name.lower() or q.lower() in m.comment.lower()]
    material = request.GET.get('material', '')
    if material:
        models_list = [m for m in models_list if material.lower() in m.material.lower()]
    status = request.GET.get('status', '')
    if status:
        models_list = [m for m in models_list if m.status == status]
    subcategories = Category.objects.filter(parent=category)
    return render(request, 'models_manager/category_detail.html', {
        'category': category,
        'models': models_list,
        'subcategories': subcategories,
    })

@login_required
def move_model_to_category(request, pk):
    if request.method != 'POST':
        messages.error(request, 'Неверный метод')
        return redirect('models_manager:model_list')
    model = get_object_or_404(Model3D, pk=pk)
    new_category_id = request.POST.get('category')
    if new_category_id:
        try:
            new_category = Category.objects.get(pk=new_category_id)
            model.category = new_category
            model.save()
            log_action(request.user, 'Перемещение модели', model, f'В папку {new_category.name}')
            messages.success(request, f'Модель перемещена в папку "{new_category.name}"')
        except Category.DoesNotExist:
            messages.error(request, 'Папка не найдена')
    else:
        model.category = None
        model.save()
        log_action(request.user, 'Перемещение модели', model, 'Удалена из папки')
        messages.success(request, 'Модель удалена из папки')
    return redirect(request.META.get('HTTP_REFERER', 'models_manager:model_list'))

@login_required
def category_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Нет прав')
        return redirect('models_manager:category_list')
    category = get_object_or_404(Category, pk=pk)
    name = category.name
    category.delete()
    log_action(request.user, 'Удаление папки', None, f'Удалена папка "{name}"')
    messages.success(request, f'Папка "{name}" удалена')
    return redirect('models_manager:category_list')

@login_required
def log_list(request):
    if not request.user.is_superuser:
        messages.error(request, 'Доступ запрещён')
        return redirect('models_manager:model_list')
    logs = LogEntry.objects.all().order_by('-timestamp')
    return render(request, 'models_manager/log_list.html', {'logs': logs})

@login_required
def get_notifications(request):
    notifications = request.user.notifications.filter(is_read=False)[:10]
    data = [{'id': n.id, 'message': n.message, 'link': n.link, 'created_at': n.created_at.isoformat()} for n in notifications]
    return JsonResponse({'notifications': data, 'count': len(data)})

@login_required
def mark_notification_read(request, pk):
    try:
        notification = request.user.notifications.get(pk=pk)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'ok'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)

@login_required
def add_comment(request, pk):
    model_version = get_object_or_404(Model3D, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.model_version = model_version
            comment.author = request.user
            comment.save()
            messages.success(request, 'Комментарий добавлен.')
    return redirect('models_manager:model_detail', pk=model_version.pk)

@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if request.user.is_superuser or comment.author == request.user:
        comment.delete()
        messages.success(request, 'Комментарий удалён.')
    else:
        messages.error(request, 'Нет прав на удаление.')
    return redirect('models_manager:model_detail', pk=comment.model_version.pk)
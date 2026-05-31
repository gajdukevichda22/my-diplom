from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from models_manager.models import Model3D, Category

class Command(BaseCommand):
    help = 'Создаёт группы пользователей и назначает права'

    def handle(self, *args, **options):

        ct_model = ContentType.objects.get_for_model(Model3D)
        ct_category = ContentType.objects.get_for_model(Category)


        perms_model = Permission.objects.filter(content_type=ct_model)
        perms_category = Permission.objects.filter(content_type=ct_category)


        admin_group, _ = Group.objects.get_or_create(name='Администратор')
        admin_group.permissions.set(perms_model.union(perms_category))

   
        tech_perms = perms_model.filter(codename__in=['add_model3d', 'change_model3d', 'view_model3d'])
        tech_group, _ = Group.objects.get_or_create(name='Технолог')
        tech_group.permissions.set(tech_perms)


        designer_perms = perms_model.filter(codename__in=['add_model3d', 'change_model3d', 'view_model3d'])
        designer_group, _ = Group.objects.get_or_create(name='Дизайнер')
        designer_group.permissions.set(designer_perms)


        manager_perms = perms_model.filter(codename__in=['view_model3d'])
        manager_group, _ = Group.objects.get_or_create(name='Менеджер')
        manager_group.permissions.set(manager_perms)

        self.stdout.write(self.style.SUCCESS('Группы и права успешно созданы'))
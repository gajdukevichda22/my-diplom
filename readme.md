## Данные об авторе
<br> Гайдукевич Даниил Александрович
<br> gajdukevich_da_22
<br> 4 курс, 8 семестр 
Управление информационными ресурсами
Дипломная работа

## Требования
- Python 3.10 или выше
- pip (устанавливается вместе с Python)

## Установка и запуск

1. *Склонируйте репозиторий 
   git clone https://github.com/gajdukevichda22/my-diplom.git
   cd my-diplom

2. Создайте виртуальное окружение (один раз):
python -m venv venv

3. Активируйте виртуальное окружение:
   venv\Scripts\activate

4.Установите зависимости:
pip install -r requirements.txt

5. Выполните миграции базы данных
python manage.py migrate

6. Создайте суперпользователя
python manage.py createsuperuser

7.Запустите сервер:
python manage.py runserver

Откройте в браузере:
Главная страница: http://127.0.0.1:8000/
Админка: http://127.0.0.1:8000/admin

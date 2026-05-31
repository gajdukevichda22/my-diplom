from django import forms
from .models import Model3D, Category, Comment

class Model3DUploadForm(forms.ModelForm):
    material = forms.ChoiceField(
        choices=[('', 'Выберите материал')] + [(m, m) for m in ['PLA', 'ABS', 'PETG', 'Другой']],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_material_select'})
    )
    custom_material = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите свой материал', 'id': 'id_custom_material'}),
        label='Свой материал'
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Папка'
    )
    customer_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов Иван Иванович'}),
        label='Заказчик (ФИО)'
    )
    customer_phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+375 XX XXX-XX-XX'}),
        label='Телефон'
    )
    customer_email = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'client@example.com'}),
        label='Email'
    )

    class Meta:
        model = Model3D
        fields = ['name', 'file', 'comment', 'category', 'customer_name', 'customer_phone', 'customer_email']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = file.name.split('.')[-1].lower()
            if ext not in ['stl', 'obj', 'step', '3mf']:
                raise forms.ValidationError('Допустимые форматы: .stl, .obj, .step, .3mf')
            if file.size > 200 * 1024 * 1024:
                raise forms.ValidationError('Максимальный размер файла 200 МБ')
        return file

    def clean(self):
        cleaned = super().clean()
        mat = cleaned.get('material')
        custom = cleaned.get('custom_material')
        if mat == 'Другой' and custom:
            cleaned['material'] = custom
        elif mat and mat != 'Другой':
            cleaned['material'] = mat
        else:
            cleaned['material'] = ''
        return cleaned

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Напишите комментарий...'}),
        }
        labels = {'text': ''}
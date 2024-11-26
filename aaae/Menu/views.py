import csv
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import FileUploadForm
from django.db import transaction
from .models import Category, CategoryItem, Menu


def upload_menu(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            try:
                # Determine file type
                if uploaded_file.name.endswith('.csv'):
                    handle_csv_file(uploaded_file)
                elif uploaded_file.name.endswith(('.xls', '.xlsx')):
                    handle_excel_file(uploaded_file)
                else:
                    messages.error(request, "Unsupported file format. Please upload a CSV or Excel file.")
                    return redirect('upload-menu')

                messages.success(request, "Menu uploaded successfully!")
                return redirect('upload-menu')
            except Exception as e:
                messages.error(request, f"Error processing file: {e}")
                return redirect('upload-menu')
    else:
        form = FileUploadForm()

    return render(request, 'Menu/upload_menu.html', {'form': form})


def handle_csv_file(file):
    decoded_file = file.read().decode('utf-8').splitlines()
    reader = csv.DictReader(decoded_file)

    with transaction.atomic():
        for row in reader:
            category_name = row.get('Category')
            item_name = row.get('Item')
            description = row.get('Description')
            price = row.get('Price')

            print("category_name: ", category_name)

            # Create or get category
            category, created = Category.objects.get_or_create(name=category_name)
            print("Category created")
            # Create menu item
            CategoryItem.objects.create(
                category=category,
                name=item_name,
                description=description,
                price=price
            )


def handle_excel_file(file):
    df = pd.read_excel(file)
    for _, row in df.iterrows():
        category_name = row['Category']
        item_name = row['Item']
        description = row['Description']
        price = row['Price']

        # Create or get category
        category, created = Category.objects.get_or_create(name=category_name)
        # Create menu item
        CategoryItem.objects.create(
            category=category,
            name=item_name,
            description=description,
            price=price
        )


def menu_list(request):
    menus = Menu.objects.all()
    return render(request, 'Menu/menu_list.html', {'menus': menus})


def menu_detail(request, pk):
    menu = get_object_or_404(Menu, pk=pk)
    return render(request, 'Menu/menu_detail.html', {'menu': menu})
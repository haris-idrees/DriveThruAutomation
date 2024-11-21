from django.db import models

# Create your models here.


class Restaurant(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    contact = models.CharField(max_length=15)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Menu(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menus')
    categories = models.ManyToManyField(Category, related_name='menus')

    def __str__(self):
        return self.restaurant.name


class CategoryItem(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='items'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    additional_info = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name






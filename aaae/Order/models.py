from django.db import models
from aaae.Menu.models import Restaurant, CategoryItem, Category

# Create your models here.


class Order(models.Model):
    conversation_id = models.UUIDField()
    customer_name = models.CharField(max_length=100)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    total_bill = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Order #{self.id} by {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    item = models.ForeignKey(CategoryItem, on_delete=models.CASCADE, related_name='ordered_items')
    quantity = models.PositiveIntegerField(default=1)
    sub_total = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.quantity}x {self.item.name} for Order #{self.order.id}"


class Transcript(models.Model):
    conversation_id = models.UUIDField()
    role = models.CharField(max_length=10, choices=[('user', 'User'), ('assistant', 'Assistant'), ('system', 'System')])
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

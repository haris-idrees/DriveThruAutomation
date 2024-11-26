from aaae.Menu.models import Menu, CategoryItem
from aaae.Order.models import Transcript, Order, OrderItem
from django.conf import settings
from django.db import transaction
import os
import json
from openai import OpenAI


def generate_response(conversation_history):
    try:
        open_ai_key = settings.OPEN_AI_KEY

        client = OpenAI(api_key=open_ai_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history
        )

        # Clean and return assistant's response
        assistant_response = response.choices[0].message.content
        print("AI response:" ,assistant_response)
        return clean_response(assistant_response)

    except Exception as e:
        print(f"Error calling LLM: {str(e)}")
        return "I'm sorry, there was an issue processing your request. Please try again later."


def initialize_conversation_history():
    menus = Menu.objects.prefetch_related('categories__items').all()
    menu_text = []

    menu = get_menu()

    return [
        {
            "role": "system",
            "content": "You are a helpful restaurant assistant. Provide menu information without prices or descriptions"
                       "unless asked. When the order is complete, respond with: 'Okay, Thank you, I have received your "
                       "order and it's being prepared. [ORDER_CONFIRM]'. Do not include any additional text or menu "
                       "information in this final response."
        },
        {"role": "user", "content": "I would like to see the menu."},
        {"role": "system", "content": menu},
    ]


def clean_response(text):
    import re
    text = re.sub(r'###\s+', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    return text.strip()


def finalize_order(session_id, conversation_history):
    print("Finalizing order")

    print("Creating transcripts")
    transcript_instances = [
        Transcript(
            conversation_id=session_id,
            role=message["role"],
            content=message["content"]
        )
        for message in conversation_history
    ]
    Transcript.objects.bulk_create(transcript_instances)

    print("Create Order")

    order = Order(conversation_id=session_id)

    order_details = extract_order_details(conversation_history)
    print(order_details)

    if isinstance(order_details, str):
        order_details = json.loads(order_details)

    print("Create Order items")

    total_bill = 0

    try:
        with transaction.atomic():
            order.save()

            for item in order_details["items"]:
                try:
                    category_item = CategoryItem.objects.get(name=item["item_name"])

                    sub_total = item["price"] * item["quantity"]

                    OrderItem.objects.create(
                        order=order,
                        item=category_item,
                        quantity=item["quantity"],
                        sub_total=sub_total
                    )

                    total_bill += sub_total

                except CategoryItem.DoesNotExist:
                    print(f"Item '{item['item_name']}' not found in the menu.")

            order.total_bill = total_bill
            order.save()

    except Exception as e:
        print(f"Error creating order: {e}")
        return

    print(f"Order created successfully with total bill: {total_bill}")


def extract_order_details(conversation_history):
    print("Extracting order details")
    client = OpenAI(api_key=os.getenv('OPENAI_KEY'))

    menu = get_menu()

    prompt = f"""
    The following is the conversation between a customer and a Order automation system. Your task is to analyze this
    communication and extract the items that the customer wants to order. Do not assume anything. Menu is also attached
    below which will help you to find the items with their description and prices.\n
    You must only provide one json response. This json must contain all the items that must be included in the order.
    Each item will have 3 identifiers namely: item_name, quantity and price of that item. make sure that your response
    must not contain any extra characters or words.\n
    The json must look like the following:\n
    '{{"items": {{"item_name": "Chicken Corn Soup","quantity": 1,"price": 700.00}} }}'\n\n
    \n\n
    Menu:\n
    {menu}\n\n
    Conversation:\n
    {conversation_history}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
        ],
    )

    return response.choices[0].message.content


def get_menu():
    menus = Menu.objects.prefetch_related('categories__items').all()
    menu_text = []

    for menu in menus:
        menu_text.append(f"Restaurant: {menu.restaurant.name}")
        for category in menu.categories.filter(is_available=True):
            menu_text.append(f"  Category: {category.name}")
            for item in category.items.filter(is_available=True):
                menu_text.append(f"    - {item.name}: {item.description or 'No description'} (Price: ${item.price})")

    formatted_menu = "\n".join(menu_text)
    return formatted_menu

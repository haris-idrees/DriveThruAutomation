from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from openai import OpenAI
from django.views import View
from django.contrib.sessions.models import Session
from aaae.Menu.models import Menu


def home(request):
    # Initialize conversation history if it doesn't exist
    if not request.session.get('conversation_history'):
        request.session['conversation_history'] = initialize_conversation_history()
    return render(request, 'Order/take_order.html')


@csrf_exempt
def process_speech(request):
    if request.method == 'POST':
        try:
            if request.content_type != 'application/json':
                return JsonResponse({"error": "Content-Type must be application/json"}, status=400)

            data = json.loads(request.body)
            transcript = data.get('transcript', '')

            if not transcript:
                return JsonResponse({"error": "No transcription received"}, status=400)

            # Retrieve conversation history from session
            conversation_history = request.session.get('conversation_history', [])
            conversation_history.append({"role": "user", "content": transcript})

            # Generate response using LLM
            response_text = generate_response(conversation_history)

            # Append assistant's response to history
            conversation_history.append({"role": "assistant", "content": response_text})
            request.session['conversation_history'] = conversation_history  # Update session

            return JsonResponse({"response": response_text})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=400)


def initialize_conversation_history():
    menus = Menu.objects.prefetch_related('categories__items').all()
    menu_text = []

    for menu in menus:
        menu_text.append(f"Restaurant: {menu.restaurant.name}")
        for category in menu.categories.filter(is_available=True):
            menu_text.append(f"  Category: {category.name}")
            for item in category.items.filter(is_available=True):
                menu_text.append(f"    - {item.name}: {item.description or 'No description'} (Price: ${item.price})")

    formatted_menu = "\n".join(menu_text)

    return [
        {
            "role": "system",
            "content": "You are a helpful restaurant assistant. Provide menu information without prices or descriptions"
                       "unless asked. When the order is complete, respond with: 'Okay, Thank you, I have received your "
                       "order and it's being prepared. [ORDER_CONFIRM]'. Do not include any additional text or menu "
                       "information in this final response."
        },
        {"role": "user", "content": "I would like to see the menu."},
        {"role": "system", "content": formatted_menu},
    ]


def generate_response(conversation_history):
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_KEY'))

        print(conversation_history)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history
        )

        # Clean and return assistant's response
        assistant_response = response.choices[0].message.content
        return clean_response(assistant_response)

    except Exception as e:
        print(f"Error calling LLM: {str(e)}")
        return "I'm sorry, there was an issue processing your request. Please try again later."


def clean_response(text):
    import re
    text = re.sub(r'###\s+', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    return text.strip()


class OrderConfirmed(View):
    def get(self, request):
        return render(request, 'Order/order_confirmation.html')
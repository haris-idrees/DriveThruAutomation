from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from aaae.Menu.models import Menu
from openai import OpenAI
from gtts import gTTS
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()


def home(request):
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

            response = generate_response(transcript)

            return JsonResponse({"response": response})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=400)


def generate_response(user_text):
    menus = Menu.objects.prefetch_related('categories__items').all()
    menu_text = []

    for menu in menus:
        menu_text.append(f"Restaurant: {menu.restaurant.name}")
        for category in menu.categories.filter(is_available=True):
            menu_text.append(f"  Category: {category.name}")
            for item in category.items.filter(is_available=True):
                menu_text.append(f"    - {item.name}: {item.description or 'No description'} (Price: ${item.price})")

    formatted_menu = "\n".join(menu_text)

    conversation_history = [{"role": "system",
                             "content": "You are a helpful restaurant assistant. Your job is to take orders and help "
                                        "customers with menu information.\n"
                                        "While providing menu do not include price and description of the items."
                                        "Provide price and description only if asked by the customer."
                                        "Do not include menu in all responses. Provide concise and to the"
                                        "point responses.\n"
                                        "Once you have the items that a user want to order you must say 'Okay"
                                        "Thank you, I have received your order and its being prepared.'"},
                            {"role": "user", "content": "I would like to see the menu."},
                            {"role": "system", "content": formatted_menu}, {"role": "user", "content": user_text}]

    try:
        client = OpenAI(api_key=os.getenv('OPENAI_KEY'))

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history
        )

        assistance_response = response.choices[0].message.content
        assistance_response = clean_response(assistance_response)

        print("GBT response: ", assistance_response)

        conversation_history.append({"role": "assistant", "content": assistance_response})

        return response.choices[0].message.content

    except Exception as e:
        print(f"Error calling LLM: {str(e)}")
        return {}


def clean_response(text):
    # Remove markdown headers
    text = re.sub(r'###\s+', '', text)
    # Remove other markdown formatting if necessary
    text = re.sub(r'###\s+', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold formatting
    return text
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from aaae.Menu.models import Menu
from openai import OpenAI
from gtts import gTTS
import json

# Create your views here.


def home(request):
    return render(request, 'Order/take_order.html')


@csrf_exempt
def process_speech(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_text = data.get('transcription', '')

        print(f"Received transcription: {user_text}")

        response = generate_response(user_text)

        return JsonResponse({'response': response}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


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
                             "content": "You are a helpful restaurant assistant. Your job is to take orders and help customers with menu information."},
                            {"role": "user", "content": "I would like to see the menu."},
                            {"role": "system", "content": formatted_menu}, {"role": "user", "content": user_text}]

    try:
        client = OpenAI(api_key="sk-lIDgH6HO8tblP9FDTkakc-2xVAz_pj9E-tmKjUKtAjT3BlbkFJJDJmbgI-Na92VDktKZDHBxc9BWxg4PHzZtQHdtGikA")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history
        )

        assistance_response = response.choices[0].message.content

        print("GBT response: ", assistance_response)

        conversation_history.append({"role": "assistant", "content": assistance_response})

        return response.choices[0].message.content

    except Exception as e:
        print(f"Error calling LLM: {str(e)}")
        return {}

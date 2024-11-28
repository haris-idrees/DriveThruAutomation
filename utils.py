from aaae.Menu.models import Menu, CategoryItem
from aaae.Order.models import Transcript, Order, OrderItem
from django.conf import settings
from django.db import transaction
import os
import json
from openai import OpenAI
import uuid


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
        print("AI response:", assistant_response)
        return clean_response(assistant_response)

    except Exception as e:
        print(f"Error calling LLM: {str(e)}")
        return "I'm sorry, there was an issue processing your request. Please try again later."


def initialize_conversation_history():

    menu = get_menu()

    prompt = f""" 
    You are a professional virtual restaurant assistant with expertise in handling customer queries 
    efficiently and ensuring a smooth ordering process. Your primary goal is to assist customers by providing 
    relevant menu information and ensuring their orders are completed to satisfaction.

    **Guidelines for Interaction:**
        1.**Conciseness:** Provide only the information requested. If no prices or descriptions are explicitly asked  
            for, refrain from including them. However, always offer clear and structured answers.
        2.**Menu Categories:** When asked about the menu, respond with a list of categories (e.g., Appetizers, Burgers,
         Pastas). Prompt the customer to specify which category they are interested in.
        3.**Item Details:** If the customer selects a category, provide the items available in that category,
         ensuring clarity and focus.
        4.**Order Completion:** Take the complete order and confirm all items. Proactively ask, "Is there anything else
         you would like to add to your order?" before concluding.
        5.**Explicit Inquiry for Beverages and Desserts:**
            If the menu contains Beverages or Desserts and the customer has not selected any items from these
             categories, explicitly ask:
                - "Would you like to add any beverages to your order?"
                - "Would you like to add a dessert to your order?"
             Do not ask for these categories if they are not present in the menu.
                
        6.**Order Confirmation:** After confirming the order, provide the final acknowledgment in this exact format:
                 "Okay, thank you. I have received your order and it is being prepared. [ORDER_CONFIRM]". 
            Do not include additional text, menu details, or unnecessary information in this response.
    
    **Special Instructions:**
    The menu you are referring to is as follows:
    {menu}
    
    Adapt your responses based on customer inputs, maintaining professionalism and a helpful tone throughout.
    **Steps for Task Completion:**
    **Greet:** Start by welcoming the customer and offer your assistance.
    **Menu Guidance:** When a query about the menu arises, list categories and guide the customer towards making a choice.
    **Order Details:** If items within a category are requested, provide a concise and accurate list.
    **Order Review:** Before concluding, confirm the full order and inquire if anything else is needed.
    **Closure:** Deliver the confirmation message exactly as specified above and close the conversation on a polite note.
    
    Take a deep breath and work on this problem step-by-step.
    """

    conversation_history = [{"role": "system", "content": prompt}]

    return [
        {
            "role": "system",
            "content": prompt
        }
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


def response_to_audio(text):
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_KEY'))

        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
        )

        # Get the audio content as bytes
        audio_data = response.content

        # Generate a unique filename for the audio response
        audio_response_name = f'response_{uuid.uuid4().hex}.mp3'

        # Define the upload directory
        upload_dir = os.path.join(settings.MEDIA_ROOT)  # Use MEDIA_ROOT

        # Ensure the 'uploads' directory exists
        os.makedirs(upload_dir, exist_ok=True)

        # Save the audio file to the media directory
        file_path = os.path.join(upload_dir, audio_response_name)
        with open(file_path, "wb") as f:
            f.write(audio_data)

        # Return the media URL
        audio_url = settings.MEDIA_URL + audio_response_name
        return audio_url  # Return the URL instead of file_path

    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return None


import requests
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import uuid
from django.views import View
from django.contrib.sessions.models import Session
from aaae.Order.models import Order, OrderItem, Transcript
from utils import initialize_conversation_history, generate_response, finalize_order, response_to_audio


class Orders(View):
    def get(self, request):
        orders = Order.objects.select_related('restaurant').all()
        return render(request, 'Order/Orders.html', {'orders': orders})


class OrderDetail(View):
    """
    View to display order details
    """
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            print(item.item.price, item.item.name, item.quantity)
        return render(request, 'Order/order_detail.html', {'order': order, 'order_items': order_items})


class TakeOrder(View):
    """
    View to take an order
    """
    def get(self, request):

        # Clear session if already exists
        if request.session.get('session_id'):
            del request.session['session_id']
            del request.session['conversation_history']

        # Generate a new session id
        conversation_id = str(uuid.uuid4())
        request.session['session_id'] = conversation_id
        print("new session created")

        # Save conversation history with initial prompt in the session
        initial_prompt = initialize_conversation_history()
        request.session['conversation_history'] = initial_prompt

        return render(request, 'Order/take_order_2.html')


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

            # Append customer response to conversation history
            conversation_history.append({"role": "user", "content": transcript})

            # Generate response using LLM
            response_text = generate_response(conversation_history)

            # Append LLM's response to history
            conversation_history.append({"role": "assistant", "content": response_text})

            # Update conversation history in session
            request.session['conversation_history'] = conversation_history

            # Update conversation history in session
            request.session['conversation_history'] = conversation_history

            response_url = response_to_audio(response_text)

            # Check if conversation is ended
            if '[ORDER_CONFIRM]' in response_text:

                finalize_order(request.session['session_id'], conversation_history)

                print("Order finalized")

                print("Clear sessions")
                request.session.pop('conversation_history', None)
                request.session.pop('session_id', None)

                print("Going to confirmation page")

            return JsonResponse({
                "message": "Audio processed successfully!",
                "audio_url": response_url,
                "response_text": response_text,
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=400)


class OrderConfirmed(View):
    def get(self, request):
        return render(request, 'Order/order_confirmation.html')


class OrderTranscription(View):
    def get(self, request, conversation_id):
        conversation = Transcript.objects.filter(conversation_id=conversation_id)
        for text in conversation:
            print(text.role, ": ", text.content)

        return render(
            request, 'Order/order_transcription.html',
            {
                'conversation_id': conversation_id,
                'conversation': conversation
            }
        )

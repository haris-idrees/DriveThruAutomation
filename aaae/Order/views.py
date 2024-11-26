import requests
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import uuid
from django.views import View
from django.contrib.sessions.models import Session
from aaae.Order.models import Order, OrderItem, Transcript
from utils import initialize_conversation_history, generate_response, finalize_order


class Orders(View):
    def get(self, request):
        orders = Order.objects.select_related('restaurant').all()
        return render(request, 'Order/Orders.html', {'orders': orders})


class OrderDetail(View):
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            print(item.item.price, item.item.name, item.quantity)
        return render(request, 'Order/order_detail.html', {'order': order, 'order_items': order_items})


class TakeOrder(View):
    def get(self, request):

        del request.session['conversation_history']
        del request.session['session_id']

        # Generate a new session_id if it doesn't exist, to get unique identifier for conversation transcripts
        conversation_id = str(uuid.uuid4())

        # save this identifier in session
        if not request.session.get('session_id'):
            request.session['session_id'] = conversation_id
            print("new session created")
            print(request.session["session_id"])

        print("Existing session", request.session["session_id"])

        # Initialize conversation history if it doesn't exist
        if not request.session.get('conversation_history'):

            # Save conversation history with initial prompt in the session
            request.session['conversation_history'] = initialize_conversation_history()
            initial_prompt = initialize_conversation_history()

            # Save initial prompt to the conversation in database with a unique identifier
            for message in initial_prompt:
                Transcript.objects.create(
                    conversation_id=conversation_id,
                    role=message["role"],
                    content=message["content"]
                )

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

            # Append customer response to conversation history
            conversation_history.append({"role": "user", "content": transcript})

            # Generate response using LLM
            response_text = generate_response(conversation_history)

            if '[ORDER_CONFIRM]' in response_text:

                finalize_order(request.session['session_id'], conversation_history)

                print("Order finalized")

                print("Clear sessions")
                request.session.pop('conversation_history', None)
                request.session.pop('session_id', None)

                print("Going to confirmation page")

            # Append LLM's response to history
            conversation_history.append({"role": "assistant", "content": response_text})

            # Update conversation history in session
            request.session['conversation_history'] = conversation_history

            return JsonResponse({"response": response_text})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=400)


class OrderConfirmed(View):
    def get(self, request):
        return render(request, 'Order/order_confirmation.html')



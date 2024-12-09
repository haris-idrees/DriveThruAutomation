import requests
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import uuid
import time
from django.views import View
from django.contrib.sessions.models import Session
from aaae.Order.models import Order, OrderItem, Transcript
from utils import initialize_conversation_history, generate_response, finalize_order


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

        # Save initial prompt to the conversation in database with a unique identifier
        for message in initial_prompt:
            Transcript.objects.create(
                conversation_id=conversation_id,
                role=message["role"],
                content=message["content"]
            )

        return render(request, 'Order/take_order_2.html')


@csrf_exempt
def process_speech(request):
    start_time = time.time()  # Record the start time of the function
    total_step_time = 0  # Variable to track total time spent on all steps

    if request.method == 'POST':
        try:
            step_start_time = time.time()
            if request.content_type != 'application/json':
                return JsonResponse({"error": "Content-Type must be application/json"}, status=400)
            step_time = time.time() - step_start_time
            total_step_time += step_time
            print(f"Check Content-Type: {step_time:.6f} seconds")

            step_start_time = time.time()
            data = json.loads(request.body)
            step_time = time.time() - step_start_time
            total_step_time += step_time
            print(f"Parse JSON: {step_time:.6f} seconds")

            step_start_time = time.time()
            transcript = data.get('transcript', '')
            if not transcript:
                return JsonResponse({"error": "No transcription received"}, status=400)
            step_time = time.time() - step_start_time
            total_step_time += step_time
            print(f"Retrieve transcript: {step_time:.6f} seconds")

            step_start_time = time.time()
            conversation_history = request.session.get('conversation_history', [])
            step_time = time.time() - step_start_time
            total_step_time += step_time
            print(f"Retrieve conversation history: {step_time:.6f} seconds")

            step_start_time = time.time()
            conversation_history.append({"role": "user", "content": transcript})
            step_time = time.time() - step_start_time
            total_step_time += step_time
            print(f"Append user response: {step_time:.6f} seconds")

            step_start_time = time.time()
            response_text = "I am also good lets meet tonight.  "  # Simulated response
            step_time = time.time() - step_start_time
            total_step_time += step_time
            print(f"Generate response (LLM): {step_time:.6f} seconds")

            step_start_time = time.time()
            conversation_history.append({"role": "assistant", "content": response_text})
            step_time = time.time() - step_start_time
            total_step_time += step_time
            print(f"Append assistant response: {step_time:.6f} seconds")

            step_start_time = time.time()
            request.session['conversation_history'] = conversation_history
            step_time = time.time() - step_start_time
            total_step_time += step_time
            print(f"Update session: {step_time:.6f} seconds")

            if '[ORDER_CONFIRM]' in response_text:
                step_start_time = time.time()
                finalize_order(request.session['session_id'], conversation_history)
                step_time = time.time() - step_start_time
                total_step_time += step_time
                print(f"Finalize order: {step_time:.6f} seconds")

                step_start_time = time.time()
                request.session.pop('conversation_history', None)
                request.session.pop('session_id', None)
                step_time = time.time() - step_start_time
                total_step_time += step_time
                print(f"Clear sessions: {step_time:.6f} seconds")

            total_time = time.time() - start_time
            print(f"Total step time: {total_step_time:.6f} seconds")
            print(f"Total function execution time: {total_time:.6f} seconds")
            return JsonResponse({"response": response_text})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    total_time = time.time() - start_time
    print(f"Total function execution time: {total_time:.6f} seconds")
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

from django.shortcuts import render
from django.views import View
import uuid
from utils import initialize_conversation_history
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from django.conf import settings

# Create your views here.


class PlaceOrder(View):
    """
    View to take an order
    """
    def get(self, request):

        # # Clear session if already exists
        # if request.session.get('session_id'):
        #     del request.session['session_id']
        #     del request.session['conversation_history']
        #
        # # Generate a new session id
        # conversation_id = str(uuid.uuid4())
        # request.session['session_id'] = conversation_id
        # print("new session created")
        #
        # # Save conversation history with initial prompt in the session
        # initial_prompt = initialize_conversation_history()
        # request.session['conversation_history'] = initial_prompt

        return render(request, 'OpenAIRealtimeAPI/realtime_api.html')


@csrf_exempt
def process_recording(request):
    # Process the request and return a response
    if request.method == 'POST':
        print("Post request received")
        audio_file = request.FILES.get('audio_file')
        if audio_file:
            # Save the audio file to a desired location
            with open(os.path.join(settings.MEDIA_ROOT, 'recording.wav'), 'wb+') as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)
            return JsonResponse({'status': 'Audio file received and saved.'})
        else:
            return JsonResponse({'status': 'No audio file received.'})
    else:
        return JsonResponse({'status': 'Invalid request method.'})
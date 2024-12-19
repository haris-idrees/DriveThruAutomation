import websocket
import threading
from django.conf import settings


class SocketManager:
    _socket = None
    _lock = threading.Lock()

    @classmethod
    def get_socket(cls):
        with cls._lock:
            if cls._socket is None or not cls._is_socket_alive():
                cls._socket = cls._connect_to_openai()
            return cls._socket

    @classmethod
    def close_socket(cls):
        with cls._lock:
            if cls._socket:
                try:
                    cls._socket.close()
                except Exception as e:
                    print(f"Error closing WebSocket: {e}")
                cls._socket = None

    @classmethod
    def _is_socket_alive(cls):
        # Check if the socket is still open
        try:
            if cls._socket:
                cls._socket.send("ping")
                return True
        except:
            return False
        return False

    @classmethod
    def _connect_to_openai(cls):
        WS_URL = 'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01'
        API_KEY = settings.OPEN_AI_KEY
        try:
            ws = websocket.create_connection(
                WS_URL,
                header=[
                    f'Authorization: Bearer {API_KEY}',
                    'OpenAI-Beta: realtime=v1',
                    'language: en'
                ]
            )
            print("Connected to OpenAI WebSocket.")
            return ws
        except Exception as e:
            print(f"Failed to connect to OpenAI WebSocket: {e}")
            return None

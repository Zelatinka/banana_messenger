import asyncio
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Conversation, Message
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        asyncio.create_task(self.send_heartbeat())

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def send_heartbeat(self):
        while True:
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            await self.send(text_data=json.dumps({"type": "ping"}))
    
    async def disconnect(self, close_code):
        print(f"WebSocket disconnected with code {close_code}")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_content = text_data_json.get('message')  # Use .get() to avoid KeyError
            sender_id = text_data_json.get('sender_id')

            if not message_content or not sender_id:
                return 

            conversation = await self.get_conversation(self.conversation_id)
            sender = await self.get_user(sender_id)

            await self.save_message(conversation, sender, message_content)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'sender_id': sender_id,
                    'sender_username': sender.username,
                }
            )
        except Exception as e:
            raise
                
    async def video_signal(self, event):
        await self.send(text_data=json.dumps({
            'type': event['type'],
            'data': event['data'],
            'sourceUserId': event['sourceUserId'],
            'targetUserId': event['targetUserId'],
        }))

    async def chat_message(self, event):
        message = event['message']
        sender_id = event['sender_id']
        sender_username = event['sender_username']

        # Send the message to the WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender_id': sender_id,
            'sender_username': sender_username,
        }))

    @staticmethod
    async def get_conversation(conversation_id):
        return await Conversation.objects.aget(id=conversation_id)

    @staticmethod
    async def get_user(user_id):
        return await User.objects.aget(id=user_id)

    @staticmethod
    async def save_message(conversation, sender, content):
        return await Message.objects.acreate(
            conversation=conversation,
            sender=sender,
            content=content
        )
        
class VideoChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_id = None
        self.room_group_name = None
        self.pc = None  # Peer connection
        self.offer = None

    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'video_chat_{self.conversation_id}'

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Initialize the peer connection
        self.pc = RTCPeerConnection()

    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Close the peer connection
        if self.pc:
            await self.pc.close()

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)

            if data['type'] == 'offer':
                # Handle incoming offer
                await self.handle_offer(data)
            elif data['type'] == 'answer':
                # Handle incoming answer
                await self.handle_answer(data)
            elif data['type'] == 'candidate':
                # Handle ICE candidates
                await self.handle_candidate(data)
        except Exception as e:
            raise

    async def handle_offer(self, data):
        # Parse the offer
        offer = RTCSessionDescription(sdp=data['sdp'], type=data['type'])

        # Set the remote description
        await self.pc.setRemoteDescription(offer)

        # Create an answer
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)

        # Send the answer back to the client
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'video_signal',
                'data': {
                    'type': 'answer',
                    'sdp': self.pc.localDescription.sdp,
                    'type': self.pc.localDescription.type,
                },
                'targetUserId': data['senderId'],
            }
        )

    async def handle_answer(self, data):
        # Parse the answer
        answer = RTCSessionDescription(sdp=data['sdp'], type=data['type'])

        # Set the remote description
        await self.pc.setRemoteDescription(answer)

    async def handle_candidate(self, data):
        # Add ICE candidate
        candidate = RTCIceCandidate(
            sdp=data['candidate']['candidate'],
            sdpMid=data['candidate']['sdpMid'],
            sdpMLineIndex=data['candidate']['sdpMLineIndex']
        )
        await self.pc.addIceCandidate(candidate)

    async def video_signal(self, event):
        # Forward signaling messages to the client
        await self.send(text_data=json.dumps(event['data']))
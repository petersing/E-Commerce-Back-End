import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Chat_Channel_Record, MessageData
from User_Manager_API.models import Client
from datetime import datetime,timezone
from django.core.cache import cache
from typing import Optional
from channels_redis.pubsub import RedisPubSubChannelLayer

def Check_Exist_ChatRoom(Target: Client, self: Client) -> Chat_Channel_Record:
    if not (Target.is_anonymous):
        cache_record = cache.get('Chat:Channel:{}_{}_Channel'.format(self.username, Target.username))
        cache_record = cache.get('Chat:Channel:{}_{}_Channel'.format(Target.username, self.username)) if not cache_record else cache_record
        if (cache_record):
            return cache_record
        else:
            record = Chat_Channel_Record.objects.filter(User = Target).filter(User = self).last()
            if not record:
                record = Chat_Channel_Record()
                record.save()
                record.User.set([Target, self])
            cache.set('Chat:Channel:{}_{}_Channel'.format(self.username, Target.username), record, 3600)
            return record
    else:
        raise 

def Check_User_Exist(username: str):
    User = cache.get('Chat:User:{}'.format(username))
    if (User):
        return User
    else:
        User: Client = Client.objects.filter(username=username).only('username', 'pk').last()
        if User:
            cache.set('Chat:User:{}'.format(username), User, 3600)
            return User
        else:
            return AnonymousUser()

class ChatConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.User : Optional[Client] = None

    @staticmethod
    @database_sync_to_async
    def New_Message(Record : Chat_Channel_Record, message: str, Sender: Client, Type: str):
        new = MessageData(Message = message, Sender=Sender, Type=Type)
        new.save()
        Record.Record.add(new)
        return new

    async def connect(self):
        self.Chat_Room = {}
        try:
            self.User : Client= await self.scope['user']
            if (self.User.is_anonymous and self.scope['jti_code'] != self.User.Previous_Access_ID):
                raise
            else:
                cache.set('Chat:{}:Socket'.format(self.User.username), self.channel_name, None)
                await self.accept()
        except:
            await self.close(code=4004)

    async def disconnect(self, code):
        if self.User:
            cache.delete('Chat:{}:Socket'.format(self.User.username))

    # Receive message from WebSocket
    async def receive(self, text_data):
        message = json.loads(text_data)
        Target : Client = await database_sync_to_async(Check_User_Exist)(username=message['Target'])
        ChatRoom: Chat_Channel_Record = await database_sync_to_async(Check_Exist_ChatRoom)(Target, self.User)
        Target_Key = cache.get('Chat:{}:Socket'.format(Target.username), '')
        Time = datetime.now(timezone.utc)  ##### for create time (UTC Time)
        MessageRecord : MessageData = await self.New_Message(ChatRoom, message['Message'], self.User, message['Type'])

        Data = {'id': MessageRecord.pk ,'Date': str(Time.date()), 'Time': str(Time.time()), 
                'SenderName': self.User.username, "Message": message['Message'], 
                "ChatRoom": 'chat_' + '_'.join([Target.username, self.User.username]), "Type": 'String'}

        await self.channel_layer.send(Target_Key, {"type": 'chat_message','message': Data}) if (Target_Key != '') else None
        await self.channel_layer.send(self.channel_name, {"type": 'chat_message', 'message': Data})

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event['message']))
import asyncio
from datetime import datetime
import json
from django.http import HttpResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
import itertools
from .models import MessageData, ChatMessageFile, Chat_Channel_Record
from rest_framework.permissions import IsAuthenticated
from Authentication.Decorator import JWT_Authentication
from rest_framework import exceptions
from channels.layers import get_channel_layer
from django.core.cache import cache
from .consumers import Check_Exist_ChatRoom, Check_User_Exist
from typing import List
from django.conf import settings


#### require input {Target: target, Type: type}}
@api_view(["POST"])
@authentication_classes([JWT_Authentication])
@permission_classes([IsAuthenticated])
def Handle_Send_File(request):
    data = request.POST.dict()
    Target = Check_User_Exist(username=data['Target'])

    if len(request.FILES) == 0: #### Prevent client send empty list
        return HttpResponse(status=205)

    if Target:
        """
            Create Message to Server
        """
        ChatRoom = Check_Exist_ChatRoom(Target, request.user)
        MessageList = []
        FileList: List[ChatMessageFile] = []
        for i in itertools.chain.from_iterable([request.FILES.getlist(x) for x in request.FILES]):
            Message = MessageData(Message='Image', Sender=request.user, Type='Image')
            FileList.append(ChatMessageFile(File = i, Message = Message))
            MessageList.append(Message)
        MessageData.objects.bulk_create(MessageList)
        ChatMessageFile.objects.bulk_create(FileList)
        ChatRoom.Record.add(*MessageList)

        """
            Using Async Method to send message to client via Channel
        """
        channel_layer = get_channel_layer()
        Send_Message_List = []
        for i in FileList:
            Time = datetime.now()
            Data = {'id': i.pk, 'Date': str(Time.date()), 'Time': str(Time.time()), 
                    'SenderName': request.user.username, "Message": settings.IMAGE_SERVER_URL + str(i.File) , 
                    "ChatRoom": ChatRoom.Get_Channel_Name(), 'Type': 'Image'}
            UserCacheSocket = cache.get('Chat:{}:Socket'.format(request.user.username))
            TargetCacheSocket = cache.get('Chat:{}:Socket'.format(Target.username))
            Send_Message_List.append(channel_layer.send(UserCacheSocket, {"type": "chat.message",'message': Data}))
            Send_Message_List.append(channel_layer.send(TargetCacheSocket, {"type": "chat.message",'message': Data})) if TargetCacheSocket else None
        asyncio.run(asyncio.wait(Send_Message_List))

    else:
        raise exceptions.NotFound('User Not Found')
    return HttpResponse(status=200)

@api_view(["POST"])
@authentication_classes([JWT_Authentication])
@permission_classes([IsAuthenticated])
def Delete_Message(request):
    Data = request.POST.dict()
    Chat = Chat_Channel_Record.objects.filter(User = request.user, Record__pk = int(Data['id']))
    if (Chat.exists()):
        message = Chat.first().Record.get(pk = Data['id'])
        message.Type = 'Delete'
        message.save()
    else:
        raise exceptions.AuthenticationFailed('This message does not belong to you')
    return HttpResponse(status=200)

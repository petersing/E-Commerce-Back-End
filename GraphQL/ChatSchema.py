import graphene
from Authentication.Decorator import Check_JWT_Valid_GraphQL
import json
from User_Manager_API.models import Client
import datetime
from Chat_API.models import Chat_Channel_Record
from django.db.models import Q

class ChatQuery(graphene.ObjectType):
    ChatRecord = graphene.String(target= graphene.String(required=True), Start = graphene.Int(required=False), End = graphene.Int(required=False))
    ChatUserList = graphene.String()

    @Check_JWT_Valid_GraphQL
    def resolve_ChatRecord(self, info, **kwargs):
        Target = Client.objects.get(username = kwargs['target'])
        if (Target.username == kwargs['user'].username): 
            Time = datetime.now()
            return json.dumps({"Message": ['Not allowed to send messages to myself'], "Date": [str(Time.date())], "Time": [str(Time.time())], "Sender": ["Server"]})
        record = Chat_Channel_Record.objects.filter(Q(User= Target)).filter(Q(User=kwargs['user'])).last()
        if (record):
            record.Record.filter(Q(is_read=False), ~Q(Sender = kwargs['user'])).update(is_read=True) 
            MessageRecord = record.Record.prefetch_related('chatmessagefile_set', 'Sender').order_by('-date')[int(kwargs['Start']):int(kwargs['End'])]
            Data = [x.GetMessage() for x in MessageRecord]
            Data.reverse()
        else:
            Data = []
        return json.dumps(Data)

    @Check_JWT_Valid_GraphQL
    def resolve_ChatUserList(self, info, **kwargs):
        record = Chat_Channel_Record.objects.filter(User__in=[kwargs['user']]).select_related().all()
        Data = {}
        for x in record:
            result = x.Get_First_Item(kwargs['user'].username)
            if (result): Data[result[0]] = result[1]      
        return json.dumps(Data)
from django.db import models
from User_Manager_API.models import Client
from django.db.models import Q
import os
import time
from PIL import Image
from django.conf import settings

def file_directory_path(instance, filename):
    year, month, day= map(str, time.strftime("%Y %m %d").split())
    ext = filename.split('.').pop()
    filename = '{0}.{1}'.format(time.time(), ext)
    return os.path.join('Chat_File_DataBase', year, month, day, instance.Message.Sender.username ,filename)

##### Modify to match change Name
class MessageData(models.Model):
    Message = models.CharField(max_length=500)
    date = models.DateTimeField(auto_now_add=True, blank=True)
    Sender = models.ForeignKey(Client, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    Type = models.CharField(max_length=10, default='String')

    ###list(MessageRecord.values('Message','SenderName', Date = Cast('date__date', output_field=CharField()), Time= Cast('date__time', output_field=CharField())))
    def GetMessage(self):
        if self.Type == 'String':
            Message = self.Message
        elif self.Type == 'Image':
            Message = settings.IMAGE_SERVER_URL + str(self.chatmessagefile_set.all()[0].File)
        elif self.Type == 'Delete':
            Message = 'This Message Deleted'
        return {'id': self.pk, 'Message': Message, 'Date': str(self.date.date()), 'Time': str(self.date.time()), "SenderName": self.Sender.username, 'Type': self.Type}


class ChatMessageFile(models.Model):
    File = models.ImageField(upload_to= file_directory_path)
    Message = models.ForeignKey(MessageData, on_delete=models.CASCADE)

    def save(self, *args, **kwargs) -> None:
        instance = super(ChatMessageFile, self).save(*args, **kwargs)
        img = Image.open(self.File.path)
        img.thumbnail(settings.MAX_CHAT_FILE_SIZE)
        img.save(self.File.path)
        return instance

class Chat_Channel_Record(models.Model):
    User = models.ManyToManyField(Client, blank=True)
    Record = models.ManyToManyField(MessageData, blank=True)

    def Get_Channel_Name(self):
        User_Name_List = [x.username for x in self.User.all()]
        return 'chat_' + '_'.join(User_Name_List)

    def Get_First_Item(self, selfname):
        try:
            TargetName = self.User.filter(~Q(username = selfname)).first()
            FirstRecord = self.Record.latest('id')
            if (FirstRecord):
                return (TargetName.username,{"Message": FirstRecord.Message, 
                                            "Time": str(FirstRecord.date.time()), 
                                            "Date": str(FirstRecord.date.date()), 
                                            "Sender": FirstRecord.Sender.username, 
                                            'Read': self.Record.filter(Q(is_read = False), Q(Sender = TargetName)).count() if FirstRecord.Sender.username != selfname else 0})
        except Exception as e:
            return None
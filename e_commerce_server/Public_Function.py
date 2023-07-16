from io import BytesIO
import os
from PIL import Image
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
import stripe

def Create_Stripe_Payment(price):
    domain_url = 'http://localhost:3000/'
    checkout_session = stripe.checkout.Session.create(
            success_url= domain_url + 'Payment/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url= domain_url + 'Payment/cancel?session_id={CHECKOUT_SESSION_ID}',
            payment_method_types = ['card'],
            mode='payment',
            line_items=[
                    {
                    'name': 'E-Commerce-Payment',
                    'quantity': 1,
                    'currency': 'hkd',
                    'amount': '{}'.format(int(price)*100),
                    }
                ]
            )
    return {'URL': checkout_session['url'], "ID": checkout_session['id'], "payment_intent": checkout_session['payment_intent']}


def Convert_Internal_Image_To_Django_Style_File(file_path: str, Root_Path: str=settings.MEDIA_ROOT):
    Image_Name = file_path.split("/")[-1]
    Default_Image = Image.open(os.path.join(Root_Path, file_path))
    IOBuffer = BytesIO()
    Default_Image.save(IOBuffer, format=Default_Image.format)
    return InMemoryUploadedFile(IOBuffer, None, Image_Name, 'image/{}'.format(Default_Image.format), len(IOBuffer.getvalue()), None)


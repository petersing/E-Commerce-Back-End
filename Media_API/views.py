from PIL import Image
from django.http import HttpResponse
from rest_framework.decorators import api_view

@api_view(['GET'])
def Get_Image(request):
    Data = request.GET.dict()
    Size = (int(Data['Width']), int(Data['Width'])) if Data.get('Width', None) else None
    try: 
        with Image.open(request.path.split("/api/Media/Image/")[1]) as img:
            if Size : img.thumbnail(Size)
            Response = HttpResponse()  
            if "ProfileIcon_DataBase" in request.path: Response['Cache-Control'] = 'max-age=3600'
            else: Response['Cache-Control'] = 'max-age=100'
            if img.format == "ICO": 
                img.save(Response, "PNG")
                Response["Content-Type"] = "image/png"
            else:
                img.save(Response, img.format) 
                Response["Content-Type"] = "image/{}".format(img.format)
            return Response
    except:
        with Image.open("./Default/NotFound.png") as img:
            if Size : img.thumbnail(Size)
            Response = HttpResponse(content_type = 'image/{}'.format(img.format))
            if "ProfileIcon_DataBase" in request.path : Response['Cache-Control'] = 'max-age=3600'
            else: Response['Cache-Control'] = 'max-age=100'
            img.save(Response, img.format)
            return Response

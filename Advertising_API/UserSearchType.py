from Cache_Function.Caches import Resolve_Cache_Model_Field
from Product_API.models import Product
from django.core.cache import cache
import re
from typing import Optional, Dict, List


def User_Product_Preference(model: Product, id: int, adsToken: Optional[str]): #### This function should use Celery to calculate, in order to reduce the delay.
    if not adsToken:
        return
    Item_Data: Product = Resolve_Cache_Model_Field.Resolve_Model(model, id)
    Key = set(re.findall(r'[^\W\d\s]{2,}',Item_Data.ProductName))
    CategoryKeyWords: List[str] = Item_Data.Category.split('/')
    Key.update(CategoryKeyWords)
    UserAdsData: Dict[str: int] = cache.get('Ads:{}:Main'.format(adsToken), {"KeyWords": {}, "Searching": {}})
    while Key:
        item: str = Key.pop()
        if item.isalpha():
            try:
                UserAdsData['KeyWords'][item] = UserAdsData["KeyWords"].get(item, 0) + 1
            except:
                UserAdsData['KeyWords'] = {}
                UserAdsData['KeyWords'][item] = 1
    cache.set('Ads:{}:Main'.format(adsToken), UserAdsData, None)


def User_Searching_Preference(SearchItem: List[str], adsToken: Optional[str]):

    if not adsToken:
        return
        
    Key = set(re.findall(r'[^\W\d\s]{2,}'," ".join(SearchItem)))
    UserAdsData: Dict[str: int] = cache.get('Ads:{}:Main'.format(adsToken), {"KeyWords": {}, "Searching": {}})
    while Key:
        item: str = Key.pop()
        if item.isalpha():
            try:
                UserAdsData['Searching'][item] = UserAdsData["Searching"].get(item, 0) + 1
            except:
                UserAdsData['Searching'] = {}
                UserAdsData['Searching'][item] = 1
    cache.set('Ads:{}:Main'.format(adsToken), UserAdsData, None)




    

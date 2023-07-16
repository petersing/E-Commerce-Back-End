from typing import Union, List, Any, Dict
from django.core.cache import cache
from django.db.models import Q, Model, QuerySet, base

import numpy as np

class Resolve_Cache_Model_Field(object):

    @staticmethod
    def Resolve_Model(Field: base.ModelBase, Item_IDs: Union[int, List, np.ndarray], select_related = [], prefetch_related = [], Time = 1200):
        Field_Name = Field.__name__
        if isinstance(Item_IDs, (list, np.ndarray)):
            Final_Result = np.empty(len(Item_IDs), dtype=object)
            CacheDataList = set()
            for loc, id in enumerate(Item_IDs):
                item = cache.get('{}:{}:Item'.format(Field_Name, id))
                if item:
                    Final_Result[loc] = item
                    CacheDataList.add(id)
            QueryDataID = set(Item_IDs).difference(CacheDataList)
            if len(QueryDataID) > 0:
                try:
                    Item_list = Field.objects.filter(id__in = QueryDataID).select_related(*select_related).prefetch_related(*prefetch_related).all()         
                    for i in Item_list:
                        cache.set('{}:{}:Item'.format(Field_Name, i.pk), i, Time)
                        Location = np.where(Item_IDs == i.pk) if isinstance(Item_IDs, np.ndarray) else Item_IDs.index(i.pk)
                        Final_Result[Location] = i
                except Exception as e:
                    print(e)
                    raise Exception("This Item not exist")
            return Final_Result
        elif isinstance(Item_IDs, int):
            item = cache.get('{}:{}:Item'.format(Field_Name, Item_IDs))
            if item:
                return item
            else:
                try:
                    item = Field.objects.select_related(*select_related).prefetch_related(*prefetch_related).get(id = Item_IDs)
                    cache.set('{}:{}:Item'.format(Field_Name, Item_IDs), item, 1800)
                    return item
                except Exception as e:
                    print(e)
                    raise Exception("This Item not exist")
        else:
            raise TypeError('Only int & list are accepted')

class Query_Cache_Function(Resolve_Cache_Model_Field):

    def __init__(self, Queryset=None, Time=1200, Range=None, Random_Field = None, RandomLimitedRange = None,
                 Is_Cache_Result=None, Is_Model_Only = None, ID_Field=None, ParentCacheField=None, IgnoreCacheField = [],
                 prefetch_related=[], select_related=[], Order_by = [], ItemName = None, CustomCacheName=None) -> None:

        #### This is wanted to makesure the output of the query, For not Is_Model_Only and Is_Cache_Result , Please MUST include Queryset in Function
        self.Queryset = Queryset

        self.Time = Time
        """
            Data Receive. For Range ['Start', 'End'] this mean that 'Start' is a key of kwargs for graphql query which can achive a range for data cache
            For RandomLimitedRange and Random_Field, RandomLimitedRange is wanted to limit the range for cache data 
            Random_Field is a key of kwargs for graphql query which can achive a mount of random   
        """
        self.Range = Range
        self.RandomLimitedRange = RandomLimitedRange
        self.Random_Field = Random_Field

        #### Direct Cache result
        self.Is_Cache_Result = Is_Cache_Result

        #### For Cache which are only key response
        self.ID_Field = ID_Field

        ### For Cache which want to add  sublist to other parent
        self.ParentCacheField= ParentCacheField

        ####Ignore some kwargs to create cache
        self.IgnoreCacheField = IgnoreCacheField

        ###Django Query Optional
        self.prefetch_related = prefetch_related
        self.select_related = select_related
        self.Order_by = Order_by

        ###For Cache wihch are relate to other field
        self.ItemName = ItemName

        self.CustomCacheName = CustomCacheName


    @staticmethod
    def Force_Update(Field_Name, pk):
        cache.delete_pattern("{}:{}*".format(Field_Name, pk))

    def Parent_Field_Name(self, Path):
        if (Path.prev):
            return (self.Parent_Field_Name(Path.prev))
        else:
            return(Path.key)

    def Cache_Name_Function(self, *args, Variable_Limited = [], **kwargs):
        parent_path = self.Parent_Field_Name(args[1].path)
        if (args[0]):
            model_name = args[0].__class__.__name__
            field_name = args[1].field_name
            id = args[0].id
            return '{}:{}:{}_{}'.format(model_name, id, parent_path, field_name)
        else:
            if self.CustomCacheName:
                VariableName = self.CustomCacheName
            else:
                Variable = {x: kwargs[x] for x in kwargs if not x in Variable_Limited}
                VariableName = '_'.join([*Variable, *map(str, Variable.values())])
            return '{}:'.format(parent_path) + VariableName
    
    def Check_Range_Item(self, Data_List, Function_Kwargs):
        if self.Range:
            return Data_List[Function_Kwargs.get(self.Range[0]): Function_Kwargs.get(self.Range[1])]
        else:
            return Data_List

    def Random_Range(self, Data_List, fn_kwargs):
        try:
            if fn_kwargs.get(self.Random_Field, False):
                return np.random.choice(Data_List, fn_kwargs.get(self.Random_Field), replace=False)
            else:
                raise
        except:
            return Data_List

    def Resolve_CacheName(self, *args, **kwargs):
        Variable_Limited = [self.Random_Field] if self.Random_Field else self.Range
        Variable_Limited = [] if not Variable_Limited else Variable_Limited
        Variable_Limited = [*Variable_Limited, *self.IgnoreCacheField]
        CacheName =  self.Cache_Name_Function(Variable_Limited=Variable_Limited, *args, **kwargs)
        if self.ParentCacheField:
            CacheName = '{}:{}:'.format(kwargs[self.ParentCacheField].__class__.__name__, kwargs[self.ParentCacheField].pk) + CacheName  
        return CacheName

    def Resolve_Custom_Function(self,function, *args, **kwargs):
        CacheName = self.Resolve_CacheName(*args, **kwargs)
        result = cache.get(CacheName)  
        if result == None and self.Is_Cache_Result:
            result = function(*args, **kwargs)
            cache.set(CacheName, result, self.Time)
        elif self.Queryset:
            if result == None:
                result = function(*args, **kwargs)
                if not isinstance(result, (QuerySet)):
                    raise 'please output queryset'
                if self.RandomLimitedRange and self.Random_Field:
                    result = list(result.order_by(*self.Order_by).values_list('pk', flat=True)[:self.RandomLimitedRange])
                else:
                    result = list(result.order_by(*self.Order_by).values_list('pk', flat=True))
                cache.set(CacheName, result, self.Time)
            result = self.Check_Range_Item(result, kwargs)
            result = self.Random_Range(result, kwargs)
            result = self.Resolve_Model(Field=self.Queryset, Item_IDs=result, select_related=self.select_related, prefetch_related=self.prefetch_related, Time=self.Time) 
       # if len(result) == 0 : raise Exception('No Item Found In Requirement')
        return result

    def Resolve_Indicated_ItemName(self, function, *args, **kwargs):
        try:    
            CacheName = self.Resolve_CacheName(*args, **kwargs)  
            result = cache.get(CacheName)    
            if self.Queryset and self.ItemName:
                if result == None:
                    if self.RandomLimitedRange and self.Random_Field:
                        result = list(getattr(args[0], self.ItemName).order_by(*self.Order_by).values_list('pk', flat=True)[:self.RandomLimitedRange])
                    else:
                        result = list(getattr(args[0], self.ItemName).order_by(*self.Order_by).values_list('pk', flat=True).all())
                    cache.set(CacheName, result, self.Time)
                result = self.Check_Range_Item(result, kwargs)
                result = self.Random_Range(result, kwargs)
                result = self.Resolve_Model(Field=self.Queryset, Item_IDs=result, select_related=self.select_related, prefetch_related=self.prefetch_related, Time=self.Time)
            else:
                if result == None:
                    result = function(*args, **kwargs)
                    cache.set(CacheName, result, self.Time)
           #if len(result) == 0 : raise Exception('No Item Found In Requirement')
            return result
        except:
            return function(*args, **kwargs)

    def __call__(self, function) -> Any:
        def Wrapper(*args, **kwargs):
            try:
                if args[0]: ##### For Query Type 
                    return self.Resolve_Indicated_ItemName(function, *args, **kwargs)
                else: 
                    return self.Resolve_Custom_Function(function, *args, **kwargs)
            except Exception as e:
                print(e)
                return function(*args, **kwargs)
        return Wrapper


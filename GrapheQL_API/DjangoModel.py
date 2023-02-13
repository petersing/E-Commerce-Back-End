from django.db.models.base import ModelBase
from django.db import models


from django.db.models.fields.files import ImageField
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.db.models.fields.reverse_related import ManyToOneRel, ManyToManyRel
from django.db.models.fields import *
from django.db.models.fields.json import JSONField
from django.db.models.fields.mixins import FieldCacheMixin


from graphene.types.field import Field
from graphene.types.structures import List
from graphene.types.utils import yank_fields_from_attrs
from graphene.types.objecttype import ObjectTypeMeta
from graphene.types.json import JSONString
from graphene.types.datetime import DateTime
from graphene.types.scalars import String, Boolean, Int, BigInt, Float, ID
from graphene.types import ObjectType

import typing


Fields =   {"Special_Fields" : [ManyToManyRel, ManyToOneRel, ForeignKey, ManyToManyField],
            "Int_Fields" : [IntegerField, AutoField, BinaryField, PositiveIntegerField, PositiveSmallIntegerField, SmallAutoField, SmallIntegerField],
            "BigInt_Fields" : [BigAutoField, BigIntegerField, DecimalField, PositiveBigIntegerField],
            "Float_Fields" : [FloatField],
            "ID_Fields" : [UUIDField],
            "String_Fields" : [ImageField, CharField, CommaSeparatedIntegerField, EmailField, FilePathField, GenericIPAddressField, TextField, URLField],
            "JSON_Fields" : [JSONField],
            "Boolean_Fields" : [BooleanField],
            "Date_Fields" : [DateTimeField, DateField, DurationField, TimeField]}

class DjangoObjectType(ObjectType):
    model_name = {}
    WaitForFinish = {}

    @staticmethod
    def CheckType(target_field):
        for (type, fields) in Fields.items():
            if isinstance(target_field, tuple(fields)) and type == 'Special_Fields':
                return target_field
            elif isinstance(target_field, tuple(fields)):
                return type.split('_')[0]
                
    
    @classmethod
    def __init_subclass_with_meta__(cls, model: ModelBase =None, fields: typing.Union[str, typing.List] = "__all__", exclude: typing.List = [], interfaces=(), possible_types=(), default_resolver=None, _meta=None, **options,):
        if isinstance(fields, List) and isinstance(exclude, List):

            raise 'Can not input fields and exclude same time'

        cls.ModelName = model.__name__
        
        ModelOut = cls.get_model_graphene(model, fields, exclude)
        
        cls.model_name[model.__name__] = {'GrapheQL': cls}

        for i in ModelOut:
            setattr(cls, i, ModelOut[i])   
            
        super(DjangoObjectType, cls).__init_subclass_with_meta__(_meta=_meta, **options)

    @staticmethod
    def Convert_Field_Name(name: str):
        Split = name.split('_')
        if (len(Split) > 1):
            return Split[0] + Split[1].capitalize()
        else:
            return Split[0]

    @classmethod
    def get_model_graphene(cls, model, fields= '__all__', exclude= []):
        ModelFields = cls.get_model_fields(model, fields, exclude)
        out = {}
        for name, field in ModelFields:
            FieldType = cls.CheckType(field)   
            if isinstance(FieldType, FieldCacheMixin):
                if isinstance(FieldType, ForeignKey):
                    if name in cls.__dict__:
                        continue
                    elif cls.model_name.get(field.related_model.__name__):
                        out[field.name] = Field(cls.model_name[field.related_model.__name__]['GrapheQL'])
                    else:
                        #### For Default and initial the model for graphql
                        cls.WaitForFinish[field.related_model.__name__] = {model.__name__: name}
                        ModelFieldsData = ObjectTypeMeta(field.related_model.__name__, (ObjectType, ), cls.get_model_graphene(field.related_model))           
                        out[field.name] = Field(ModelFieldsData)
                elif isinstance(FieldType, ManyToManyField):
                    #### This want to make sure user can overrate the type
                    if name in cls.__dict__:
                        continue
                    elif cls.model_name.get(field.related_model.__name__):
                        out[field.name] = List(cls.model_name[field.related_model.__name__]['GrapheQL'])
                    else:
                        cls.WaitForFinish[field.related_model.__name__] = {model.__name__: name}
                        Link_Field = cls.get_model_graphene(field.related_model)
                        ModelFieldsData = ObjectTypeMeta(field.related_model.__name__, (ObjectType, ), {**Link_Field})     
                        out[field.name] = List(ModelFieldsData)

                    if cls.ModelName == model.__name__:
                        setattr(cls, 'resolve_{}'.format(name), lambda x, y : getattr(x, y.field_name).all())
                    else:
                        out['resolve_{}'.format(name)] =  lambda x, y : getattr(x, y.field_name).all()
                elif isinstance(FieldType, ManyToOneRel):
                    try:
                        rela = cls.model_name[field.related_model.__name__]['GrapheQL']._meta.fields
                        lack_data = cls.WaitForFinish[model.__name__][field.related_model.__name__]
                        rela.update(yank_fields_from_attrs({str(lack_data): Field(cls)}))
                    except:
                            pass
                elif isinstance(FieldType, ManyToManyRel):
                    try:
                        rela = cls.model_name[field.related_model.__name__]['GrapheQL']._meta.fields
                        lack_data = cls.WaitForFinish[model.__name__][field.related_model.__name__]
                        rela.update(yank_fields_from_attrs({str(lack_data): List(cls), 'resolve_{}'.format(lack_data): lambda x,y : getattr(x, y.field_name).all()}))
                    except:
                        pass
            else:
                if FieldType == "Int":
                    if name in cls.__dict__:
                        continue
                    else:
                        out[field.name] = Int()
                elif FieldType == "BigInt":
                    if name in cls.__dict__:
                        continue
                    else:
                        out[field.name] = BigInt()
                elif FieldType == 'Float':
                    if name in cls.__dict__:
                        continue
                    else:
                        out[field.name] = Float()
                elif FieldType == 'ID':
                    if name in cls.__dict__:
                        continue
                    else:
                        out[field.name] = ID()
                elif FieldType == "String":
                    if name in cls.__dict__:
                        continue
                    else:
                        out[field.name] = String()
                elif FieldType == 'JSON':
                    if name in cls.__dict__:
                        continue
                    else:
                        out[field.name] = JSONString()
                elif FieldType == 'Boolean':
                    if name in cls.__dict__:
                        continue
                    else:
                        out[field.name] = Boolean()
                elif FieldType == 'Date':
                    if name in cls.__dict__:
                        continue
                    else:
                        out[field.name] = DateTime()
                else:
                    print(type(field))
                    print('name: {}, Field: {}'.format(name, field))
                    related = field.related_model
                    print(related.__name__) if related else None
                    print('\n')
        return out
        
    @classmethod
    def get_model_fields(cls, model, fields, exclude):
        if isinstance(fields, list):
            local_fields = [(cls.Convert_Field_Name(field.name), field) for field in sorted(list(model._meta.fields) + list(model._meta.local_many_to_many)) if field.name in fields]
        else:
            local_fields = [(cls.Convert_Field_Name(field.name), field) for field in sorted(list(model._meta.fields) + list(model._meta.local_many_to_many)) if field.name not in exclude]

        # Make sure we don't duplicate local fields with "reverse" version
        local_field_names = [field[0] for field in local_fields]
        reverse_fields = cls.get_reverse_fields(model, local_field_names)


        all_fields = local_fields + list(reverse_fields)

        return all_fields

    @staticmethod
    def get_reverse_fields(model, local_field_names):
        for name, attr in model.__dict__.items():
            # Don't duplicate any local fields
            if name in local_field_names:
                continue

            # "rel" for FK and M2M relations and "related" for O2O Relations
            related = getattr(attr, "rel", None) or getattr(attr, "related", None)
            if isinstance(related, models.ManyToOneRel):
                yield (name, related)
            elif isinstance(related, models.ManyToManyRel) and not related.symmetrical:
                yield (name, related)
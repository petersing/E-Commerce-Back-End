import json
from requests import HTTPError
import six
from django.db import connection, transaction
from django.http import HttpResponse, HttpResponseNotAllowed
from django.http.response import HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.decorators.csrf import ensure_csrf_cookie
from typing import List

from graphql.error import GraphQLError

#from GraphQL.schema import schema
import importlib
from django.conf import settings

schema_path = settings.GRAPHENE['SCHEMA'].split('.')
Schema_Variable_Name = schema_path.pop(-1)
Schema_Module = importlib.import_module('.'.join(schema_path))
schema = getattr(Schema_Module, Schema_Variable_Name)

MUTATION_ERRORS_FLAG = "graphene_mutation_has_errors"

def set_rollback():
    atomic_requests = connection.settings_dict.get("ATOMIC_REQUESTS", False)
    if atomic_requests and connection.in_atomic_block:
        transaction.set_rollback(True)



### This Function is copy from graphene-django project, but since graphene-django have stop the project, so i decide to update this parts
class GraphQLView(View):
    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        """ Django GraphQL procedure

            1. Model to Fields and seperate ManytoMany and ForeignKey
            2. Identify the type of the Field
            3. convery the field to type and name
        """
        try:
            if request.method.lower() not in ("get", "post"):
                raise HTTPError(HttpResponseNotAllowed(["GET", "POST"], "GraphQL only supports GET and POST requests."))
            data = self.parse_body(request)

            result, status_code = self.get_response(request, data)
            return HttpResponse(
                status=status_code, content=result, content_type="application/json"
            )

        except HTTPError as e:
            response = e.response
            response["Content-Type"] = "application/json"
            response.content = self.json_encode(
                request, {"errors": [self.format_error(e)]}
            )
            return response

    def parse_body(self, request):
        content_type = self.get_content_type(request)
        if content_type == "application/graphql":
            return {"query": request.body.decode()}

        elif content_type == "application/json":
            # noinspection PyBroadException
            try:
                body = request.body.decode("utf-8")
            except Exception as e:
                raise HTTPError(HttpResponseBadRequest(str(e)))
            try:
                request_json = json.loads(body)
                assert isinstance(
                    request_json, dict
                ), "The received data is not a valid JSON query."

                return request_json
            except AssertionError as e:
                raise HTTPError(HttpResponseBadRequest(str(e)))
            except (TypeError, ValueError):
                raise HTTPError(HttpResponseBadRequest("POST body sent invalid JSON."))

        elif content_type in ["application/x-www-form-urlencoded",  "multipart/form-data",]:
            return request.POST
        return {}
    
    def json_encode(self, request, d, pretty=False):
        if not (pretty) and not request.GET.get("pretty"):
            return json.dumps(d, separators=(",", ":"))

        return json.dumps(d, sort_keys=True, indent=2, separators=(",", ": "))

    def get_response(self, request, data):
        query, variables, operation_name, id = self.get_graphql_params(request, data)

        execution_result = schema.execute(query, context_value=request, **{"variable_values": variables,"operation_name": operation_name})


        if getattr(request, MUTATION_ERRORS_FLAG, False) is True:
            set_rollback()

        status_code = 200
        if execution_result:
            response = {}

            if execution_result.errors:
                set_rollback()
                status_code = 400
                response["errors"] = [self.format_error(e) for e in execution_result.errors]
                
                
            else:
                response["data"] = execution_result.data

            result = self.json_encode(request, response)

        else:
            result = None

        return result, status_code

    @staticmethod
    def get_content_type(request):
        meta = request.META
        content_type = meta.get("CONTENT_TYPE", meta.get("HTTP_CONTENT_TYPE", ""))
        return content_type.split(";", 1)[0].lower()

    @staticmethod
    def get_graphql_params(request, data):
        query = request.GET.get("query") or data.get("query")
        variables = request.GET.get("variables") or data.get("variables")
        id = request.GET.get("id") or data.get("id")

        if variables and isinstance(variables, six.text_type):
            try:
                variables = json.loads(variables)
            except Exception:
                raise HTTPError(HttpResponseBadRequest("Variables are invalid JSON."))

        operation_name = request.GET.get("operationName") or data.get("operationName")
        if operation_name == "null":
            operation_name = None

        return query, variables, operation_name, id

    @staticmethod
    def format_error(error):
        if isinstance(error, GraphQLError):
            return error.message

        return {"message": six.text_type(error)}


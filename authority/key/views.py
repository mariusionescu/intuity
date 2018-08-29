import uuid

import jwt
from django.conf import settings
import jsonschema
from rest_framework import parsers
from rest_framework.response import Response
from rest_framework.views import APIView


def validate_token(func):
    def _decorated(view, request, *args, **kwargs):
        token = request.GET.get('token', '')
        if not token:
            return Response({'error': 'Missing authentication token'}, status=401)
        try:
            payload = jwt.decode(
                token,
                key=settings.SECRET_KEY,
                audience='authority',
                issuer='authority'
            )
        except (jwt.DecodeError, AttributeError, jwt.InvalidAudience, jwt.InvalidIssuer) as e:
            return Response({'error': e.message}, status=401)
        return func(view, request, payload, *args, **kwargs)
    return _decorated


class Key(APIView):
    parser_classes = (parsers.JSONParser,)

    schema = {
        'type': 'object',
        'properties': {
            'job_type': {
                'type': 'string',
                'enum': ['classification', 'clustering', 'regression']
            }
        },
        'required': ['job_type']
    }

    def get_view_name(self):
        return "Key"

    @validate_token
    def get(self, request, payload):
        return Response({'payload': payload})

    def post(self, request):

        try:
            jsonschema.validate(request.data, self.schema)
        except jsonschema.exceptions.ValidationError as e:
            return Response({'error': e.message})

        payload = {
            'uuid': str(uuid.uuid4()),
            'data': request.data,
            'iss': 'authority',
            'aud': ('authority', 'curiosity', 'intuity', 'activity')
        }
        return Response({'payload': payload, 'token': jwt.encode(payload, key=settings.SECRET_KEY)})






import jwt
from django.conf import settings
from django.shortcuts import Http404
from rest_framework import parsers
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.views import APIView

from training.models import Training
import logging

log = logging.getLogger('intuity.training.views')


def validate_token(func):
    def _decorated(view, request, *args, **kwargs):
        token = request.GET.get('token', '')
        try:
            payload = jwt.decode(token, key=settings.SECRET_KEY, audience='curiosity', issuer='authority')
        except (jwt.DecodeError, AttributeError, jwt.InvalidAudience, jwt.InvalidIssuer) as e:
            return Response({'error': e.message}, status=401)
        return func(view, request, payload, *args, **kwargs)

    return _decorated


class TrainingApi(APIView):
    parser_classes = (parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)

    def get_view_name(self):
        return 'Training'

    @validate_token
    def get(self, request, payload):
        try:
            training = Training.objects.get(pk=payload['uuid'])
        except Training.DoesNotExist:
            raise Http404

        return Response({'data': training.data_object, 'target': training.target_object})

    @validate_token
    def post(self, request, payload):
        log.debug('Received training request.')
        if type(request.data) is not dict:
            return Response({'error': 'Invalid input: dict expected'}, status=400)

        training, created = Training.objects.get_or_create(pk=payload['uuid'])

        accuracy = training.process(request.data)

        trainings = []
        for data, target in zip(training.data_object, training.target_object):
            trainings.append({'data': data, 'target': target})

        return Response({"records": len(trainings), 'accuracy': accuracy})

    @validate_token
    def delete(self, request, payload):
        return Response({})


class PredictionApi(APIView):
    parser_classes = (parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)

    @validate_token
    def post(self, request, payload):
        log.debug('Received prediction request.')
        if type(request.data) is not dict:
            log.debug('Invalid input: dict expected.')
            return Response({'error': 'Invalid input: dict expected'}, status=400)
        try:
            training = Training.objects.get(pk=payload['uuid'])
            log.debug('Found training with ID %s', training.pk)
        except Training.DoesNotExist:
            log.warning('Training with ID %s not found', payload['uuid'])
            raise Http404

        prediction = training.predict(request.data['data'])

        log.info('Prediction: %s', prediction)
        return Response({'prediction': prediction})

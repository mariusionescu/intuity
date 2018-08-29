import json

import jwt
from django.conf import settings
from django.shortcuts import Http404
from rest_framework import parsers
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.views import APIView

from observation.models import Observation, BadFormat, Question

import requests

import logging

log = logging.getLogger('curiosity.observation.views')


def validate_token(func):
    def _decorated(view, request, *args, **kwargs):
        token = request.GET.get('token', '')
        if not token:
            return Response({'error': 'Missing authentication token'}, status=401)
        try:
            payload = jwt.decode(token, key=settings.SECRET_KEY, audience='curiosity', issuer='authority')
        except (jwt.DecodeError, AttributeError, jwt.InvalidAudience, jwt.InvalidIssuer) as e:
            return Response({'error': e.message}, status=401)
        return func(view, request, payload, *args, **kwargs)

    return _decorated


class ObservationApi(APIView):
    """
    GET
        URL: /v1/observation/?token={token}
    POST
        URL: /v1/observation/?token={token}
        DATA: [{"data": {observation_json}, "target": {target_value}, ...]
    DELETE
        URL: /v1/observation/?token={token}
    """

    parser_classes = (parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)

    def get_view_name(self):
        return 'Observation'

    @validate_token
    def get(self, request, payload):
        try:
            observation = Observation.objects.get(pk=payload['uuid'])
        except Observation.DoesNotExist:
            raise Http404

        observations = []
        for data, target in zip(observation.data_object, observation.target_object):
            observations.append({'data': data, 'target': target})
        return Response(observations)

    @validate_token
    def post(self, request, payload):

        log.debug("Received observation request.")

        if type(request.data) is not list:
            log.warning("Invalid input: list expected.")
            return Response({'error': 'Invalid input: list expected'}, status=400)

        observation, created = Observation.objects.get_or_create(pk=payload['uuid'])

        if created:
            log.info("New observation with ID %s", observation.pk)
            observation.data_type = request.META['CONTENT_TYPE']
        else:
            log.info("Found observation with ID %s", observation.pk)

        try:
            observation.process(request.data)
        except BadFormat:
            return Response({'error': 'Invalid input: missing target'}, status=400)

        observations = []
        for data, target in zip(observation.data_object, observation.target_object):
            observations.append({'data': data, 'target': target})

        accuracy = requests.post(
            'http://localhost:8084/v1/training/?token={}'.format(request.GET['token']),
            json={
                'data': observation.data_normalized,
                'target': observation.target_normalized
            }
        )

        return Response({"records": len(observations), 'accuracy': accuracy.json()['accuracy']})

    @validate_token
    def delete(self, request, payload):

        try:
            observation = Observation.objects.get(pk=payload['uuid'])
        except Observation.DoesNotExist:
            raise Http404

        observation.delete()
        return Response({})


class QuestionApi(APIView):
    parser_classes = (parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)

    @validate_token
    def post(self, request, payload):
        if type(request.data) not in (dict, list):
            return Response({'error': 'Invalid input: dict or list are expected'}, status=400)

        observation = Observation.objects.get(pk=payload['uuid'])
        question = Question(request.data, observation)

        answer = requests.post(
            'http://localhost:8084/v1/prediction/?token={}'.format(request.GET['token']),
            json={
                'data': question.data_normalized,
            }
        )

        answer_object = answer.json()

        predictions = answer_object['prediction']
        answers = []
        for prediction in predictions:
            answers.append(observation.target_map[prediction])

        return Response({'answer': answers})

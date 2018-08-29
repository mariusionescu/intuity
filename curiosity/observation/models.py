from __future__ import unicode_literals

import json

from django.db import models
from django.utils import timezone
from sklearn import preprocessing
from sklearn.feature_extraction import DictVectorizer

import logging

log = logging.getLogger('curiosity.observation.models')


class BadFormat(Exception):
    pass


class Observation(models.Model):
    uuid = models.CharField(max_length=64, null=False, blank=False, primary_key=True)
    data = models.TextField(default='[]')
    features = models.TextField(default='[]')
    target = models.TextField(default='[]')
    data_type = models.CharField(max_length=32)
    date_created = models.DateTimeField(default=timezone.now)

    def process(self, data):
        log.debug("Start processing observation.")
        try:
            current_data = json.loads(self.data)
            log.debug("Found valid current data.")
        except ValueError:
            log.debug("Empty or invalid current data.")
            current_data = []

        try:
            current_target = json.loads(self.target)
            log.debug("Found valid current target.")
        except ValueError:
            log.debug("Empty or invalid current target.")
            current_target = []

        new_data = []
        new_target = []

        for l in data:
            try:
                new_target.append(l['target'])
                new_data.append(l['data'])
            except KeyError:
                raise BadFormat

        if new_data:
            log.debug("New data shape: %s x %s", len(new_data), len(new_data[0]))
            log.debug("New target shape: %s", len(new_target))

        if current_data:
            log.debug("Current data shape: %s x %s", len(current_data), len(current_data[0]))
            log.debug("Current target shape: %s", len(current_target))

        current_data.extend(new_data)
        current_target.extend(new_target)

        self.data = json.dumps(current_data)
        self.target = json.dumps(current_target)
        self.save()

    @property
    def target_normalized(self):
        le = preprocessing.LabelEncoder()
        le.fit(self.target_object)
        normalized = list(le.transform(self.target_object))
        if normalized:
            log.debug("Normalized target shape %s", len(normalized))
        return normalized

    @property
    def data_normalized(self):
        log.debug("Started observation normalization.")
        v = DictVectorizer(sparse=False)
        array = v.fit_transform(self.data_object)
        self.features = json.dumps(v.get_feature_names())
        self.save()
        log.debug("Found features %s", v.get_feature_names())
        log.debug("DATA %s", self.data_object)
        log.debug("ARRAY %s", array)
        log.debug("Normalized data array shape %s x %s", len(array), len(array[0]))
        normalized = map(list, map(list, array))
        if normalized:
            log.debug("Normalized data shape %s x %s", len(normalized), len(normalized[0]))

        return normalized

    @property
    def features_object(self):
        return json.loads(self.features)

    @property
    def data_object(self):
        return json.loads(self.data)

    @property
    def target_object(self):
        return json.loads(self.target)

    @property
    def target_map(self):
        return dict(zip(self.target_normalized, self.target_object))


class Question(object):

    def __init__(self, data_object, observation):
        self.data_object = data_object
        self.observation = observation

    @property
    def data_normalized(self):
        if type(self.data_object) is dict:
            return self.normalize(self.data_object)
        else:
            return map(self.normalize, self.data_object)

    def normalize(self, data):
        v = DictVectorizer(sparse=False)
        array = v.fit_transform(data)
        log.debug("Found features in question %s", v.get_feature_names())
        log.debug("Features in training %s", self.observation.features_object)
        log.debug("Normalized question value %s", array)

        normalized_list = []
        prediction_features = dict(zip(v.get_feature_names(), array[0]))
        for trained_feature in self.observation.features_object:
            if trained_feature in prediction_features:
                normalized_list.append(prediction_features[trained_feature])
            else:
                normalized_list.append(0)
        log.debug("Processed normalized question %s", normalized_list)
        return normalized_list




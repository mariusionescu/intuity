from __future__ import unicode_literals

from django.db import models
import json

from sklearn.svm import SVC, LinearSVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.cluster import AgglomerativeClustering, KMeans
import numpy as np

import logging

log = logging.getLogger('intuity.training.models')


class Training(models.Model):
    uuid = models.CharField(max_length=64, null=False, blank=False, primary_key=True)
    data = models.TextField(default='[]')
    target = models.TextField(default='[]')

    @property
    def data_object(self):
        return json.loads(self.data)

    @property
    def target_object(self):
        return json.loads(self.target)

    def process_clustering(self, data):
        log.debug("Saving data with shape %s x %s", len(data['data']), len(data['data'][0]))
        self.data = json.dumps(data['data'])
        log.debug("Saving target with shape %s", len(data['target']))
        self.target = json.dumps(data['target'])
        self.save()

        frequency = {}

        for n_clusters in (2, 3, 5):
            model = KMeans(n_clusters=n_clusters)

            model.fit(self.data_object)

            unique = set(model.labels_)

            log.debug('Cluster %s', model.labels_)

            clusters = {}
            for u in unique:
                clusters[str(u)] = list(model.labels_).count(u)
                log.debug("Frequency of %s - %s", u, clusters[str(u)])

            frequency[str(n_clusters)] = clusters

        return frequency

    def process_classification(self, data):
        log.debug("Saving data with shape %s x %s", len(data['data']), len(data['data'][0]))
        self.data = json.dumps(data['data'])
        log.debug("Saving target with shape %s", len(data['target']))
        self.target = json.dumps(data['target'])
        self.save()

        split = int(round((len(self.target_object) / 100.0) * 10))

        log.debug("Split value %s", split)

        classifier = KNeighborsClassifier(n_neighbors=2)
        # log.debug("Train data %s", np.array(self.data_object[:split]))
        # log.debug("Train target %s", np.array(self.target_object[:split]))
        classifier.fit(np.array(self.data_object[:split]), np.array(self.target_object[:split]))

        passed = 0
        failed = 0
        for test, result in zip(np.array(self.data_object[split:]), np.array(self.target_object[:split])):
            # log.debug("Test data %s", test)
            # log.debug("Test result %s", result)
            prediction = classifier.predict([test])
            if prediction[0] == result:
                passed += 1
            else:
                failed += 1
            log.debug("Test result %s, expected %s", prediction[0], result)
        log.debug("Passed %s, failed %s", passed, failed)
        accuracy = float(passed)/(float(passed) + float(failed)) * 100
        log.debug("Prediction accuracy %s", accuracy)
        return accuracy

    process = process_clustering

    def predict(self, data):

        log.debug("Starting prediction.")
        log.debug("Received sample %s", data)
        log.debug("Sample shape %s", len(data))
        classifier = SVC(gamma=0.001, C=100.)
        # log.debug("Data object %s", self.data_object)
        # log.debug("Target object %s", self.target_object)
        log.debug("Training data with shape %s x %s", len(self.data_object), len(self.data_object[0]))
        log.debug("Training target with shape %s", len(self.target_object))
        log.debug("Training array dimension %s", np.array(self.data_object).ndim)
        classifier.fit(np.array(self.data_object), np.array(self.target_object))
        data = np.array(data)
        log.debug("Sample array dimension %s", data.ndim)
        if data.ndim == 1:
            data = [data]
        return classifier.predict(data)

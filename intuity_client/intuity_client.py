import json
from datetime import datetime



class ElasticSearchLoader(object):

    def __init__(self, json_file, target, features=None, size=None):
        self.features = features or []
        self.target_name = target
        self.json_data = open(json_file).read()
        self.size = size

    @property
    def obj_data(self):
        return json.loads(self.json_data)

    @property
    def hits(self):
        if type(self.size) is int:
            return self.obj_data['hits']['hits'][:self.size]
        else:
            return self.obj_data['hits']['hits']

    @property
    def records(self):
        return [r['_source'] for r in self.hits]

    @property
    def data(self):
        d = []
        for r in self.records:
            if self.features:
                o = {}
                for f in self.features:
                    o[f] = r[f]
                    if type(r[f]) in (str, unicode):
                        try:
                            t = datetime.strptime(r[f], '%Y-%m-%dT%H:%M:%S.%f+00:00')
                            o[f] = t.hour
                        except Exception as e:
                            pass
            else:
                o = r.copy()
                del o[self.target_name]
            d.append(o)
        return d

    @property
    def target(self):
        d = []
        for r in self.records:
            d.append(r[self.target_name])
        return d

    @property
    def observations(self):
        o = []
        for data, target in zip(self.data, self.target):
            o.append({'data': data, 'target': target})
        return o

    @property
    def observations_json(self):
        return json.dumps(self.observations)

if __name__ == '__main__':

    e = ElasticSearchLoader(
        '../tmp/adblock.json',
        target='has_adblocker',
        features=('browser_name', 'browser_version', 'city',
                  'country', 'created_at', 'device_family', 'domain_id', 'ip', 'is_mobile', 'is_pc', 'is_tablet', 'os',
                  'os_version'
                  ),
        size=2000
    )

    print e.observations_json

import hashlib
import requests
from time import sleep
from random import randint
from fame.core.module import ProcessingModule


class GeneralError(Exception):
    def __init__(self, message='General Error.'):
        super(GeneralError, self).__init__(message)

class APIRateLimitError(Exception):
    def __init__(self, message='Rate limit exceeded.'):
        super(APIRateLimitError, self).__init__(message)

class APIBadRequest(Exception):
    def __init__(self, message='Bad request.'):
        super(APIBadRequest, self).__init__(message)

class APIUnauthorized(Exception):
    def __init__(self, message='Access is denied due to invalid token.'):
        super(APIUnauthorized, self).__init__(message)


class VirusTotalPub(ProcessingModule):
    name = "virustotal_pub"
    description = "Check file hash or url against VirusTotal database"
    #acts_on = ['url', 'file']
    config = [
        {
            'name': 'VT_API_KEY',
            'type': 'str',
            'description': 'VirusTotal API key'
        },
        {
            'name': 'VT_API_MAX_TRIES',
            'type': 'int',
            'description': 'How many times VirusTotal API should be quieried after hitting rate limit',
            'default': 10
        }
    ]
    counter = 1

    def _call_VT(self, resource, method):
        vt_api_url = 'https://www.virustotal.com/vtapi/v2/{method!s}/report'
        params = {'apikey': self.VT_API_KEY,
                  'resource': resource}
        results = dict()
        r = requests.get(url=vt_api_url.format(method=method), params=params)
        if r.status_code == 200:
            rjson = r.json()
            if rjson['response_code'] == 1:
                results['response_code'] = 1
                results['detections'] = u'{}/{}'.format(rjson['positives'], rjson['total'])
                results['scan_date'] = rjson['scan_date']
                results['vt'] = rjson['permalink']
                results['scan_details'] = rjson['scans']
            results['Raw'] = rjson
            return results
        elif r.status_code == 204:
            # try again and again until MAX_TRIES is hit
            if self.counter < self.VT_API_MAX_TRIES:
                self.counter += 1
                random_sleep = randint(16,20)
                self.log('warning', 'VirusTotal public API request rate limit exceeded. Trying again in {t} seconds [{count}/{max_tries}].'.format(t=random_sleep, count=self.counter, max_tries=self.VT_API_MAX_TRIES))
                sleep(random_sleep)
                self._call_VT(resource, method)
            else:
                raise APIRateLimitError
        elif r.status_code == 400:
            raise APIBadRequest
        elif r.status_code == 403:
            raise APIUnauthorized
        else:
            raise GeneralError('{}'.format(r.status_code))

    def each_with_type(self, target, obj_type):

        self.results = dict()
        if obj_type == 'url':
            method = 'url'
            resource = target
        elif obj_type == 'hash':
            return False
        else:
            method = 'file'
            # try to calculate target hash (assuming it is a file)
            h = hashlib.sha256()
            try:
                with open(target, 'rb') as f:
                    h.update(f.read())
                resource = h.hexdigest()
            except IOError:
                self.log('debug', 'No such file: {}'.format(target))
                return False
        try:
            self.results = self._call_VT(resource=resource, method=method)
        except APIRateLimitError:
            self.log('warning', 'VirusTotal public API request rate limit exceeded. Trying again later.')
            return False
        except APIUnauthorized:
            self.log('error', 'You have tried to perform calls to VirusTotal\'s functions for which you do not have the required privileges.')
            return False
        return True

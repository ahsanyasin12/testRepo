import requests
from urllib import quote_plus
from fame.core.module import ProcessingModule


class APIError(Exception):
    def __init__(self, message='API Error'):
        super(APIError, self).__init__(message)

class APIRateLimitError(Exception):
    def __init__(self, message='Rate limit exceeded.'):
        super(APIRateLimitError, self).__init__(message)

class APIUnauthorized(Exception):
    def __init__(self, message='Access is denied due to invalid token.'):
        super(APIUnauthorized, self).__init__(message)



class CymonAPI(object):
    ''' Slightly rewrittent cymon.io client lib. See orginal at https://github.com/eSentire/cymon-python '''

    def __init__(self, auth_token=None, endpoint='https://cymon.io/api/nexus/v1'):
        self.endpoint = endpoint
        self.session = requests.Session()
        self.session.headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
        }
        if auth_token:
            self.session.headers.update({'Authorization': 'Token {0}'.format(auth_token)})

    def _get(self, method, params=None):
        r = self.session.get(self.endpoint + method, params=params)
        if r.status_code == 401:
            raise APIUnauthorized()
        elif r.status_code == 429:
            raise APIRateLimitError()
        elif r.status_code == 500:
            raise APIError()
        return r

    def _post(self, method, params, headers=None):
        r = self.session.post(self.endpoint + method, data=json.dumps(params), headers=headers)
        if r.status_code == 401:
            raise APIUnauthorized()
        elif r.status_code == 429:
            raise APIRateLimitError()
        elif r.status_code == 500:
            raise APIError()
        return r

    def url_lookup(self, location):
        url = quote_plus(location).replace('%', '%25')
        print url
        r = self._get('/url/' + url)
        if r.status_code == 404:
            #return r.json()
            return {"Status": "URL not found"}
        return r.json()


class CymonIO(ProcessingModule):
    ''' checking file hash will available via APIv2 '''
    name = "cymon"
    description = "Check domain, url or IP address against Cymon.io service"
    acts_on = ['url']
    config = [
        {
            'name': 'CYMON_API_KEY',
            'type': 'str',
            'description': 'Cymon.io API key',
            'default': None
        },
    ]

    def each_with_type(self, target, obj_type):

        self.results = dict()

        if self.CYMON_API_KEY is None:
            cymon = CymonAPI()
        else:
            cymon = CymonAPI(self.CYMON_API_KEY)

        if obj_type == 'url':
            try:
                r = cymon.url_lookup(target)
            except APIError:
                self.log('error', 'Cymon.io API Error')
                return False
            except APIRateLimitError:
                self.log('error', 'Cymon.io public API request rate limit exceeded. Try again tomorrow.')
                return False
            except APIUnauthorized:
                self.log('error', 'Cymon.io unauthorized: Access is denied due to invalid token.')
                return False
            if 'Status' in r:
                self.results['Raw'] = r['Status']
            else:
                self.results = r

        return True
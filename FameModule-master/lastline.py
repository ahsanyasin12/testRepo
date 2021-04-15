# coding: utf8
import datetime
import json
import time
from urllib.parse import urljoin

try:
    import requests

    HAVE_REQUESTS = True
except ImportError:
    HAVE_REQUESTS = False

try:
    import ijson

    HAVE_IJSON = True
except ImportError:
    HAVE_IJSON = False

from fame.common.exceptions import ModuleInitializationError, ModuleExecutionError
from fame.core.module import ProcessingModule


class Lastline(ProcessingModule):
    useDevTestServer = "true"
    name = "lastline"
    description = "Submit the file to Lastline Sandbox."
    acts_on = ["executable", "word", "html", "rtf", "excel", "pdf", "javascript", "jar", "url", "powerpoint", "vbs"]

    config = [
        {
            'name': 'api_endpoint',
            'type': 'str',
            'default': 'http://127.0.0.1:8008/',
            'description': "URL of Lastline's API endpoint."
        },
        {
            'name': 'wait_timeout',
            'type': 'integer',
            'default': 5400,
            'description': 'Time in seconds that the module will wait for Lastline analysis to be over.'
        },
        {
            'name': 'wait_step',
            'type': 'integer',
            'default': 30,
            'description': "Time in seconds between two check of lastline's analysis status"
        },
        {
            'name': 'analysis_time',
            'type': 'integer',
            'default': 300,
            'description': 'Time (in seconds) during which the sample will be analyzed.',
            'option': True
        },
        {
            'name': 'username',
            'type': 'str',
            'default': 'none',
            'description': "Username for Lastline"
        },
        {
            'name': 'password',
            'type': 'str',
            'default': ' ',
            'description': "Passwort for Lastline."
        }
    ]

    def initialize(self):
        # Check dependencies
        if not HAVE_REQUESTS:
            raise ModuleInitializationError(self, "Missing dependency: requests")
        if not HAVE_IJSON:
            raise ModuleInitializationError(self, "Missing dependency: ijson")

    def each_with_type(self, target, file_type):
        self.log('info', "RunWithDEVTestServer!!!")
        # Set root URLs
        self.results = dict()

        options = self.define_options()

        #Todo submit file

        self.authenticate()

        # First, submit the file / URL
        self.submit_url(target, options)

        # Wait for analysis to be over
        self.wait_for_analysis()

        # Get report, and tag signatures
        self.process_report()

        # Add report URL to results
        # self.results['URL'] = urljoin(self.web_endpoint, "/analysis/{}/summary/".format(self.task_id))

        return True

    #Todo optionen überarbeiten
    def define_options(self):
        # if self.allow_internet_access:
        #     route = "internet"
        # else:
        route = "drop"

        return {
            'timeout': self.analysis_time,
            'enforce_timeout': True,
            'options': 'route={}'.format(route)
        }

    def authenticate(self):
        url = urljoin(self.api_endpoint, 'papi/login.json')
        print("sende Requst mit user:" +self.username +" und password:"+ self.password)
        response = requests.post(url, data=json.dumps({"username": self.username, "password": self.password}), headers={'content-type': 'application/json'})
        print("ResponseSucces is:" , response.json()['success'] )
        if(response.json()['success'] !="1"):
            print("can't authenticate on lastline!")
            raise ModuleExecutionError('Could not Login in Lastlline')

    def submit_url(self, target_url, options):
        url = urljoin(self.api_endpoint, '/papi/analysis/submit_url.json')
        options['url'] = target_url
        response = requests.post(url, data=json.dumps(options), headers={'content-type': 'application/json'})
        self.task_id = response.json()['data']['task_uuid']

    def wait_for_analysis(self):
        taskfound = 'false'
        # Format time to send Back to Server
        after = datetime.datetime.utcnow()
        after = after.strftime("%Y-%m-%d %H:%M:%S")
        moreData = "moreData"
        jsonHeaders = {'content-type': 'application/json'}

        waited_time = 0
        analyzeduuids = []
        while True:
            while True:
                url = urljoin(self.api_endpoint, 'analysis/get_completed.json')
                if self.useDevTestServer == "true":
                    # MoreData only need for DevServer
                    # Todo remove moreData
                    response = requests.post(url, data=json.dumps({moreData: 'nothing', "after": after}), headers=jsonHeaders)
                    after = response.json()["data"]["before"]
                    moreData = "noMore"
                else:
                    response = requests.post(url, data=json.dumps({"after": after}),headers=jsonHeaders)
                    after = response.json()["data"]["before"]

                # Add found Uuids to a List
                for uuid in response.json()['data']['tasks']:
                    analyzeduuids.append(uuid)
                # Are there more to fetch?
                if response.json()['data']['more_results_available'] != 1:
                    # No more uuids..
                    break
            for actualTask in analyzeduuids:
                if actualTask == self.task_id:
                    print("Break !!!")
                    taskfound = 'true'
                    # Found the UUID from task
                    break
            if taskfound == 'true':
                break
            elif waited_time > self.wait_timeout:
                # Timeout, we found nothing
                raise ModuleExecutionError('could not get report before timeout.')
            else:
                time.sleep(self.wait_step)
                waited_time += self.wait_step

        self.log('info', "Found Task-UUID!")

    def process_report(self):
        url = urljoin(self.api_endpoint, '/analysis/get_result.json')
        payload = {'uuid': self.task_id}
        response = requests.post(url, data=json.dumps(payload), headers={'content-type': 'application/json'})

        if response.status_code != 200:
            self.log('error', 'could not find report for task id {0}'.format(self.task_id))
        else:
            self.log('info', 'Next Step is Analyse of the Data!')
            self.extract_info(response)

    def extract_info(self, reportFullFromWeb):

        # Add Score
        data = reportFullFromWeb.json().get('data')
        print("Score", data['score'])
        self.results['score'] = float(data['score'])

        # report = data.get('report')
        reports = data.get('reports')

        # add signatures
        self.results['signatures'] = []
        for addreport in reports:
            # add Tags
            self.add_tag(addreport.get('description'))
            # Extract Signatures
            signature = dict()
            signature['description'] = addreport.get('description')
            signature['relevance'] = addreport.get('relevance')
            self.results['signatures'].append(signature)

        # add signatures
        # self.results['signatures'] = []
        # for signatures in report['activities']:
        #    #add Tags
        #    self.add_tag(signatures)
        #    #Extract Signatures
        #    signature = dict()
        #    signature['name'] = signatures
        #    self.results['signatures'].append(signature)

        # elif prefix in ["network.domains.item.domain", "network.hosts.item.ip", "network.http.item.uri"]:
        #     if value not in ["8.8.8.8", "8.8.4.4"]:
        # self.add_ioc(value)

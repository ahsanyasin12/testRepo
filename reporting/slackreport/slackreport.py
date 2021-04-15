from __future__ import unicode_literals
import json
import os

from utils import fileline, insertfile

from fame.common.exceptions import ModuleInitializationError
from fame.common.exceptions import ModuleExecutionError

from fame.core.module import ReportingModule

import subprocess
from os import path, remove
from distutils.spawn import find_executable

from fame.common.config import fame_config

try:
    import requests
    HAVE_REQUESTS = True
except ImportError:
    HAVE_REQUESTS = False

try:
    from weasyprint import HTML, CSS
    HAVE_WEASYPRINT = True
except ImportError:
    HAVE_WEASYPRINT = False

try:
    from defang import defang
    HAVE_DEFANG = True
except ImportError:
    HAVE_DEFANG = False


class SlackReport(ReportingModule):

    name = "slack_report"
    description = "Post report on Slack when an anlysis if finished."

    config = [
        {
            'name': 'channels',
            'type': 'str',
            'description': 'Slack channel(s) to share the report, separated by commas. Ex: CXYXZZZZ,CXYXWWWW'
        },
        {
            'name': 'legacy_token',
            'type': 'str',
            'description': 'Slack API legacy Token'
        },        
        {
            'name': 'fame_base_url',
            'type': 'str',
            'description': 'Base URL:PORT of your FAME instance, as you want it to appear in links. Ex: http://localhost:4200'
        },
        {
            'name': 'fame_api_key',
            'type': 'str',
            'description': 'API key of your FAME instance.'
        },
        {
            'name': 'proxy',
            'type': 'str',
            'default': '',
            'description': 'If you are behind a proxy, please provide it'
        },
        {
            'name': 'pdf_enabled',
            'type': 'bool',
            'default': False,
            'description': 'Enable PDF report instead of HTML'
        },
        {
            'name': 'zip_enabled',
            'type': 'bool',
            'default': False,
            'description': 'Enable higher privacy using compressed reports with password'
        },
        {
            'name': 'password',
            'type': 'str',
            'default': '!p4$$W0rD_',
            'description': 'Password used for encrypt report'
        },
    ]

    ### plugin methods ###

    def slackupload(self, object2upload, object_type, analysis):

        report = {'file': open(object2upload,'rb')}

        payload={
          "title":"{0}_report.{1}".format(analysis['_id'],object_type),
          "initial_comment": "Report of {0}\n<{1}/analyses/{2}|See the analysis on FAME>".format(
            defang(', '.join(analysis._file['names'])),
            self.fame_base_url,
            analysis['_id']
            ),
          "token": self.legacy_token, 
          "channels": [self.channels], 
        }

        r = requests.post("https://slack.com/api/files.upload", params=payload, files=report)

        print(">>> Report {0} sent to Slack").format(analysis['_id'])

    def htmlreport(self, analysis):
        url_analysis = "{0}/analyses/{1}".format(self.fame_base_url, analysis['_id'])        
        response = requests.get(url_analysis, stream=True, headers={'Accept': "text/html", 'X-API-KEY': self.fame_api_key})

        html_name = "report_{0}.html".format(analysis['_id'])
        html_file = path.join(fame_config.temp_path, html_name)

        with open(html_file, mode='wb') as file:
            file.write(response.content)

        environmentPath = os.path.dirname(os.path.abspath(__file__))
        css = os.path.join(environmentPath, 'styles/report.css')
        
        fileline(html_file, css, analysis)
        print(">>> HTML Report {0} generated").format(analysis['_id'])
        return html_file

    def pdfreport(self, html_obj, analysis):
        pdf_name = "report_{0}.pdf".format(analysis['_id'])
        pdf_file = path.join(fame_config.temp_path, pdf_name)
        HTML(html_obj).write_pdf(pdf_file)
        print(">>> PDF Report {0} generated").format(analysis['_id'])
        return pdf_file

    def compress(self, archive, analysis):
        archive_name = "report_{0}.zip".format(analysis['_id'])
        archive_file = path.join(fame_config.temp_path, archive_name)
        subprocess.call(["7z", "a", "-tzip", "-p{0}".format(self.password), archive_file, archive])
        return archive_file        

    ### /plugin methods ###

    def initialize(self):
        if ReportingModule.initialize(self):
            if not HAVE_REQUESTS:
                raise ModuleInitializationError(self, "Missing dependency: requests")

            if not HAVE_DEFANG:
                raise ModuleInitializationError(self, "Missing dependency: defang")

            if not HAVE_WEASYPRINT:
                raise ModuleInitializationError(self, "Missing dependency: weasyprint")

            if find_executable("7z") is None:
                raise ModuleInitializationError(self, "Missing dependency: 7z")

            return True

        else:
            return False


    def done(self, analysis):
 
        html_file = self.htmlreport(analysis)

        ### PDF Report
        if self.pdf_enabled:

            pdf_file = self.pdfreport(html_file, analysis)

            ### Zipped
            if self.zip_enabled:

                archive_file = self.compress(pdf_file, analysis)
                self.slackupload(archive_file, 'zip', analysis)
                remove(archive_file)

            else:
                self.slackupload(pdf_file,'pdf',analysis)

            remove(pdf_file)
        
        ### HTML Report
        else:
            ### Zipped
            if self.zip_enabled:

                archive_file = self.compress(html_file, analysis)
                self.slackupload(archive_file,'zip',analysis)
                remove(archive_file)

            else:
                self.slackupload(html_file,'html',analysis)
            
        remove(html_file)

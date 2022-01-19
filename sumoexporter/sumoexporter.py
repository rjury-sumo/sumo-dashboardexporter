import logging
import sys
import json
import time
import requests
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path

try:
    import cookielib
except ImportError:
    import http.cookiejar as cookielib

LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=LOGLEVEL,
    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger()

class sumoexporter(object):
    def __init__(self, accessId=os.environ.get('SUMO_ACCESS_ID'), accessKey=os.environ.get('SUMO_ACCESS_KEY'), endpoint=None, caBundle=None, cookieFile='cookies.txt'):
        self.session = requests.Session()
        self.session.auth = (accessId, accessKey)
        self.DEFAULT_VERSION = 'v2'
        self.session.headers = {'content-type': 'application/json', 'accept': '*/*'}
        if caBundle is not None:
            self.session.verify = caBundle
        cj = cookielib.FileCookieJar(cookieFile)
        self.session.cookies = cj
        if endpoint is None:
            self.endpoint = self._get_endpoint()
        elif len(endpoint) <3:
            self.endpoint = 'https://api.' + endpoint + '.sumologic.com/api'
        else:
            self.endpoint = endpoint
        if self.endpoint[-1:] == "/":
            raise Exception("Endpoint should not end with a slash character")

    def _get_endpoint(self):
        """
        SumoLogic REST API endpoint changes based on the geo location of the client.
        For example, If the client geolocation is Australia then the REST end point is
        https://api.au.sumologic.com/api/v1
        When the default REST endpoint (https://api.sumologic.com/api/v1) is used the server
        responds with a 401 and causes the SumoLogic class instantiation to fail and this very
        unhelpful message is shown 'Full authentication is required to access this resource'
        This method makes a request to the default REST endpoint and resolves the 401 to learn
        the right endpoint
        """

        self.endpoint = 'https://api.sumologic.com/api'
        self.response = self.session.get('https://api.sumologic.com/api/v1/collectors')  # Dummy call to get endpoint
        endpoint = self.response.url.replace('/v1/collectors', '')  # dirty hack to sanitise URI and retain domain
        print("SDK Endpoint", endpoint, file=sys.stderr)
        return endpoint

    def get_versioned_endpoint(self, version):
        return self.endpoint+'/%s' % version

    def delete(self, method, params=None, version=None):
        version = version or self.DEFAULT_VERSION
        endpoint = self.get_versioned_endpoint(version)
        r = self.session.delete(endpoint + method, params=params)
        if 400 <= r.status_code < 600:
            r.reason = r.text
        r.raise_for_status()
        return r

    def get(self, method, params=None, version=None):
        version = version or self.DEFAULT_VERSION
        endpoint = self.get_versioned_endpoint(version)
        r = self.session.get(endpoint + method, params=params)
        if 400 <= r.status_code < 600:
            r.reason = r.text
        r.raise_for_status()
        return r

    def get_file(self, method, params=None, version=None, headers=None):
        version = version or self.DEFAULT_VERSION
        endpoint = self.get_versioned_endpoint(version)
        r = self.session.get(endpoint + method, params=params, headers=headers)
        if 400 <= r.status_code < 600:
            r.reason = r.text
        r.raise_for_status()
        return r

    def post(self, method, params, headers=None, version=None):
        version = version or self.DEFAULT_VERSION
        endpoint = self.get_versioned_endpoint(version)
        r = self.session.post(endpoint + method, data=json.dumps(params), headers=headers)
        if 400 <= r.status_code < 600:
            r.reason = r.text
        r.raise_for_status()
        return r

    def post_file(self, method, params, headers=None, version=None):
        """
        Handle file uploads via a separate post request to avoid having to clear
        the content-type header in the session.
        Requests (or urllib3) does not set a boundary in the header if the content-type
        is already set to multipart/form-data.  Urllib will create a boundary but it
        won't be specified in the content-type header, producing invalid POST request.
        Multi-threaded applications using self.session may experience issues if we
        try to clear the content-type from the session.  Thus we don't re-use the
        session for the upload, rather we create a new one off session.
        """
        version = version or self.DEFAULT_VERSION
        endpoint = self.get_versioned_endpoint(version)
        post_params = {'merge': params['merge']}
        file_data = open(params['full_file_path'], 'rb').read()
        files = {'file': (params['file_name'], file_data)}
        r = requests.post(endpoint + method, files=files, params=post_params,
                auth=(self.session.auth[0], self.session.auth[1]), headers=headers)
        if 400 <= r.status_code < 600:
            r.reason = r.text
        r.raise_for_status()
        return r

    def put(self, method, params, headers=None, version=None):
        version = version or self.DEFAULT_VERSION
        endpoint = self.get_versioned_endpoint(version)
        r = self.session.put(endpoint + method, data=json.dumps(params), headers=headers)
        if 400 <= r.status_code < 600:
            r.reason = r.text
        r.raise_for_status()
        return r

    def dashboards(self, monitors=False):
        params = {'monitors': monitors}
        r = self.get('/dashboards', params)
        return json.loads(r.text)['dashboards']

    def dashboard(self, dashboard_id):
        r = self.get('/dashboards/' + str(dashboard_id))
        return json.loads(r.text)['dashboard']

    def dashboard_data(self, dashboard_id):
        r = self.get('/dashboards/' + str(dashboard_id) + '/data')
        return json.loads(r.text)['dashboardMonitorDatas']

    def export_dashboard(self,body):
        r = self.post('/dashboards/reportJobs', params=body, version='v2')
        job_id = json.loads(r.text)['id']
        logger.debug (f"started job: {job_id}")
        return job_id

    def check_export_dashboard_status(self,job_id):
        r = self.get('/dashboards/reportJobs/%s/status' % (job_id), version='v2')
        response = {
            "result": json.loads(r.text),
            "job": job_id
        }
        return response

    def get_export_dashboard_result(self,job_id):
        r = self.get_file(f"/dashboards/reportJobs/{job_id}/result", version='v2',headers={'content-type': 'application/json', 'accept': '*/*'})
        response = {
            "job": job_id,
            "format": r.headers["Content-Type"],
            "bytes": r.content
        }
        logger.debug (f"returned job file type: {response['format']}")
        return response

    def define_export_dashboard_job(self,report_id,timezone="America/Los_Angeles",exportFormat='Pdf'):
        payload = { 
            "action": { 
                "actionType": "DirectDownloadReportAction"
                },
            "exportFormat": exportFormat,
            "timezone": timezone,
            "template": { 
                "templateType": "DashboardTemplate",
                "id": report_id
                }
        }

        return payload

    def poll_export_dashboard_job(self,job_id,tries=60,seconds=1):
        progress = ''
        tried=0

        while progress != 'Success' and tried < tries:
            tried += 1
            r = self.check_export_dashboard_status(job_id)
            progress = r['result']['status']
            time.sleep(seconds)
        
        logger.debug(f"{tried}/{tries} job: {job_id} status is: {r['result']['status']}")

        r['tried'] = tried
        r['seconds'] = tried * seconds
        r['tries'] = tries
        r['max_seconds'] = tries * seconds
        return r

    def run_dashboard_export_job(self,report_id,timezone="America/Los_Angeles",exportFormat='Pdf',tries=120,seconds=1):
        payload = self.define_export_dashboard_job(report_id,timezone=timezone,exportFormat=exportFormat)  
        job = self.export_dashboard(payload)
        logger.info (f"started job: {job}")
        poll_status = self.poll_export_dashboard_job(job,tries=tries,seconds=seconds)
        if poll_status['result']['status'] == 'Success':
            export = self.get_export_dashboard_result(job)
        else:
            logger.warn(f"job was not successful in {tries} poll attempts")
            export = {
                'job': job
            }
        export['id'] = report_id
        export['status'] = poll_status['result']['status']
        export['poll_status'] = poll_status
        return export

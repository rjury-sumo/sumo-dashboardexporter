
from sumoexporter.sumoexporter import sumoexporter
import json
import sys
import time
import logging
import re
import os

logger = logging.getLogger()
logging.basicConfig()
logger.setLevel('DEBUG')

exporter = sumoexporter(endpoint='au')
id = 'TlVzZzMS2yRowxt3VdZah2uMXTDDKCLUVPvAG4pe5u32ywgDLJ2i3cBPHLbB'
os.environ['jobid'] = ''

class Test_defineJob:
    def test_run(self):
        assert 1 == 1

    def test_define_export_dashboard_job(self):
        expected = json.loads(r'''{
  "action": {
    "actionType": "DirectDownloadReportAction"
  },
  "exportFormat": "Pdf",
  "timezone": "America/Los_Angeles",
  "template": {
    "templateType": "DashboardTemplate",
    "id": "abc"
  }
}
''')
        assert exporter.define_export_dashboard_job('abc') == expected

    def test_define_export_with_params(self):

        expected = json.loads(r'''
{
  "action": {
    "actionType": "DirectDownloadReportAction"
  },
  "exportFormat": "Png",
  "timezone": "Etc/UTC",
  "template": {
    "templateType": "DashboardTemplate",
    "id": "abc"
  }
}''')
        assert exporter.define_export_dashboard_job(
            'abc', timezone="Etc/UTC", exportFormat='Png') == expected

class TestStartJob:
    def test_create_job(self):
        #id = 'TlVzZzMS2yRowxt3VdZah2uMXTDDKCLUVPvAG4pe5u32ywgDLJ2i3cBPHLbB'
        payload = exporter.define_export_dashboard_job(id)  
        job = exporter.export_dashboard(payload)
        logger.info (f"started job: {job}")
        os.environ['jobid'] = job
        assert re.match(r'[A-F0-9]{16}',job)

    def test_have_job_id(self):
        assert re.match(r'[A-F0-9]{16}',os.environ['jobid'])

    def test_poll_job(self):
        job = os.getenv('jobid')
        poll_status = exporter.poll_export_dashboard_job(job)
        completion = poll_status['result']['status']
        assert completion == 'Success'

    def test_get_job_result(self):
        job = os.getenv('jobid')
        export = exporter.get_export_dashboard_result(job)
        assert export['format'] == 'application/pdf'

    def test_run_dashboard_export_job(self):
        export = exporter.run_dashboard_export_job(id,timezone="America/Los_Angeles",exportFormat='Pdf')
        assert export['status'] == 'Success'

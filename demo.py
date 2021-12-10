import json
import sys
import time
import logging
import os

logger = logging.getLogger()
logging.basicConfig()
logger.setLevel('INFO')

from sumoexporter.sumoexporter import sumoexporter
exporter=sumoexporter(endpoint='au')

id = 'TlVzZzMS2yRowxt3VdZah2uMXTDDKCLUVPvAG4pe5u32ywgDLJ2i3cBPHLbB'
export = exporter.run_dashboard_export_job(id,timezone="America/Los_Angeles",exportFormat='Pdf')

if export['status'] != 'Success':
    logger.error (f"job: {export['job']} status failure: {export['status']}")
    logger.error (json.dumps(export['poll_status']))
else:
    if export['format'] == 'application/png':
        ext = 'png'
    else:
        ext = 'pdf'

    filename = f"./export/{export['job']}.{ext}"
    logger.info (f"writing file: {filename}")

    f = open(filename, "wb")
    f.write(export['bytes'])
    f.close()


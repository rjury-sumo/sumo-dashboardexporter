# sumo-dashboardexporter
Export dashboards to pdf or png using the new report API
see: https://api.au.sumologic.com/docs/#operation/generateDashboardReport

example to export a dashboard as a pdf

requires env vars as below:
- LOGLEVEL optional python log level
- SUMO_ACCESS_ID
- SUMO_ACCESS_KEY
- export directory 

```
from sumoexporter.sumoexporter import sumoexporter
exporter=sumoexporter(endpoint='au')

id = 'TlVzZzMS2yRowxt3VdZah2uMXTDDKCLUVPvAG4pe5u32ywgDLJ2i3cBPHLbB'
export = exporter.run_dashboard_export_job(id,timezone="America/Los_Angeles",exportFormat='Pdf')

if export['status'] == 'Success':
    if export['format'] == 'application/png':
        ext = 'png'
    else:
        ext = 'pdf'

    filename = f"./export/{export['job']}.{ext}"

    f = open(filename, "wb")
    f.write(export['bytes'])
    f.close()

```

# todo
- parameters for creds, endpoint, retries, poll seconds etc
- support more parts of possible payload: arguments etc
- report mode
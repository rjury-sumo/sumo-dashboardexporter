# sumo-dashboardexporter
Export dashboards to pdf or png using the new report API
see: https://api.au.sumologic.com/docs/#operation/generateDashboardReport

example to export a dashboard as a pdf
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

import sys
if sys.version_info.major >= 3:
    from sumoexporter.sumoexporter import *
else:
    from sumoexporter import *
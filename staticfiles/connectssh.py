from Toptica_ophyd import LaserToptica
from XMLGenerator import xml_config_to_dict
toptica_host = xml_config_to_dict("staticfiles/toptica.xml")
LTDLC = LaserToptica(prefix="...",name="LTDLC",host= "129.129.131.136")

import time
while True:
    print(LTDLC.try_connect())
    time.sleep(2)
    LTDLC.disconnect()
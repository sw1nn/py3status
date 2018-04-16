#!/home/neale/.virtualenvs/py3status/bin/python

"""
Huawei

Displays the status of a Huawei E3785 mifi module

Configuration parameters:
    signal_chars: characters to display for signal strength
       (default "⁰¹²³⁴⁵")
    format_up: format of output
       (default "{signal_icon} {current_network_type}")
    format_down: format when down
       (default "Modem Not found")
    bad_threshold: threshold for 'bad' signal
       (default 2)
    degraded_threshold threshold for 'degraded' signal
       (default 3)

Format placeholders:
    {quota_left}
    {quota_total}
    {quota_days}
    {quota_hours} the hours in last day.

Examples:
```
huawei {
    format_up= "H:{signal_icon} {current_network_type}")
    format_down=""
}
```

Requires:
    requests

@author <Neale Swinnerton>
@license BSD
"""

import re
import xml.etree.ElementTree as ET
import requests


first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')

def convert(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


GSM = "1"
GPRS = "2"
EDGE = "3"
WCDMA = "4"
HSDPA = "5"
HSUPA = "6"
HSPA = "7"
TDSCDMA = "8"
HSPA_PLUS = "9"
EVDO_REV_0 = "10"
EVDO_REV_A = "11"
EVDO_REV_B = "12"
RTT = "13"
UMB = "14"
EVDV = "15"
RTT = "16"
HSPA_PLUS_64QAM = "17"
HSPA_PLUS_MIMO = "18"
LTE = "19"

NO_SERVICE = set("0")
NET_2G = set([GSM, GPRS, EDGE, RTT, EVDV])
NET_3G = set([WCDMA, TDSCDMA, EVDO_REV_0, EVDO_REV_A, EVDO_REV_B,
             HSDPA, HSUPA, HSPA, HSPA_PLUS, HSPA_PLUS_64QAM,
              HSPA_PLUS_MIMO])
NET_4G = set([LTE])

def network_type(n):

    if n in NO_SERVICE:
        return "No Service"
    elif n in NET_2G:
        return "2G"
    if n in NET_3G:
        return "3G"
    if n in NET_4G:
        return "4G"
    else:
        return "??"

class Py3status:
    url = "http://192.168.8.1"
    signal_chars = "⁰¹²³⁴⁵"
    format_up = "H:{signal_icon} {current_network_type}"
    format_down = "Modem Not found"
    bad_threshold = 2
    degraded_threshold = 3
    cookies = {}

    def _parse_status(self, text):
        status = {convert(child.tag): child.text for child in ET.fromstring(text)}

        status['current_network_type'] = network_type(status['current_network_type'])
        signal_strength = int(status['signal_icon'])
        status['signal_icon'] = self.signal_chars[signal_strength]
        if signal_strength < self.bad_threshold:
            color = self.py3.COLOR_BAD
        elif signal_strength < self.degraded_threshold:
            color = self.py3.COLOR_DEGRADED
        else:
            color = self.py3.COLOR_GOOD

        status['color'] = color
        return status

    def _get(self, url):
        try:
            s = requests.Session()
            a = requests.adapters.HTTPAdapter(max_retries=0)
            b = requests.adapters.HTTPAdapter(max_retries=0)
            s.mount('http://', a)
            s.mount('https://', b)
            r = s.get(url, cookies=self.cookies, timeout=(0.5, 10))
            if r.status_code == 200:
                return r
            else:
                return None
        except Exception as err:
            return None

    def _get_status(self):
        r = self._get(self.url + "/api/monitoring/status")
        if r:
            code = getattr(ET.fromstring(r.text).find('code'), 'text', None)
            if code:
                assert(code == "125002")  # don't know about other codes
                self.cookies = self._get(self.url).cookies
                r = self._get(self.url + "/api/monitoring/status")

        if r:
            return self._parse_status(r.text)

    def status(self):
        status = self._get_status()

        if status:
            fmt = self.format_up
        else:
            fmt = self.format_down
            status = {"color": self.py3.COLOR_BAD}

        return {
            "full_text": fmt.format(**status),
            "color": status['color'],
            "cached_until": self.py3.time_in(60)
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)

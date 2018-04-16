#!/home/neale/.virtualenvs/py3status/bin/python
# -*- coding: utf-8 -*-
"""
EE Quota.

Displays the quota left on an EE account

Configuration parameters:
    format: Format of the output.
    format_down: Format of the output when not on EE network.
    low_threshold: quota below which the output is low
        (default 1)
    warn_threshold: quota below which the output is colored 'bad'
        (default 3)

Format placeholders:
    {quota_left}
    {quota_total}
    {quota_days}
    {quota_hours} the hours in last day.

Examples:
```
ee_quota {

   format = "EE:{quota_left}/{quota_total}[{quota_days}d]"
}
```

Requires:
    beautifulsoup4
    requests


@author <Neale Swinnerton>
@license BSD
"""

from bs4 import BeautifulSoup
import requests

import re

url = "http://add-on.ee.co.uk/status"
headers = {
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"
}


class Py3status:
    format = "EE:{quota_left}/{quota_total}[{quota_days}d]"
    format_down = "ɆɆ"
    bad_threshold = 1.0
    degraded_threshold = 3.0

    def _allowance(self, soup):
        data = {"quota_left": None}
        allowance = soup.find_all(class_="allowance__left")
        if allowance:
            str = allowance[0].get_text()
            m = re.match(r"(?s).*?(([0-9\.]+)\w+)\s+left\s+of\s+(([0-9\.]+)\w+)",
                         str)
            if m:
                quota_left = float(m.group(2))

                if quota_left < self.bad_threshold:
                    color = self.py3.COLOR_BAD
                elif quota_left < self.degraded_threshold:
                    color = self.py3.COLOR_DEGRADED
                else:
                    color = self.py3.COLOR_GOOD

                data = {"quota_left": m.group(1),
                        "quota_total": m.group(3),
                        "quota_color": color}

        return data

    def _timespan(self, soup):
        timespan = soup.find_all(class_="allowance__timespan")
        if timespan:
            str = timespan[0].get_text()
            m = re.match(r"(?s)\s*Lasts for\s+(\d+).*?(\d+)\s+", str)
            if m:
                return {"quota_days": m.group(1),
                        "quota_hours": m.group(2)}

        return {}

    def _get(self, url):
        s = requests.Session()
        a = requests.adapters.HTTPAdapter(max_retries=0)
        b = requests.adapters.HTTPAdapter(max_retries=0)
        s.mount('http://', a)
        s.mount('https://', b)
        return s.get(url, headers=headers, timeout=(0.5, 10))

    def quota(self):
        data = {}
        try:
            text = self._get(url).text
            soup = BeautifulSoup(text, 'html.parser')
            data = self._allowance(soup)

            data.update(self._timespan(soup))

            if all(data.values()):
                return {
                    "full_text": self.format.format(**data),
                    "color": data["quota_color"],
                    "cached_until": self.py3.time_in(3600)
                }

        except Exception as err:
            print(err)

        return {
            "full_text": self.format_down.format(**data),
            "color": self.py3.COLOR_BAD,
            "cached_until": self.py3.time_in(3600)
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)

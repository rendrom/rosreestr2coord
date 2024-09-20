import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from urllib.parse import urlparse
from urllib.request import urlopen

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) \
        Chrome/64.0.3282.186 Safari/537.36"


class ProxyHandling:
    def __init__(self, path="proxy.txt", user_agent=USER_AGENT):
        self.path = path
        self.user_agent = user_agent

    def update_proxies(self):
        # Getting proxy list from address if file is old
        proxies = self._load_proxies_from_file()
        if not proxies:
            self._download_proxies()
        try:
            older = 3600 * 6  # 6h
            diff = time.time() - os.path.getmtime(self.path)
            if diff > older:
                self._download_proxies()
        except OSError:
            self._download_proxies()

    def dump_proxies(self, proxies):
        with open(self.path, "w") as outfile:
            for proxy in proxies:
                outfile.write(proxy)

    def load_proxies(self):
        if not os.path.exists(self.path):
            with open(self.path, "w"):
                pass
        self.update_proxies()
        return self._load_proxies_from_file()

    def get_proxies(self):
        return self._load_proxies_from_file()

    def _download_proxies(self):
        found = self._free_proxies()
        self.dump_proxies(found[:20])  # 20 top proxies

    def _free_proxies(self, url="https://free-proxy-list.net/"):
        # Downloading without proxy
        opener = urllib.request.build_opener(urllib.request.ProxyHandler())
        urllib.request.install_opener(opener)
        request = urllib.request.Request(url)
        request.add_header("user-agent", self.user_agent)
        parsed_uri = urlparse(url)
        host = "{uri.scheme}://{uri.netloc}/".format(uri=parsed_uri)
        request.add_header("referer", host)
        f = urllib.request.urlopen(request)
        pattern = r"\d*\.\d*\.\d*\.\d*\</td><td>\d*"
        s = f.read().decode("utf-8")
        found = [i.replace("</td><td>", ":") + "\n" for i in re.findall(pattern, s)]
        return found

    def _load_proxies_from_file(self):
        try:
            with open(self.path) as outfile:
                return outfile.readlines()
        except Exception:
            return []

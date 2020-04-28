import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from urllib.parse import urlparse
from urllib.request import urlopen

PROXY_PATH = 'proxy.txt'
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) \
    Chrome/64.0.3282.186 Safari/537.36'


def update_proxies(path=PROXY_PATH):
    # Getting proxy list from address if file is old
    proxies = load_proxies_from_file(path)
    if not proxies:
        download_proxies(path)
    older = 3600 * 6  # 6h
    try:
        os.path.getmtime(path)
    except OSError:
        download_proxies(path)
    diff = time.time() - os.path.getmtime(path)
    if diff > older:
        download_proxies(path)


def download_proxies(path=PROXY_PATH):
    found = ip_adress_proxies()
    # found = free_proxies()
    dump_proxies_to_file(found[:20], path)  # 20 top proxies


def ip_adress_proxies(url='https://www.ip-adress.com/proxy_list/'):
    # Downloading without proxy
    opener = urllib.request.build_opener(urllib.request.ProxyHandler())
    urllib.request.install_opener(opener)
    request = urllib.request.Request(url)
    request.add_header('user-agent', USER_AGENT)
    parsed_uri = urlparse(url)
    host = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    request.add_header('referer', host)
    s = False
    try:
        context = ssl._create_unverified_context()
        with urlopen(request, context=context, timeout=3000) as response:
            s = response.read().decode('utf-8')
    except Exception as er:
        print(er)
    pattern = r'\d*\.\d*\.\d*\.\d*\</a>:\d*'
    found = [i.replace('</a>', '') + '\n' for i in re.findall(pattern, s)]
    return found


def free_proxies(url='https://free-proxy-list.net/'):
    # Downloading without proxy
    opener = urllib.request.build_opener(urllib.request.ProxyHandler())
    urllib.request.install_opener(opener)
    request = urllib.request.Request(url)
    request.add_header('user-agent', USER_AGENT)
    parsed_uri = urlparse(url)
    host = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    request.add_header('referer', host)
    f = urllib.request.urlopen(request)
    pattern = r'\d*\.\d*\.\d*\.\d*\</td><td>\d*'
    s = f.read().decode('utf-8')
    found = [i.replace('</td><td>', ':') +
             '\n' for i in re.findall(pattern, s)]
    return found


def load_proxies(path=PROXY_PATH):
    if not os.path.exists(PROXY_PATH):
        with open(PROXY_PATH, 'w'):
            pass
    update_proxies(path)
    return load_proxies_from_file(path)


def load_proxies_from_file(path=PROXY_PATH):
    try:
        with open(path) as outfile:
            return outfile.readlines()
    except Exception:
        return None


def dump_proxies_to_file(proxies, path=PROXY_PATH):
    with open(path, 'w') as outfile:
        for proxy in proxies:
            outfile.write(proxy)

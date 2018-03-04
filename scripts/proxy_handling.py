import urllib2
import re
from random import choice
import os
import time


def update_proxies(path='proxy.txt'):
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


def download_proxies(path='proxy.txt'):
    # Downloading without proxy
    opener = urllib2.build_opener(urllib2.ProxyHandler())
    urllib2.install_opener(opener)
    request = urllib2.Request('http://www.ip-adress.com/proxy_list/')
    request.add_header('user-agent',
                       'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36')
    request.add_header('referer', 'htpps://www.google.com/')
    f = urllib2.urlopen(request)
    pattern = r'\d*\.\d*\.\d*\.\d*\</a>:\d*'
    found = [i.replace('</a>', '') + '\n' for i in re.findall(pattern, f.read())]
    dump_proxies_to_file(found[:20], path)  # 20 top proxies


def get_random_proxy(path='proxy.txt'):
    with open(path) as outfile:
        proxies = outfile.readlines()
    return choice(proxies)


def load_proxies_from_file(path='proxy.txt'):
    try:
        with open(path) as outfile:
            return outfile.readlines()
    except Exception:
        return None


def dump_proxies_to_file(proxies, path='proxy.txt'):
    with open(path, 'w') as outfile:
        for proxy in proxies:
            outfile.write(proxy)


if __name__ == '__main__':
    # rand_proxy = '37.187.116.100:801'
    # proxy = urllib2.ProxyHandler({'http': rand_proxy, 'https': rand_proxy})
    # opener = urllib2.build_opener(proxy)
    # urllib2.install_opener(opener)
    # headers = {
    #     'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
    #     'referer': 'htpps://www.google.com/'}
    # request = urllib2.Request('https://2ip.ru/', headers=headers)
    # urlopen = urllib2.urlopen(request)
    # with open('temp.htm', 'w') as file:
    #     file.write(urlopen.read())
    # print(load_proxies_from_file())
    # download_proxies()
    update_proxies()
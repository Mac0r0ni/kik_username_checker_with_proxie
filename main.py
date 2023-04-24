import logging
import queue
import random
import threading


import requests
from lxml.html import fromstring

# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('log.txt')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:299]:  # 299 proxies will be scraped
        proxy = ":".join([i.xpath('.//td[1]/text()')
                          [0], i.xpath('.//td[2]/text()')[0]])
        proxies.add(proxy)
    return proxies


try:
    proxies = get_proxies()
    f = open('proxies.txt', 'w')
    for proxy in proxies:
        f.write(proxy + '\n')
    f.close()
    print("DONE SCRAPING PROXIES")
except:
    print("FAILED SCRAPING PROXIES")


def get_proxies(file_path):
    with open(file_path, 'r') as file:
        proxies = file.read().splitlines()
    return proxies


def get_proxies(filename):
    with open(filename, 'r') as file:
        proxies = [line.strip() for line in file]
    return proxies


def make_request(url, proxies):
    proxy = random.choice(proxies)
    proxies.remove(proxy)
    try:
        response = requests.get(url, proxies={'http': proxy, 'https': proxy}, timeout=5)
        if response.status_code == 404:
            logger.info(f'Username not available for {url} using {proxy}')
            with open('not_available.txt', 'a') as file:
                file.write(url.split('/')[-1] + '\n')
        else:
            logger.info(f'Username available for {url} using {proxy}')
            with open('available.txt', 'a') as file:
                file.write(url.split('/')[-1] + '\n')
            response.raise_for_status()
            return response.json()
    except:
        proxies.append(proxy)
        return make_request(url, proxies)


def process_usernames(q, proxies):
    while True:
        username = q.get()
        self.client.check_username_uniqueness(username)
        url = f'https://ws2.kik.com/user/{username}'
        data = make_request(url, proxies)
        if data is not None:
            print(data)
        q.task_done()


if __name__ == '__main__':
    proxies = get_proxies('proxies.txt')
    random.shuffle(proxies)

    q = queue.Queue()
    threads = []
    num_threads = 10

    for i in range(num_threads):
        t = threading.Thread(target=process_usernames, args=(q, proxies))
        t.daemon = True
        t.start()
        threads.append(t)

    with open('usernames.txt', 'r') as file:
        for line in file:
            username = line.strip()
            q.put(username)

    q.join()

    for t in threads:
        t.join()

    print('Done')


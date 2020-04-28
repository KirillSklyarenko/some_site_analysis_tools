# check website sitemap for 200, 404, 410, 500-599 responses; output to txt file

import random
import logging
from threading import Thread
import sys
from typing import List
import queue

import requests
from bs4 import BeautifulSoup

log_format = '%(filename)s - %(levelname)s - %(message)s'
logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')
stream = logging.StreamHandler()
formatter = logging.Formatter(log_format)
stream.setFormatter(formatter)
logger.addHandler(stream)


desktop_agents = ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                  'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
                  'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
                  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                  'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                  'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0']
# https://kirill-sklyarenko.ru/index.php?option=com_jmap&view=sitemap&format=xml
# https://perevodzakonov.ru/index.php?option=com_jmap&view=sitemap&format=xml


def sitemapurl() -> str:
    """asks for sitemap link and prevents apparently incorrect strings"""
    sitemap = False
    while not sitemap:
        entered_input = input("paste an xml sitemap link or 'e' to exit:")
        if entered_input.lower() == 'e':
            sys.exit()
        else:
            status = 0
            if entered_input.startswith("http") and entered_input.endswith("=xml"):
                f = requests.get(entered_input, headers={'User-Agent': random.choice(desktop_agents)}, timeout=(2, 5))
                status = f.status_code
                if status == 200:
                    sitemap = f
                else:
                    logger.info("link not reachable")
            else:
                logger.info("not a valid xml link")
    return sitemap.text


def sitemaplist(content: str) -> List:
    """goes to sitemap page and creates a list of its links"""
    links = []
    soup = BeautifulSoup(content, 'xml')
    for i in soup.find_all('url'):
        link = i.findNext("loc").text
        links.append(link)
    if links:
        logger.info(f"The number of url tags in sitemap: {len(links)}")
        return links
    else:
        logger.info("list of sitemap urls is empty. The xml link must be wrong.")


def checker(url: str, response_list=[]) -> List:
    """
    follows a provided link
    and appends to list of (url, response) tuples
    """
    f = requests.get(url, headers={'User-Agent': random.choice(desktop_agents)}, timeout=(2, 5))
    status = f.status_code
    response_list.append((url, status))
    return response_list


def wrapper_checker(checker, q):
    while not q.empty():
        work = q.get()
        checker(work)
        q.task_done()


def threads(urls: list) -> None:
    q = queue.Queue()
    threads = []
    for i in urls:
        q.put(i)
    num_threads = min(40, len(urls))
    logger.info(f"number of link packages: {num_threads}")
    for i in enumerate(range(num_threads), 1):
        logger.info(f"starting package {i[0]}")
        t = Thread(target=wrapper_checker, args=(checker, q))
        t.start()
        threads.append(t)
    q.join()


def results(fourlists: tuple) -> None:
    """
    accepts lists with response urls, shows count
    writes to txt file in the same folder
    """
    if fourlists[0]:
        logger.info(f"found {str(len(fourlists[0]))} good ")
        logger.info("list of links sent to good links.txt")
        with open("good links.txt", "w") as f:
            f.write("\r".join(fourlists[0]))
    else:
        logger.info("no 200 pages found")

    if fourlists[1]:
        logger.info(f"found {str(len(fourlists[1]))} 404 ")
        logger.info("list of links sent to 404 links.txt")
        with open("404 links.txt", "w") as f:
            f.write("\r".join(fourlists[1]))
    else:
        logger.info("no 404 pages found")

    if fourlists[2]:
        logger.info(f"found {str(len(fourlists[2]))} 410 ")
        logger.info("list of links sent to 410 links.txt")
        with open("410 links.txt", "w") as f:
            f.write("\r".join(fourlists[2]))
    else:
        logger.info("no 410 pages found")

    if fourlists[3]:
        logger.info(f"found {str(len(fourlists[3]))} server error(s) ")
        logger.info("list of links sent to server error links.txt")
        with open("server error links.txt", "w") as f:
            f.write("\r".join(fourlists[3]))
    else:
        logger.info("no server errors found")


def main():
    sitemap = sitemaplist(sitemapurl())
    threads(sitemap)
    results((list200, list404, list410, server_errors))


if __name__ == '__main__':
    main()

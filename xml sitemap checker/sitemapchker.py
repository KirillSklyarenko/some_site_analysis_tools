# check website sitemap for responses; output to stdout or,
# if selected, txt file according to status

import itertools as IT
import logging
import queue
import random
import threading as t
from typing import List, Dict, Optional, Tuple
import sys


import requests
from bs4 import BeautifulSoup

log_format = '%(levelname)s: %(message)s'
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


def sitemapurl() -> str:
    """asks for sitemap link and prevents apparently incorrect strings"""
    sitemap = False
    while not sitemap:
        entered_input = input("paste an xml sitemap link or 'e' to exit:")
        if entered_input.lower() == 'e':
            sys.exit()
        else:
            status = 0
            if entered_input.startswith("http") and entered_input.endswith("xml"):
                f = requests.get(entered_input, headers={'User-Agent': random.choice(desktop_agents)}, timeout=None)
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


response_list = []
requests_exceptions = []
q = queue.Queue()


def q_putter(q, links: List) -> None:
    """all urls found on xml sitemap are added to the q"""
    for i in links:
        q.put(i)
    q.put("END")


def checker(url: str) -> Tuple:
    """
    follows the provided link
    and makes (url, response status) tuples
    """
    try:
        f = requests.get(url, headers={'User-Agent': random.choice(desktop_agents)}, timeout=None)
        status = f.status_code
        return (url, status)
    except requests.exceptions.RequestException:
        exc_type, value, traceback = sys.exc_info()
        return (url, exc_type.__name__)


def responselist_maker(response_tuple: Tuple) -> None:
    response_list.append(response_tuple)


def checker_wrapper(url, q) -> None:
    "accepts threads and processes them with 2 funcs"
    response_tuple = checker(url)
    responselist_maker(response_tuple)
    q.task_done()


iterator = iter(q.get, 'END')


def threads(q, links: List, checker_wrapper) -> None:
    threads_list = []
    for i in iter(lambda: list(IT.islice(iterator, 30)), []):
        for j in i:
            threader = t.Thread(target=checker_wrapper, args=(j, q))
            threads_list.append(threader)
            threader.start()
    for i, k in enumerate(threads_list, start=1):
        k.join()
        print("Progress: ", i, " link of", len(threads_list), end="\r")
    logger.info("Checked all.")


q.join()


def ask_for_output() -> Optional[bool]:
    "ask whether output to file is needed"
    entered_input = input("""Can make a txt file in the same folder with urls sorted according to status.
                            Press 'y' to make it or 'n' to exit: """)
    if entered_input.lower() == 'n':
        sys.exit()
    elif entered_input.lower() == 'y':
        return True
    else:
        logger.info("please, select between offered alternatives")
        ask_for_output()


def created_output(response_list: List) -> Dict:
    """from list of (url, status) tuples
        make a dict with statues as key and
        list of urls as value"""
    final_output = {}
    for i in response_list:
        if i[1] not in final_output.keys():
            final_output[i[1]] = [(i[0])]
        else:
            final_output[i[1]] += [i[0]]
    return final_output


def show_result(final_output: Dict) -> None:
    "show statuses and number of associated sitemap urls"
    logger.info("I got the following results:")
    for key, value in final_output.items():
        logger.info(f"{key}: {len(value)}")


def output_to_file(final_output: Dict) -> None:
    """create a file in the same dir and
        write statuses and number of associated sitemap urls"""
    with open("sitemap_output.txt", 'w') as f:
        for k, v in final_output.items():
            f.write('%s\n%s\n\n' % (k, "\n".join(v)))
    logger.info("I'm out.")


def main():
    sitemaplink = sitemapurl()
    urllist = sitemaplist(sitemaplink)
    q_putter(q, urllist)
    threads(q, urllist, checker_wrapper)
    output_dict = created_output(response_list)
    show_result(output_dict)
    if ask_for_output() is True:
        output_to_file(output_dict)


if __name__ == '__main__':
    main()

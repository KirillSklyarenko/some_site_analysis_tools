#! python 3.7
# check website sitemap for 200, 404, 410, 500-599 responses; output to txt file

import requests
from bs4 import BeautifulSoup
import random
# import logging
from threading import Thread
import sys

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

def inputurl() -> str:
    """asks for sitemap link and asserts to variable"""
    try:
        sitemap = input("paste xml sitemap link:")
        assert sitemap.startswith("http") and sitemap.endswith("=xml")
    except AssertionError:
        print("not a valid xml link")
        inputurl()
    return sitemap


def sitemaplist(url: str) -> list:
    """goes to sitemap page and creates list of its links"""
    links = []
    pagetext = requests.get(url, headers={'User-Agent': random.choice(desktop_agents)})
    while pagetext.status_code != 200:
        print(f"sitemap xml url was not reached. Status code {pagetext.status_code}")
        tryagainquestion = input("try another xml link? y or n:")
        if tryagainquestion.lower() == "y":
            inputurl()
        elif tryagainquestion.lower() == "n":
            print("let's close")
            sys.exit()
        else:
            print("please insert y or n")
    data = pagetext.text
    soup = BeautifulSoup(data, 'xml')
    for i in soup.find_all('url'):
        link = i.findNext("loc").text
        links.append(link)
    print("The number of url tags in sitemap: ", len(links))
    if links:
        return links
    else:
        print("list of sitemap urls is empty. The xml link must be wrong.")


def checker(url: str) -> tuple:
    """
    follows each link in sitemap list
    and appends to relevant list subject to response
    """
    f = requests.get(url, headers={'User-Agent': random.choice(desktop_agents)})
    status = f.status_code
    if status == 200:
        list200.append(url)
    elif status == 404:
        list404.append(url)
    elif status == 410:
        list410.append(url)
    elif 500 <= status <= 599:
        server_errors.append(url)
    return (list200, list404, list410, server_errors)


def threads(urls):
    threads = []
    for i in urls:
        process = Thread(target=checker, args=[i])
        process.start()
        threads.append(process)
    for process in threads:
        process.join()


def results(fourlists: tuple) -> None:
    
    if fourlists[0]:
        print(f"found {str(len(fourlists[0]))} good ")
        print("list of links sent to good links.txt")
        with open("good links.txt", "w") as f:
            f.write("\r".join(fourlists[0]))
    else:
        print("no 200 pages found")

    if fourlists[1]:
        print(f"found {str(len(fourlists[1]))} 404 ")
        print("list of links sent to 404 links.txt")
        with open("404 links.txt", "w") as f:
            f.write("\r".join(fourlists[1]))
    else:
        print("no 404 pages found")

    if fourlists[2]:
        print(f"found {str(len(fourlists[2]))} 410 ")
        print("list of links sent to 410 links.txt")
        with open("410 links.txt", "w") as f:
            f.write("\r".join(fourlists[2]))
    else:
        print("no 410 pages found")

    if fourlists[3]:
        print(f"found {str(len(fourlists[3]))} server error(s) ")
        print("list of links sent to server error links.txt")
        with open("server error links.txt", "w") as f:
            f.write("\r".join(fourlists[3]))
    else:
        print("no server errors found")


if __name__ == '__main__':
    list200 = []
    list404 = []
    list410 = []
    server_errors = []
    sitemap = sitemaplist(inputurl())
    threads(sitemap)
    results((list200, list404, list410, server_errors))

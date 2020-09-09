# program accepts the website link and checks responses of all links on the page
# concurrently, it tries to recognize other website pages and check them too
# the main purpose is to detect links with non-200 responses, since they worsen the seo
# generally, this program is my take on composition in Python

# four classes:
# 1. BaseClass holds global variables 
# like the updatable queue object, dict with final resulsts and set of visited urls
# 2. PageChecker checks each url with bs4, creates the set of new internal urls and sends it
# to the BaseClass.build_q and the BaseClass global set of internal urls
# 3. ProvideOutput shows the summary result on the command line and writes total results to the txt file
# 4. Runner manipulates all the above and the queue object and uses threading

import collections
import itertools as IT
import logging
import queue
import random
import re
import pathlib
import sys
import threading

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup


log_format = '%(levelname)s: %(message)s'
logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')
stream = logging.StreamHandler()
formatter = logging.Formatter(log_format)
stream.setFormatter(formatter)
logger.addHandler(stream)


# a separate logger with non-default terminator
# to make one-line counts of tasks in BaseClass.build_q
logger1 = logging.getLogger("counter")
logger1.setLevel('DEBUG')
stream1 = logging.StreamHandler()
stream1.terminator = '\r'
stream1.setFormatter(formatter)
logger1.addHandler(stream1)

# requests session with 3 retries
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)


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


class BaseClass:
    """ asks the user for a website domain input
        prepares the queue object for threaded link checking
        holds common variables for the given website, see variables in __init__
        """

    def __init__(self):
        self.siteurl = ''
        self.found_siteurls_to_check = set()
        self.checkedpages = {}
        self.q = queue.Queue()
        self.lock = threading.Lock()

    def define_starturl(self):
        """asks for website link and prevents apparently incorrect strings using regex"""
        while not self.siteurl:
            entered_input = input("type a website or 'e' to exit:")
            if entered_input.lower() == 'e':
                sys.exit()
            else:
                url_regex = re.compile(r"((http|https)\:\/\/)[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*")
                onlydomain = re.compile(r"[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*")
                if url_regex.match(entered_input):
                    self.siteurl = entered_input
                elif onlydomain.match(entered_input):
                    self.siteurl = "http://" + entered_input
                else:
                    logger.info("not a valid startpage link")
        if self.siteurl.endswith("/"):
            self.siteurl = self.siteurl[:-1]
        return self.siteurl

    def check_website_connection(self):
        try:
            f = session.get(self.siteurl, headers={'User-Agent': random.choice(desktop_agents)})
            logger.info(f"your website returns {f.status_code}")
        except requests.exceptions.RequestException:
            exc_type, value, traceback = sys.exc_info()
            logger.warning(f"your website returns the error {exc_type.__name__} after 3 retries")
            self.siteurl = ''
            self.define_starturl()

    def build_q(self, received_set=None):
        """ from PageChecker.add_other_siteurls_toset_forchecking()
            accepts the set of internal website links and adds them to the queue object
            the received_set is None just once, for the first startpage check
            all subsequent usages of this func are with the set
            the first item of the queue object is None
            """
        if received_set:
            set_of_new_pages = received_set - self.found_siteurls_to_check
            if set_of_new_pages:
                for i in set_of_new_pages:
                    if "#" not in i:
                        self.q.put(i)
                self.found_siteurls_to_check |= received_set
        else:
            for i in self.found_siteurls_to_check:
                self.q.put(i)
        logger1.info(f"website pages to check: {self.q.qsize()}, remaining: {self.q.unfinished_tasks}-----")


class PageChecker:
    """ accepts the link from the queue object and checks links on it
        by creating the list of checked urls with its items in the form ("url", "response")
        creates the set of the internal website links found on the given page and
        creates the set to be sent to the Baseclass.build_q()
        yes, using a class means a lot of page checking objects, I see it as a learning subject
        """

    def __init__(self, url, baseclass):
        self.url = url
        self.ulrs_onpage = set()
        self.checkedurls = []
        self.baseclass = baseclass

    def findallurls(self):
        """creates the set of urls found on the page"""
        pagetext = session.get(self.url)
        data = pagetext.text
        soup = BeautifulSoup(data, 'html.parser')
        tags_with_href = {i.get('href') for i in soup.find_all('a') if (i.get('href') and i.get('href').startswith(('http', '/')))}
        for i in tags_with_href:
            if i.startswith(('/')):
                fullurl = self.baseclass.siteurl + i
                self.ulrs_onpage.add(fullurl)
            else:
                self.ulrs_onpage.add(i)

    def checkurls(self):
        """all found urls are added to the checkedurls list in the form ("url", "response")"""
        for i in self.ulrs_onpage:
            try:
                f = session.get(i, headers={'User-Agent': random.choice(desktop_agents)})
                status = f.status_code
                returned_status = (status, i)
                self.checkedurls.append(returned_status)
            except requests.exceptions.RequestException:
                exc_type, value, traceback = sys.exc_info()
                returned_error = (exc_type.__name__, i)
                self.checkedurls.append(returned_error)

    def add_to_total_dict(self):
        """the results of checking on the page are added to the global dict of checked pages
            in the form {"url_under_check": "list_of_checked_urls_on_it"}
            """
        self.baseclass.checkedpages[self.url] = self.checkedurls

    def add_other_siteurls_toset_forchecking(self):
        """the set to be sent to the Baseclass.build_q()"""
        set_for_adding_to_q = set(i[1] for i in self.checkedurls if self.baseclass.siteurl in i[1])
        with self.baseclass.lock:
            if self.url == self.baseclass.siteurl:
                self.baseclass.found_siteurls_to_check = set_for_adding_to_q
                self.baseclass.build_q()
            else:
                self.baseclass.build_q(set_for_adding_to_q)

    def run(self):
        """the method to run the PageChecker"""
        self.findallurls()
        self.checkurls()
        self.add_to_total_dict()
        self.add_other_siteurls_toset_forchecking()


class ProvideOutput:
    """ accepts the checkedpages dict with all of the checking results from baseclass
        shows summary results and asks whether all of the results should be written to a txt file
        to be created in the folder, where the module is located
        """

    def __init__(self, baseclass):
        self.baseclass = baseclass

    def show_result(self):
        count_checked_pages = sum(len(v) for v in self.baseclass.checkedpages.values())
        all_values_to_count_responses = [w for v in self.baseclass.checkedpages.values() for w in v]
        counted_responses = collections.Counter(i[0] for i in all_values_to_count_responses)
        logger.info("\n")  # just to separate summary from the line with counters
        logger.info(f"""I got the following results:
                    number of visited pages: {len(self.baseclass.checkedpages.keys())}
                    total number of checked urls on all pages: {count_checked_pages}
                    counter of responses: {counted_responses}
                    """)

    def maybe_write_tofile(self):
        entered_input = input("""Can write total results to a txt file in the same folder.
                                Press 'y' to proceed or 'n' to exit: """)
        if entered_input.lower() == 'n':
            sys.exit()
        elif entered_input.lower() == 'y':
            self.write_tofile()
        else:
            logger.info("please select from the offered alternatives")
            self.maybe_write_tofile()

    def write_tofile(self):
        with open(pathlib.Path(__file__).parent.absolute() / "checked links.txt", 'w') as f:
            for k, v in self.baseclass.checkedpages.items():
                f.write('%s\n%s\n\n' % (f"checked url: {k}", "".join(str(i)+'\n' for i in v)))
        logger.info("I'm done.")

    def run(self):
        self.show_result()
        self.maybe_write_tofile()


class Run:
    """ navigates the program through runner and presenter methods
        engages the threads to consume the queue object
        """

    def __init__(self):
        self.baseclass = BaseClass()

    def runner(self):
        starting_url = self.baseclass.define_starturl()
        self.baseclass.check_website_connection()
        first_checker = PageChecker(starting_url, self.baseclass)
        first_checker.run()
        self.consume_queue()
        self.baseclass.q.join()

    def presenter(self):
        output_provider = ProvideOutput(self.baseclass)
        output_provider.run()

    def consume_queue(self):
        """the queue object is consumed in chunks of 20 items"""
        threads_list = []
        for i in range(20):
            threader = threading.Thread(target=self.checker_wrapper, args=(self.baseclass.q,))
            threads_list.append(threader)
            threader.start()
        for i in threads_list:
            i.join()

    def checker_wrapper(self, q):
        """worker func for threading that accepts one url-item from the queue
        and gives it to the PageChecker class.
        yes, it means a lot of PageChecker objects
        no, i did not want to make this func separately
        """
        while not q.unfinished_tasks == 0:
            try:
                url = q.get(timeout=5)
            except queue.Empty:
                continue
            start_checker = PageChecker(url, self.baseclass)
            start_checker.run()
            q.task_done()


if __name__ == '__main__':
    start_running = Run()
    start_running.runner()
    start_running.presenter()

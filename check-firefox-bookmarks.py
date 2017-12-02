"Check the health of Firefox bookmarks."

import sqlite3
import multiprocessing as mp
import urllib.request as rq
from urllib.error import URLError
import socket
import itertools as itert

query = "select url from moz_places inner join moz_bookmarks on moz_places.id = moz_bookmarks.fk"
useragent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'

connection = sqlite3.connect('places.sqlite')
cursor = connection.cursor()
results = map(lambda x: x[0],
              filter(lambda x: x[0].startswith("http"), cursor.execute(query)))

report_success = False
report_redirects = False
timeout = 10

success = mp.Queue()
failure = mp.Queue()

def check1(url, timeout=10):
    req = rq.Request(url, headers={'User-Agent': useragent})
    request = None
    try: request = rq.urlopen(req, timeout=timeout)
    except socket.timeout as e:
        raise e
    finally:
        if request: request.close()
    rurl = request.url
    if rurl == url: return (url, request.status)
    else: return ([url, rurl], request.status)

def check(url):
    try:
        url, status = check1(url)
        if report_redirects or report_success:
            if type(url2) == list:
                url = " => ".join(url)
            print("Success '{}': {}".format(url, status))
        success.put((url, status))
    except Exception as error:
        errstr = str(error)
        print("Error '{}': {}".format(url, errstr))
        failure.put((url, errstr))

def run(nprocs=10, nresults=None):
    with mp.Pool(processes=nprocs) as pool:
        act = pool.map
        if nresults: act(check, itert.islice(results, nresults))
        else: act(check, results)

    nsuccess = success.qsize()
    nfailure = failure.qsize()
    total = nsuccess + nfailure

    print("Checked {} urls: {} healty, {} dead (%{} linkrot)".format(
        total, nsuccess, nfailure, nfailure / total * 100))

if __name__ == "__main__":
    run()

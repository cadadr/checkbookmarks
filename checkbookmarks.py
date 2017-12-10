# Copyright (C) 2017 İ. Göktuğ Kayaalp <self at gkayaalp dot com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"Check the health of Firefox bookmarks."

import argparse
import itertools as itert
import multiprocessing as mp
import socket
import sqlite3
import sys
import urllib.request as rq
from urllib.error import URLError

query = "select url from moz_places inner join moz_bookmarks on moz_places.id = moz_bookmarks.fk"
useragent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'

report_success = False
report_redirects = False
timeout = 10
database = "places.sqlite"

connection = sqlite3.connect(database)
cursor = connection.cursor()
results = map(lambda x: x[0],
              filter(lambda x: x[0].startswith("http"), cursor.execute(query)))

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

def cli(args):
    p = argparse.ArgumentParser(
        description="Check the health of Firefox bookmarks.")
    p.add_argument("db", metavar="DB", type=str,
        help="the path to places.sqlite file (preferably a copy,"
             " not the actual one Firefox uses)")
    p.add_argument("-a", type=str, metavar="USER-AGENT",
        help="the user agent string to usewhen making requests,"
             " by default set to resemble a web browser")
    p.add_argument("-v", action="count", help="be verbose")
    p.add_argument("-t", metavar="SECONDS", type=int,
        help="connection timeout")

    args = p.parse_args(args)

    global report_success, report_redirects, timeout, database
    if args.v:
        if args.v >= 1: report_success = True
        if args.v >= 2: report_redirects = True
    if args.t: timeout = args.t
    database = args.db

if __name__ == "__main__":
    cli(sys.argv[1:])
    run()

"""
Utils for dealing with bioarxiv API and related processing
"""

import time
import logging
import urllib.request
from collections import OrderedDict
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def get_response(search_query, start_index=0):
    """ pings bioarxiv.org API to fetch a batch of 100 papers """
    # fetch raw response
    date_start = search_query['date_start']
    date_end   = search_query['date_end']
    server = search_query['server']

    base_url = 'https://api.biorxiv.org/details/'
    add_url  = f'{server}/{date_start}/{date_end}/{start_index}'
    search_query = base_url + add_url
    
    logger.debug(f"Searching arxiv for {search_query}")
    with urllib.request.urlopen(search_query) as url:
        response = url.read()

    if url.status != 200:
        logger.error(f"bioarxiv did not return status 200 response")

    return response

def parse_response(response):

    parse = json.loads(response.decode("utf-8"))
    papers = parse['collection']
    total_papers = parse['messages'][0]['total']

    parsed_papers = []
    for paper in papers:
        
        server = paper['server']
        version = int(paper['version'])
        dt = datetime.strptime(paper['date'], '%Y-%m-%d')
        
        db_entry = {}
        db_entry['id'] = paper['doi']
        db_entry['link'] = f"https://www.{server}.org/content/{paper['doi']}"
        db_entry['title'] = paper['title']
        db_entry['summary'] = paper['abstract']
        db_entry['authors'] = [{'name': name.strip()} for name in paper['authors'].split(';')]
        db_entry['arxiv_primary_category'] = paper['category']
        db_entry['tags'] = [{'term': server}, {'term': paper['category']}]
        db_entry['_time'] = time.mktime(dt.timetuple())
        db_entry['_time_str'] = datetime.strftime(dt, '%b %d %Y')
        db_entry['_id'] = paper['doi']
        db_entry['_idv'] = f"{paper['doi']}v{version}"
        db_entry['_version'] = version
        
        parsed_papers.append(db_entry)
    
    return parsed_papers, total_papers

def filter_latest_version(idvs):
    """
    for each idv filter the list down to only the most recent version
    """

    pid_to_v = OrderedDict()
    for idv in idvs:
        pid, v = idv.split('v')
        pid_to_v[pid] = max(int(v), pid_to_v.get(pid, 0))

    filt = [f"{pid}v{v}" for pid, v in pid_to_v.items()]
    return filt
"""
This script is intended to wake up every 30 min or so (eg via cron),
it checks for any new arxiv papers via the arxiv API and stashes
them into a sqlite database.
"""

import sys
import time
import random
import logging
import argparse
from datetime import date, timedelta

from aslite.bioarxiv import get_response, parse_response
from aslite.db import get_papers_db, get_metas_db


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO, format='%(name)s %(levelname)s %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # by default every time script is run, the database is updated with new papers published between yesterday and today.
    today = date.today()
    yesterday = today - timedelta(days=1)
    today = today.strftime('%Y-%m-%d')
    yesterday = yesterday.strftime('%Y-%m-%d')

    parser = argparse.ArgumentParser(description='BioArxiv Daemon')
    parser.add_argument('-s', '--start', type=int, default=0, help='start at what index')
    parser.add_argument('-ds', '--date_start', type=str, default=yesterday, help='start of date interval to search rxiv papers. Format: (YYYY-mm-dd)')
    parser.add_argument('-de', '--date_end',   type=str, default=today,     help='end of date interval to search rxiv papers. Format: (YYYY-mm-dd)')
    args = parser.parse_args()
    print(args)

    pdb = get_papers_db(flag='c')
    mdb = get_metas_db(flag='c')
    prevn = len(pdb)

    def store(p):
        pdb[p['_id']] = p
        mdb[p['_id']] = {'_time': p['_time'], 'collection': p['collection']}

    def bioarxiv_fetch(query, start_idx):
        logging.info(f"querying {query['server']} api at start_index {start_idx} in date range [{query['date_start']}, {query['date_end']}].")

        # attempt to fetch a batch of papers from arxiv api
        ntried = 0
        while True:
            try:
                resp = get_response(search_query=query, start_index=start_idx)
                papers, total_papers = parse_response(resp)
                time.sleep(0.5)
                break
            except Exception as e:
                logging.warning(e)
                logging.warning("will try again in a bit...")
                ntried += 1
                if ntried > 1000:
                    logging.error("ok we tried 1,000 times, something is srsly wrong. exitting.")
                    sys.exit()
                time.sleep(2 + random.uniform(0, 4))
        
        return papers, total_papers

    
    def process_retrieved_papers(papers):
        # process the batch of retrieved papers
        nhad, nnew, nreplace = 0, 0, 0
        for p in papers:
            pid = p['_id']
            if pid in pdb:
                if p['_time'] > pdb[pid]['_time']:
                    # replace, this one is newer
                    store(p)
                    nreplace += 1
                else:
                    # we already had this paper, nothing to do
                    nhad += 1
            else:
                # new, simple store into database
                store(p)
                nnew += 1
        prevn = len(pdb)

        # some diagnostic information on how things are coming along
        logging.info(papers[0]['_time_str'])
        logging.info("k=%d, out of %d: had %d, replaced %d, new %d. now total db size: %d" %
             (k, len(papers), nhad, nreplace, nnew, prevn))

        nupdated = nreplace + nnew
        
        return nupdated


    ### main update loop ### 
    total_updated = 0

    # query to build api call
    q = {
        'date_start': args.date_start,
        'date_end': args.date_end,
    }
    
    for server in ['biorxiv', 'medrxiv']: 
        
        q['server'] = server

        # get first batch of max. 100 papers + total number of published papers in date interval
        k = args.start
        papers, total_papers = bioarxiv_fetch(q, start_idx=k)
        nupdated = process_retrieved_papers(papers)
        total_updated += nupdated

        # zzz
        time.sleep(1 + random.uniform(0, 3))

        # iterate over remaining papers in dateinterval in case there are more
        for k in range(args.start+100, total_papers, 100):
            papers, _ = bioarxiv_fetch(q, start_idx=k)
            nupdated = process_retrieved_papers(papers)
            total_updated += nupdated

            # zzz
            time.sleep(1 + random.uniform(0, 3))

    # exit with OK status if anything at all changed, but if nothing happened then raise 1
    sys.exit(0 if total_updated > 0 else 1)
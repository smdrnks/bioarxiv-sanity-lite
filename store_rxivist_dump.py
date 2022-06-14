
from aslite.db import get_papers_db, get_metas_db, get_tags_db
from datetime import datetime
import pandas as pd
import time
from tqdm import tqdm

def get_author_list(author_df, article_id):
    authors = author_df[author_df.article == article_id].copy().reset_index(drop=True).noperiodname.tolist()
    formatted = []
    for author in authors:
        author = ' '.join(author.split())
        names = author.split(' ')
        name = names[-1]
        for n in reversed(names[:-1]):
            name = f'{n[0]}. {name}'
        formatted.append(name)
    return formatted


def bioarxiv_db_entry(paper):
    db_entry = {}

    server = paper['repo']
    
    pid = paper['doi'].split('/')[1]
    db_entry['id'] = pid
    db_entry['link'] = f"https://www.{server}.org/content/{paper['doi']}"
    db_entry['title'] = paper['title']
    db_entry['summary'] = paper['abstract']
    db_entry['authors'] = [{'name': author} for author in get_author_list(df_article_authors, paper['id'])]
    db_entry['arxiv_primary_category'] = paper['collection']

    dt = datetime.strptime(paper['posted'], '%Y-%m-%d')
    db_entry['_time'] = time.mktime(dt.timetuple())
    db_entry['_time_str'] = datetime.strftime(dt, '%b %d %Y')
    db_entry['tags'] = [{'term': server}, {'term': paper['collection']}]
    db_entry['_id'] = pid
    version = paper['article_version']
    db_entry['_idv'] = f"{pid}v{version}"
    db_entry['_version'] = version

    return db_entry


if __name__=='__main__':

    pdb = get_papers_db(flag='c')
    mdb = get_metas_db(flag='c')
    prevn = len(pdb)

    def store(p):
        pdb[p['_id']] = p
        mdb[p['_id']] = {'_time': p['_time']}

    # load data
    df = pd.read_csv('./data/rxivist_dump/rxivist_dump.csv')
    df_article_authors = pd.read_csv('./data/rxivist_dump/article_author_mapping.csv')

    nhad, nnew, nreplace = 0, 0, 0
    for _, paper in tqdm(df.iterrows(), total=df.shape[0]):
        
        try:
            p = bioarxiv_db_entry(paper)
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

        except:
            print('failed:', paper.url)
            
    print(f'{nnew} new papers; {nreplace} papers replaced; now have {len(pdb)}')


    

    
    
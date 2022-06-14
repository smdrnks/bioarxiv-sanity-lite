# bioarxiv-sanity-lite
This is a fork of the awesome <a href="https://github.com/karpathy/arxiv-sanity-lite">arxiv-sanity lite</a> by <a href="https://twitter.com/karpathy">@karpathy</a>. The server periodically pulls new papers from <a href="https://www.biorxiv.org/">bioRxiv</a> and <a href="https://www.medrxiv.org/">medRxiv</a>. Then allows users to tag papers of interest, and recommends new papers for each tag based on SVMs over tfidf features of paper abstracts. Allows one to search, rank, sort, slice and dice these results in a pretty web UI. Lastly, bioarxiv-sanity-lite can send you daily emails with recommendations of new papers based on your tags.

![Screenshot](screenshot.png)

#### To run

To run this locally I usually run the following script to update the database with any new papers. I typically schedule this via a periodic cron job:

```bash
#!/bin/bash

python bioarxiv_daemon.py

if [ $? -eq 0 ]; then
    echo "New papers detected! Running compute.py"
    python compute.py
else
    echo "No new papers were added, skipping feature computation"
fi
```

You can see that updating the database is a matter of first downloading the new papers via the arxiv api using `bioarxiv_daemon.py`, and then running `compute.py` to compute the tfidf features of the papers. Finally to serve the flask server locally we'd run something like:

```bash
export FLASK_APP=serve.py; flask run
```

All of the database will be stored inside the `data` directory. Finally, if you'd like to run your own instance on the interwebs I recommend simply running the above on a [Linode](https://www.linode.com), e.g. I am running this code currently on the smallest "Nanode 1 GB" instance indexing about 30K papers, which costs $5/month.

(Optional) Finally, if you'd like to send periodic emails to users about new papers, see the `send_emails.py` script. You'll also have to `pip install sendgrid`. I run this script in a daily cron job.

#### Requirements

 Install via requirements:

 ```bash
 pip install -r requirements.txt
 ```

#### Todos

- Build category filter to filter bioRxiv and medRxiv collections.

#### License

MIT

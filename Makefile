
# I run this to update the database with newest papers every day or so or etc.
up:
	python bioarxiv_daemon.py
	python compute.py

# I use this to run the server
fun:
	export FLASK_APP=serve.py; flask run

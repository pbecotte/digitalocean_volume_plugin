FROM python:3.5
WORKDIR /app/

RUN apt-get update && apt-get install -y parted

RUN pip install requests flask uwsgi
COPY digitalocean.py /app/
CMD uwsgi --http-socket /run/docker/plugins/digitalocean.sock --chdir /app --wsgi-file digitalocean.py --callable app --close-on-exec

FROM python:3.5
WORKDIR /app/

RUN apt-get update && apt-get install -y parted

COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app/
CMD uwsgi --http-socket /run/docker/plugins/digitalocean.sock --chdir /app --wsgi-file wsgi.py --callable app --close-on-exec

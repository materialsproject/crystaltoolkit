FROM python:3.7
LABEL maintainer="mkhorton@lbl.gov"

RUN apt update && apt install vim povray asymptote -y

RUN mkdir -p /home/project/dash_app
WORKDIR /home/project/dash_app

RUN pip install --no-cache-dir numpy scipy

ADD requirements.txt /home/project/dash_app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# whether to embed in materialsproject.org or not
ENV CRYSTAL_TOOLKIT_MP_EMBED_MODE=False

ENV CRYSTAL_TOOLKIT_NUM_WORKERS=16

# for Crossref API, used for DOI lookups
ENV CROSSREF_MAILTO=YOUR_EMAIL_HERE

# this can be obtained from materialsproject.org
ENV PMG_MAPI_KEY=YOUR_MP_API_KEY_HERE

# whether to run the server in debug mode or not
ENV CRYSTAL_TOOLKIT_DEBUG_MODE=False

ADD . /home/project/dash_app

EXPOSE 8000
CMD gunicorn --workers=$CRYSTAL_TOOLKIT_NUM_WORKERS --timeout=300 --bind=0.0.0.0 crystal_toolkit.apps.main_app:server

FROM python:3.9
LABEL maintainer="mkhorton@lbl.gov"

RUN apt-get update && apt-get install vim gfortran povray -y

WORKDIR /home/build

# install critic2
RUN git clone https://github.com/aoterodelaroza/critic2.git && \
    cd critic2 && git checkout 84da382 && autoreconf && ./configure && \
    make && make install

# install enumlib
ENV F90 gfortran
RUN git clone --recursive https://github.com/msg-byu/enumlib.git && \
    cd enumlib && git checkout 165c917 && cd symlib/src/ && make && \
    cd ../../src && make enum.x && make makestr.x && \
    cp enum.x makestr.x /usr/local/bin

WORKDIR /home/app

RUN pip install --upgrade --no-cache-dir pip && \
    pip install -r requirements/ubuntu-latest_py3.9_extras.txt

# whether to embed in materialsproject.org or not
ENV CRYSTAL_TOOLKIT_MP_EMBED_MODE=False

ENV CRYSTAL_TOOLKIT_NUM_WORKERS=16

# for Crossref API, used for DOI lookups
ENV CROSSREF_MAILTO=YOUR_EMAIL_HERE

# this can be obtained from materialsproject.org
ENV PMG_MAPI_KEY=YOUR_MP_API_KEY_HERE

# whether to run the server in debug mode or not
ENV CRYSTAL_TOOLKIT_DEBUG_MODE=False

ADD . /home/app

EXPOSE 8000
CMD gunicorn --workers=$CRYSTAL_TOOLKIT_NUM_WORKERS --timeout=300 --bind=0.0.0.0 crystal_toolkit.apps.main:server

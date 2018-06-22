FROM python:3.6.5

RUN mkdir -p /home/project/dash_app
ADD . /home/project/dash_app
WORKDIR /home/project/dash_app

RUN pip install numpy scipy
RUN pip install --no-cache-dir -r requirements.txt
CMD ["gunicorn", "--workers $NUM_WORKERS", "app:server"]

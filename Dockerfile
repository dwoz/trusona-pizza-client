FROM python:3.4-alpine
ADD . /code
WORKDIR /code
RUN pip3 install -r requirements.txt
RUN python3 setup.py develop
RUN pytest -v
CMD pizza-client

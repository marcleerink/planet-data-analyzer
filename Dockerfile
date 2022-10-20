FROM python:3.10.4
WORKDIR /code
ENV PL_API_KEY='PLAKfef2608cfa784a2baae1ed95ce507bb1'
ENV DB_NAME='planet'
ENV DB_PW='5jippie5'
ENV DB_USER='postgres'
ENV DB_HOST='localhost'
ENV DB_PORT='5432'
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
EXPOSE 5000
COPY . .

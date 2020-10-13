FROM python:3.8-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy source code from the local host
#  to the filesystem of the container at the working directory
COPY . .

CMD ["python", "./main.py"]

LABEL org.opencontainers.image.source https://github.com/robin-castellani/website-monitor
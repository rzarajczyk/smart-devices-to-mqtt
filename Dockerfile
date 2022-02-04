FROM python:3
ENV TZ="Europe/Warsaw"
ENV SD_ROOT="/smart-devices-to-graphite"

RUN mkdir -p /smart-devices-to-graphite
RUN mkdir -p /smart-devices-to-graphite/config
RUN mkdir -p /smart-devices-to-graphite/logs

WORKDIR /smart-devices-to-graphite

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./src/main/main.py"]
#CMD ["bash"]

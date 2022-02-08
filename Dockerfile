FROM python:3
ENV TZ="Europe/Warsaw"
ENV APP_ROOT="/smart-devices-to-mqtt"

RUN mkdir -p /smart-devices-to-mqtt
RUN mkdir -p /smart-devices-to-mqtt/config
RUN mkdir -p /smart-devices-to-mqtt/logs

WORKDIR /smart-devices-to-mqtt

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./src/main/main.py"]
#CMD ["bash"]

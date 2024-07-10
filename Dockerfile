FROM python:3.9

RUN apt-get update && apt-get upgrade -y
RUN apt-get install cron -y
# RUN apt-get install -y libhdf5-dev
RUN pip install --upgrade pip
# RUN pip install --no-binary h5py h5py

COPY . /app

WORKDIR /app

RUN pip install --no-cache-dir --upgrade -r requirements.txt 

HEALTHCHECK --interval=120s --timeout=30s --start-period=5s --retries=3 CMD curl --fail http://localhost:6000/health || exit 1

CMD ["python3", "./src/cron.py"]

# DOCKER_DEFAULT_PLATFORM="linux/amd64" docker build . -t ixxc/prediction_amd64:1.0
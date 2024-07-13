FROM python:3.12.2-bookworm

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY dvi_exporter.py ./
COPY output_mapping.json ./

CMD [ "python", "./dvi_exporter.py" ]

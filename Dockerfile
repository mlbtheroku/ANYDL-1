FROM python:3.11.1

WORKDIR .
RUN apt -qq update && apt -qq install -y git p7zip ffmpeg

COPY . .

RUN pip3 install -r requirements.txt

CMD ["python3", "bot.py"]

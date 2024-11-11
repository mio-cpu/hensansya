FROM python:3.11
WORKDIR /bot

COPY requirements.txt /bot/
RUN pip install -r requirements.txt

# 永続的なボリュームを設定
VOLUME /bot/data

EXPOSE 8080
COPY . /bot
CMD python main.py

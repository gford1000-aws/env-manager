FROM python:alpine3.7
COPY ./requirements.txt /tmp/requirements.txt
RUN apk add --no-cache --virtual .build-deps g++ musl-dev \
 && pip install --upgrade pip \
 && pip install -r /tmp/requirements.txt \
 && apk del .build-deps \
 && apk add libstdc++
RUN addgroup -g 1000 -S env_mgr && \
    adduser -u 1000 -S env_mgr -G env_mgr
USER env_mgr
COPY ./server /home/env_mgr/server
WORKDIR /home/env_mgr/server
EXPOSE 50055
CMD python ./aws_env_server.py --p 50055

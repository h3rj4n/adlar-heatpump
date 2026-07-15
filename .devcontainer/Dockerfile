FROM mcr.microsoft.com/devcontainers/python:3.14

RUN apt-get update && \
    apt-get install -y ffmpeg libturbojpeg0-dev libpcap0.8 && \
    rm -rf /var/lib/apt/lists/*

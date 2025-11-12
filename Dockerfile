FROM ubuntu:22.04
USER root

WORKDIR /workspace

ENV TZ=Asia/Tokyo
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y && \
    apt-get install -y \
    python3.10 \
    python3-pip \
    libgl1-mesa-dev \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# pythonコマンドの参照先をPython3.10に変更
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1

# requirements.txtをコピーしてインストール
COPY requirements.txt /workspace/
RUN pip install -r requirements.txt

CMD ["/bin/bash"]
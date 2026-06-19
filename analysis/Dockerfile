FROM ubuntu:22.04

RUN sed -i 's@//.*archive.ubuntu.com@//mirrors.aliyun.com@g; s@//.*security.ubuntu.com@//mirrors.aliyun.com@g' /etc/apt/sources.list \
    && apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 python3-pip perl linux-tools-generic git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://gitee.com/mirrors/FlameGraph.git /opt/FlameGraph

ENV FLAMEGRAPH_DIR=/opt/FlameGraph
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV PIP_TRUSTED_HOST=mirrors.aliyun.com

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
COPY . .

ENTRYPOINT ["python3", "hotmethod_analyzer.py"]

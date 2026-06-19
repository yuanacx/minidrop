FROM ubuntu:22.04

RUN sed -i 's@//.*archive.ubuntu.com@//mirrors.aliyun.com@g; s@//.*security.ubuntu.com@//mirrors.aliyun.com@g' /etc/apt/sources.list \
    && apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 python3-pip linux-tools-common linux-tools-generic \
    linux-tools-5.15.0-179-generic linux-cloud-tools-5.15.0-179-generic \
    bpftrace curl \
    && rm -rf /var/lib/apt/lists/* \
    && (test -x /usr/bin/perf || ln -sf /usr/lib/linux-tools/*/perf /usr/bin/perf)

ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV PIP_TRUSTED_HOST=mirrors.aliyun.com

RUN pip3 install --no-cache-dir py-spy

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
COPY . .

ENV PORT=50051
EXPOSE 50051

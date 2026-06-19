FROM golang:1.21-alpine AS build
ENV GOPROXY=https://goproxy.cn,direct
WORKDIR /src
COPY go.mod ./
RUN go mod download 2>/dev/null || true
COPY . .
RUN go mod tidy && CGO_ENABLED=0 go build -o /apiserver .

FROM ubuntu:22.04
RUN sed -i 's@//.*archive.ubuntu.com@//mirrors.aliyun.com@g; s@//.*security.ubuntu.com@//mirrors.aliyun.com@g' /etc/apt/sources.list \
    && apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 python3-pip perl git ca-certificates \
    linux-tools-common linux-tools-5.15.0-179-generic linux-cloud-tools-5.15.0-179-generic \
    && rm -rf /var/lib/apt/lists/* \
    && (test -x /usr/bin/perf || ln -sf /usr/lib/linux-tools/*/perf /usr/bin/perf)
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV PIP_TRUSTED_HOST=mirrors.aliyun.com
RUN pip3 install --no-cache-dir minio PyYAML requests \
    && git clone --depth 1 https://gitee.com/mirrors/FlameGraph.git /opt/FlameGraph
ENV FLAMEGRAPH_DIR=/opt/FlameGraph
WORKDIR /app
COPY --from=build /apiserver /app/apiserver
EXPOSE 8191
CMD ["/app/apiserver"]

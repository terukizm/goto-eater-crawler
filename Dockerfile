FROM ubuntu:focal

# for playwright
# @see https://github.com/microsoft/playwright-python/blob/master/Dockerfile

# 1. Install latest Python
RUN apt-get update && apt-get install -y python3 python3-pip && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3 1

# 2. Install WebKit dependencies
RUN apt-get update && DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends \
    libwoff1 \
    libopus0 \
    libwebp6 \
    libwebpdemux2 \
    libenchant1c2a \
    libgudev-1.0-0 \
    libsecret-1-0 \
    libhyphen0 \
    libgdk-pixbuf2.0-0 \
    libegl1 \
    libnotify4 \
    libxslt1.1 \
    libevent-2.1-7 \
    libgles2 \
    libxcomposite1 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libepoxy0 \
    libgtk-3-0 \
    libharfbuzz-icu0

# 3. Install gstreamer and plugins to support video playback in WebKit.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libvpx6\
    libgstreamer-plugins-base1.0-0\
    libgstreamer1.0-0\
    libgstreamer-gl1.0-0\
    libgstreamer-plugins-bad1.0-0\
    libopenjp2-7\
    gstreamer1.0-libav

WORKDIR /tmp
COPY pyproject.toml poetry.lock ./

RUN apt-get update \
    && apt-get install -y gcc python3-dev git \
    # for tabula-py
    && mkdir -p /usr/share/man/man1 && apt-get install -y openjdk-11-jdk \
    && pip install --upgrade pip \
    && pip install --no-cache-dir poetry && poetry config virtualenvs.create false && poetry install --no-dev \
    && playwright install webkit \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CMD ["python", "-m" "goto_eat_scrapy.main"]

FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 \
    FLUTTER_VERSION=stable \
    FLUTTER_HOME=/opt/flutter ANDROID_HOME=/opt/android-sdk ANDROID_SDK_ROOT=/opt/android-sdk \
    PUB_CACHE=/cache/pub GRADLE_USER_HOME=/cache/gradle
ENV PATH=/opt/flutter/bin:/opt/flutter/bin/cache/dart-sdk/bin:/cache/pub/bin:/opt/android-sdk/cmdline-tools/latest/bin:/opt/android-sdk/platform-tools:/opt/venv/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl wget git git-lfs unzip zip xz-utils jq make cmake ninja-build pkg-config clang \
    build-essential openjdk-17-jdk-headless python3 python3-venv python3-pip \
    libglu1-mesa libgl1 libegl1 libgtk-3-dev xvfb xauth fonts-liberation fonts-noto-core fonts-noto-color-emoji fontconfig \
    imagemagick ffmpeg sqlite3 openssh-client rsync procps less nano tini \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o /usr/share/keyrings/gh.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/gh.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/gh.list \
    && apt-get update && apt-get install -y gh && rm -rf /var/lib/apt/lists/*

# Flutter SDK (channel stable)
RUN git clone --depth 1 -b stable https://github.com/flutter/flutter.git $FLUTTER_HOME \
    && git config --global --add safe.directory '*' \
    && flutter config --no-analytics --enable-android --enable-web --no-enable-linux-desktop \
    && dart --disable-analytics || true

# Android SDK
RUN mkdir -p $ANDROID_HOME/cmdline-tools && cd /tmp \
    && curl -fsSL -o cmd.zip https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip \
    && unzip -q cmd.zip && mv cmdline-tools $ANDROID_HOME/cmdline-tools/latest && rm cmd.zip \
    && yes | sdkmanager --licenses >/dev/null \
    && sdkmanager "platform-tools" "build-tools;34.0.0" "build-tools;35.0.0" "platforms;android-34" "platforms;android-35" "platforms;android-36" "ndk;27.0.12077973" "cmake;3.22.1" >/dev/null

# Python outils (analyse, assets, QA visuelle)
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir pillow numpy matplotlib scikit-image pyyaml requests trimesh pygltflib

# Node 22 + outils glTF/3D (sharp doit embarquer ses binaires optionnels linux-x64)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs && rm -rf /var/lib/apt/lists/* \
    && npm install -g @gltf-transform/cli gltf-pipeline \
    && cd /usr/local/lib/node_modules/@gltf-transform/cli && npm install --include=optional --os=linux --cpu=x64 sharp \
    && gltf-transform --version

# Précharge Flutter (artefacts Android + web) et vérifie
RUN flutter precache --android --web && flutter --version && (flutter doctor -v || true)

RUN mkdir -p /cache/pub /cache/gradle /workspace && chmod -R 777 /cache /workspace
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
WORKDIR /workspace
ENTRYPOINT ["/usr/bin/tini","--","/usr/local/bin/entrypoint.sh"]
CMD ["sleep","infinity"]

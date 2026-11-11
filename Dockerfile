FROM osrf/ros:jazzy-desktop-full

ENV DEBIAN_FRONTEND=noninteractive
ENV EDITOR=nano
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# 1. Herramientas básicas, nano, screen, socat (puertos virtuales), librerías gráficas y AVR
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gpg \
    wget \
    git \
    gedit \
    screen \
    socat \
    libgl1 \
    libgl1-mesa-dri \
    python3-pip \
    python3-serial \
    gcc-avr \
    avr-libc \
    avrdude \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# 2. Paquetes ROS 2 para simulación y control (en una sola capa)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    && rm -rf /var/lib/apt/lists/*

# 3. KiCad 10.0 desde el PPA oficial
RUN add-apt-repository --yes ppa:kicad/kicad-10.0-releases \
    && apt-get update \
    && apt-get install -y --no-install-recommends kicad \
    && rm -rf /var/lib/apt/lists/*

# 4. FreeCAD vía AppImage extraído
RUN LATEST_URL=$(curl -s https://api.github.com/repos/FreeCAD/FreeCAD/releases/latest \
        | grep "browser_download_url" | grep "Linux-x86_64" | grep "AppImage" \
        | head -n 1 | cut -d '"' -f 4) \
    && wget "$LATEST_URL" -O freecad.AppImage \
    && chmod +x freecad.AppImage \
    && ./freecad.AppImage --appimage-extract \
    && mv squashfs-root /opt/freecad \
    && ln -s /opt/freecad/AppRun /usr/local/bin/freecad \
    && rm -f freecad.AppImage

# 5. VS Code y dependencias Qt para SimulIDE
RUN wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg \
    && install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list \
    && rm -f packages.microsoft.gpg \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        code \
        libqt5xml5 \
        libqt5widgets5 \
        libqt5gui5 \
        libqt5core5a \
        libqt5serialport5 \
    && rm -rf /var/lib/apt/lists/*

# 6. SimulIDE (AppImage extraído, sin FUSE)
RUN SIMULIDE_URL=$(curl -sL https://launchpad.net/simulide/+download \
        | grep -o 'href="[^"]*Lin64[^"]*\.tar\.gz"' | head -n 1 | cut -d '"' -f 2) \
    && case "$SIMULIDE_URL" in /*) SIMULIDE_URL="https://launchpad.net$SIMULIDE_URL" ;; esac \
    && echo "Descargando SimulIDE desde: $SIMULIDE_URL" \
    && wget "$SIMULIDE_URL" -O simulide.tar.gz \
    && tar -xzf simulide.tar.gz -C /opt/ \
    && rm simulide.tar.gz \
    && SIMULIDE_DIR=$(find /opt -maxdepth 1 -name "SimulIDE*" -type d | head -n 1) \
    && cd "$SIMULIDE_DIR" \
    && chmod +x simulide \
    && ./simulide --appimage-extract \
    && cp -r data examples squashfs-root/usr/bin/ \
    && rm -f simulide \
    && printf '#!/bin/bash\nexec "%s/squashfs-root/AppRun" "$@"\n' "$SIMULIDE_DIR" > /usr/local/bin/simulide \
    && chmod +x /usr/local/bin/simulide

# 7. PlatformIO y plugin A2plus de FreeCAD (sin caché)
RUN pip3 install --no-cache-dir --break-system-packages -U platformio \
    && mkdir -p /root/.local/share/FreeCAD/Mod \
    && git clone --depth 1 https://github.com/kbwbe/A2plus.git /root/.local/share/FreeCAD/Mod/A2plus \
    && rm -rf /root/.local/share/FreeCAD/Mod/A2plus/.git

# 8. YOLO (ultralytics) con PyTorch solo CPU, mucho más pequeño que la versión CUDA
RUN pip3 install --no-cache-dir --break-system-packages \
        torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip3 install --no-cache-dir --break-system-packages --ignore-installed numpy ultralytics \
    && rm -rf /root/.cache

# 9. Entorno de ROS 2 automático
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc

CMD ["bash"]
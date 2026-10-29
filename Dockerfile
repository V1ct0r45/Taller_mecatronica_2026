FROM osrf/ros:jazzy-desktop-full

ENV DEBIAN_FRONTEND=noninteractive

# 1. Instalar herramientas básicas, librerías gráficas, Arduino y puertos virtuales
RUN apt-get update && apt-get install -y \
    curl \
    gpg \
    wget \
    libgl1 \
    libgl1-mesa-dri \
    python3-pip \
    git \
    software-properties-common \
    arduino \
    arduino-core \
    gcc-avr \
    avr-libc \
    avrdude \
    socat \
    python3-serial \
    && rm -rf /var/lib/apt/lists/*

# 2. Instalar KiCad 10.0 desde el repositorio oficial
RUN add-apt-repository --yes ppa:kicad/kicad-10.0-releases \
    && apt-get update \
    && apt-get install -y kicad

# 3. Instalar FreeCAD vía AppImage extraído (Descarga dinámica)
RUN LATEST_URL=$(curl -s https://api.github.com/repos/FreeCAD/FreeCAD/releases/latest | grep "browser_download_url" | grep "Linux-x86_64" | grep "AppImage" | head -n 1 | cut -d '"' -f 4) \
    && wget "$LATEST_URL" -O freecad.AppImage \
    && chmod +x freecad.AppImage \
    && ./freecad.AppImage --appimage-extract \
    && mv squashfs-root /opt/freecad \
    && ln -s /opt/freecad/AppRun /usr/local/bin/freecad \
    && rm freecad.AppImage

# 4. Instalar VS Code y dependencias para SimulIDE
RUN wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg \
    && install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list \
    && rm -f packages.microsoft.gpg \
    && apt-get update && apt-get install -y \
    code \
    libqt5xml5 \
    libqt5widgets5 \
    libqt5gui5 \
    libqt5core5a \
    libqt5serialport5 \
    && rm -rf /var/lib/apt/lists/*

# 5. Descargar e instalar SimulIDE (Descarga dinámica y extracción de AppImage interno)
RUN SIMULIDE_URL=$(curl -sL https://launchpad.net/simulide/+download | grep -o 'href="[^"]*Lin64[^"]*\.tar\.gz"' | head -n 1 | cut -d '"' -f 2) \
    && case "$SIMULIDE_URL" in /*) SIMULIDE_URL="https://launchpad.net$SIMULIDE_URL" ;; esac \
    && echo "Descargando SimulIDE desde: $SIMULIDE_URL" \
    && wget "$SIMULIDE_URL" -O simulide.tar.gz \
    && tar -xzf simulide.tar.gz -C /opt/ \
    && rm simulide.tar.gz \
    && SIMULIDE_DIR=$(find /opt -maxdepth 1 -name "SimulIDE*" -type d | head -n 1) \
    && cd "$SIMULIDE_DIR" \
    && chmod +x simulide \
    && ./simulide --appimage-extract \
    && ln -s "$SIMULIDE_DIR/squashfs-root/AppRun" /usr/local/bin/simulide
# 6. Instalar PlatformIO
RUN pip3 install --break-system-packages -U platformio
RUN mkdir -p /root/.local/share/FreeCAD/Mod \
    && git clone https://github.com/kbwbe/A2plus.git /root/.local/share/FreeCAD/Mod/A2plus

# 7. Configurar el entorno automático de ROS 2
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc


CMD ["bash"]
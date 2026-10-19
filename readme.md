## 1. Construcción Inicial (Solo la primera vez)
```bash
sudo docker compose build
```

## 2. Iniciar el Entorno
```bash
sudo docker compose up -d
```

## 3. Entrar a la Terminal de Ubuntu
```bash
sudo docker exec -it taller_torreta bash
```

## 4. Compilar Código ROS 2 (Dentro de Ubuntu)
```bash
cd ros2_ws
colcon build
source install/setup.bash
```

## 5. Abrir Simuladores (Dentro de Ubuntu)
Escribe cualquiera de estos comandos y presiona Enter:
* `simulide`
* `freecad`
* `kicad`
* `pio`
* `rviz2`
* `gz sim`

## 6. Apagar el Entorno (Al terminar el taller)
Desde tu terminal principal (fuera de Ubuntu), ejecuta:
```bash
sudo docker compose down
```

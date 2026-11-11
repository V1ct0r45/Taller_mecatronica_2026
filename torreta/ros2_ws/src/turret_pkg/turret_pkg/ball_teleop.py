#!/usr/bin/env python3
import select
import subprocess
import sys
import termios
import tty

import rclpy
from rclpy.node import Node

WORLD = 'taller_world'
BALL = 'pelota_naranja'
STEP = 0.02                      # metros por pulsación

# Posición inicial: debe coincidir con la <pose> del SDF
X_INICIAL = 0
Y_FIJO = -0.8                    # la pelota no se mueve en Y
Z_INICIAL = 0.3

X_RANGO = (-1, 1.0)             # profundidad (hacia/desde la cámara)
Z_RANGO = (0.05, 0.6)            # 0.05 = tocando el piso

MOVIMIENTOS = {
    'a': (STEP, 0.0),           # -X
    'd': (-STEP, 0.0),            # +X
    'w': (0.0, STEP),            # +Z (arriba)
    's': (0.0, -STEP),           # -Z (abajo)
}


class BallTeleop(Node):
    def __init__(self):
        super().__init__('ball_teleop')
        self.x = X_INICIAL
        self.z = Z_INICIAL

        self.fd = sys.stdin.fileno()
        self.viejo = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)

        self.enviar_pose()
        self.get_logger().info('A/D: eje X | W/S: eje Z | Q: salir')
        self.create_timer(0.05, self.leer_teclas)

    def enviar_pose(self):
        req = (f'name: "{BALL}", '
               f'position: {{x: {self.x:.3f}, y: {Y_FIJO:.3f}, z: {self.z:.3f}}}, '
               f'orientation: {{w: 1.0}}')
        subprocess.run([
            'gz', 'service', '-s', f'/world/{WORLD}/set_pose',
            '--reqtype', 'gz.msgs.Pose',
            '--reptype', 'gz.msgs.Boolean',
            '--timeout', '300',
            '--req', req,
        ], capture_output=True)

    def leer_teclas(self):
        while select.select([sys.stdin], [], [], 0)[0]:
            tecla = sys.stdin.read(1).lower()
            if tecla == 'q':
                raise KeyboardInterrupt
            if tecla in MOVIMIENTOS:
                dx, dz = MOVIMIENTOS[tecla]
                self.x = min(max(self.x + dx, X_RANGO[0]), X_RANGO[1])
                self.z = min(max(self.z + dz, Z_RANGO[0]), Z_RANGO[1])
                self.enviar_pose()
                self.get_logger().info(f'Pelota en x={self.x:.2f}, z={self.z:.2f}')

    def destroy_node(self):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.viejo)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = BallTeleop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
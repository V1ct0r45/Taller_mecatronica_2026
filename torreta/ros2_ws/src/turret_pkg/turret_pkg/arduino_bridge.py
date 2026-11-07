#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory
import serial
import math
import sys

class ArduinoNode(Node):
    def __init__(self):
        super().__init__('arduino_node')
        
        # Declarar parámetros para el puerto serial (útil si cambia al reconectar)
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 115200)
        
        port = self.get_parameter('port').get_parameter_value().string_value
        baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        
        # Iniciar conexión serial
        try:
            self.arduino = serial.Serial(port, baudrate, timeout=0.1)
            self.get_logger().info(f"Conectado exitosamente al Arduino en {port} a {baudrate} bps.")
        except serial.SerialException as e:
            self.get_logger().error(f"Error al conectar con el Arduino en {port}: {e}")
            self.get_logger().error("Revisa los permisos: sudo chmod a+rw /dev/ttyUSB0")
            sys.exit(1) # Sale del nodo si no hay hardware conectado

        # Suscripción al tópico del teleop de tu compañero
        self.subscription = self.create_subscription(
            JointTrajectory,
            '/pan_tilt_controller/joint_trajectory',
            self.trajectory_callback,
            10)

    def trajectory_callback(self, msg):
        if not self.arduino.is_open or not msg.points:
            return

        # Buscar los índices correctos de las articulaciones en el mensaje
        try:
            pan_idx = msg.joint_names.index('pan_joint')
            tilt_idx = msg.joint_names.index('tilt_joint')
        except ValueError:
            self.get_logger().warn("El mensaje no contiene 'pan_joint' o 'tilt_joint'. Ignorando.")
            return

        # Extraer posiciones en radianes (desde el primer punto de la trayectoria)
        pan_rad = msg.points[0].positions[pan_idx]
        tilt_rad = msg.points[0].positions[tilt_idx]

        # Convertir de radianes (-1.57 a 1.57) a grados (0 a 180) para los servos
        # 0 radianes = 90 grados (centro)
        pan_deg = int(math.degrees(pan_rad) + 90)
        tilt_deg = int(math.degrees(tilt_rad) + 90)

        modo = 1 # Modo activo por defecto mientras recibe comandos

        # Armar la trama para el Arduino Nano
        trama = f"{modo},{pan_deg},{tilt_deg}\n"
        
        # Enviar por serial
        self.arduino.write(trama.encode('utf-8'))
        
        # Imprimir en terminal para monitoreo (puedes comentarlo si satura la consola)
        self.get_logger().info(f"Enviando al Arduino -> Modo: {modo} | Pan: {pan_deg}° | Tilt: {tilt_deg}°")

def main(args=None):
    rclpy.init(args=args)
    node = ArduinoNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Nodo detenido por el usuario.")
    finally:
        # Asegurarse de cerrar el puerto serial limpiamente
        if hasattr(node, 'arduino') and node.arduino.is_open:
            # Enviar trama de seguridad (Modo 0) antes de cerrar
            node.arduino.write("0,90,45\n".encode('utf-8'))
            node.arduino.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from geometry_msgs.msg import Twist
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import sys
import termios
import tty
import select

class TurretTeleop(Node):
    def __init__(self):
        super().__init__('turret_teleop', 
                       allow_undeclared_parameters=True, 
                       parameter_overrides=[Parameter('use_sim_time', Parameter.Type.BOOL, True)])
                       
        self.publisher_ = self.create_publisher(JointTrajectory, '/pan_tilt_controller/joint_trajectory', 10)
        
        self.pan_pos = 0.0
        self.tilt_pos = 0.0
        self.step = 0.05 
        
        # NUEVO: Guardar el último momento en que publicamos para evitar saturación de comandos
        self.last_pub_time = self.get_clock().now()
        
        print("========================================")
        print("🎮 NODO DE CONTROL (MOVIMIENTO FLUIDO)")
        print("Usa las FLECHAS del teclado para moverla.")
        print("Mantenlas presionadas para movimiento continuo.")
        print("Presiona Ctrl+C para salir.")
        print("========================================")

    def process_twist(self, twist_msg):
        # FILTRO DE FRECUENCIA: Solo permite enviar una orden cada 0.1 segundos. 
        # Esto soluciona el problema de mantener la tecla presionada.
        current_time = self.get_clock().now()
        if (current_time - self.last_pub_time).nanoseconds < 100000000: 
            return 
        self.last_pub_time = current_time

        # Matemáticas de movimiento
        if twist_msg.linear.x > 0:
            self.tilt_pos -= self.step 
        elif twist_msg.linear.x < 0:
            self.tilt_pos += self.step
            
        if twist_msg.angular.z > 0:
            self.pan_pos += self.step 
        elif twist_msg.angular.z < 0:
            self.pan_pos -= self.step 

        # LÍMITES DE SEGURIDAD FÍSICOS
        # La base gira libre de -90 a 90 grados
        self.pan_pos = max(-1.5708, min(1.5708, self.pan_pos))
        # El cabeceo lo topamos en -0.75 rad hacia atrás para que no choque con la pieza azul
        self.tilt_pos = max(-0.75, min(1.2, self.tilt_pos)) 

        # Empaquetar y enviar el comando
        traj_msg = JointTrajectory()
        traj_msg.joint_names = ['pan_joint', 'tilt_joint']
        traj_msg.header.stamp = self.get_clock().now().to_msg()
        
        point = JointTrajectoryPoint()
        point.positions = [self.pan_pos, self.tilt_pos]
        point.time_from_start = Duration(sec=0, nanosec=100000000) 
        
        traj_msg.points.append(point)
        self.publisher_.publish(traj_msg)
        
        sys.stdout.write(f"\r\033[K[TELEMETRÍA] Pan: {self.pan_pos:.2f} rad | Tilt: {self.tilt_pos:.2f} rad")
        sys.stdout.flush()

def get_key(settings):
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
    if rlist:
        key = sys.stdin.read(1)
        if key == '\x1b':
            key += sys.stdin.read(2)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def main(args=None):
    rclpy.init(args=args)
    node = TurretTeleop()
    settings = termios.tcgetattr(sys.stdin)

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.01) 
            
            key = get_key(settings)
            
            if key == '':
                continue 
                
            twist = Twist()
            if key == '\x1b[A':   # ARRIBA
                twist.linear.x = 1.0
            elif key == '\x1b[B': # ABAJO
                twist.linear.x = -1.0
            elif key == '\x1b[C': # DERECHA
                twist.angular.z = -1.0
            elif key == '\x1b[D': # IZQUIERDA
                twist.angular.z = 1.0
            elif key == '\x03':   # Ctrl+C
                break
            else:
                continue
                
            node.process_twist(twist)
            
    except Exception as e:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()
        print("\nControl finalizado.")

if __name__ == '__main__':
    main()
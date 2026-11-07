#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Point
from cv_bridge import CvBridge
from ultralytics import YOLO
import os
import cv2  # NUEVO: Importar OpenCV para dibujar
from ament_index_python.packages import get_package_share_directory

class DetectorPelota(Node):
    def __init__(self):
        super().__init__('detector_pelota_node')
        self.bridge = CvBridge()
        
        # Buscar el archivo best.pt automáticamente en el paquete
        try:
            pkg_path = get_package_share_directory('vision')
            model_path = os.path.join(pkg_path, 'models', 'best.pt')
            self.model = YOLO(model_path)
            self.get_logger().info(f"Modelo YOLO cargado exitosamente desde {model_path}")
        except Exception as e:
            self.get_logger().error(f"Error al cargar el modelo: {e}")
            return
            
        # Suscribirse a la cámara MIPI 1
        self.sub = self.create_subscription(Image, '/camera_mipi1/image_raw', self.image_callback, 10)
        
        # Publicar el punto central de la pelota (lo lee el nodo de control PID)
        self.pub_pos = self.create_publisher(Point, '/vision/ball_position', 10)
        
        # NUEVO: Publicar la imagen procesada con el cuadro dibujado
        self.pub_img = self.create_publisher(Image, '/vision/image_annotated', 10)
        
    def image_callback(self, msg):
        # Convertir mensaje de ROS a imagen de OpenCV
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        
        # Inferencia rápida (verbose=False para no saturar la terminal)
        results = self.model(cv_image, verbose=False)
        
        pt_msg = Point()
        pt_msg.z = 0.0  # Z = 0 significa "Pelota NO detectada"
        
        if len(results[0].boxes) > 0:
            # Seleccionar la detección con más confianza
            best_box = results[0].boxes[0]
            x1, y1, x2, y2 = best_box.xyxy[0].tolist()
            
            # Calcular el centro
            center_x = (x1 + x2) / 2.0
            center_y = (y1 + y2) / 2.0
            
            pt_msg.x = center_x
            pt_msg.y = center_y
            pt_msg.z = 1.0  # Pelota detectada
            
            # NUEVO: Dibujar el rectángulo delimitador (color verde) y el punto central (color rojo)
            cv2.rectangle(cv_image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.circle(cv_image, (int(center_x), int(center_y)), 5, (0, 0, 255), -1)
            
        # Publicar coordenadas al nodo de control
        self.pub_pos.publish(pt_msg)
        
        # NUEVO: Convertir la imagen editada de vuelta a mensaje ROS y publicarla
        annotated_msg = self.bridge.cv2_to_imgmsg(cv_image, encoding='bgr8')
        annotated_msg.header = msg.header  # Mantener el tiempo exacto original
        self.pub_img.publish(annotated_msg)

def main(args=None):
    rclpy.init(args=args)
    node = DetectorPelota()
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
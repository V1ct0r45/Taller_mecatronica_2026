import os
from glob import glob
from setuptools import setup

package_name = 'turret_pkg'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Indicar a ROS 2 que instale las carpetas launch y urdf en la ruta compartida
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.xacro')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Asociacion Open Source',
    maintainer_email='contacto@ejemplo.com',
    description='Paquete de control y simulación de Torreta Pan-Tilt (Taller 2026)',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # Formato: 'nombre_comando = carpeta_paquete.nombre_archivo_python:main'
            'color_tracker = turret_pkg.color_tracker:main',
            'target_mover = turret_pkg.target_mover:main'
        ],
    },
)
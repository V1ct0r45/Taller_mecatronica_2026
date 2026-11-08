import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, AppendEnvironmentVariable, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.substitutions import Command
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    pkg_name = 'turret_description'
    pkg_share = get_package_share_directory(pkg_name)
    
    workspace_share_dir = os.path.abspath(os.path.join(pkg_share, '..'))
    
    set_env_gazebo_model = AppendEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=workspace_share_dir
    )

    xacro_file = os.path.join(pkg_share, 'urdf', 'pan_tilt.urdf.xacro')
    
    # Ruta hacia tu mundo personalizado en la carpeta worlds/
    world_file = os.path.join(pkg_share, 'worlds', 'taller_world.sdf')
    
    # 1. ROBOT STATE PUBLISHER
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(Command(['xacro ', xacro_file]), value_type=str),
            'use_sim_time': True
        }]
    )

    # 2. GAZEBO (Cargando tu mundo personalizado)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': f'{world_file} -r -v 3'
        }.items()
    )

    # 3. SPAWNER DEL ROBOT
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-name', 'torreta_pan_tilt',
            '-topic', 'robot_description',
            '-z', '0.0' 
        ]
    )
    
    # 4. PUENTE DEL RELOJ Y CÁMARA (Mapeado al nombre de la cámara real)
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            # Cambiamos el destino en ROS a /camera_mipi1/image_raw
            '/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image'
        ],
        remappings=[
            ('/camera/image_raw', '/camera_mipi1/image_raw')
        ],
        output='screen'
    )

    # 5. CONTROLADORES
    load_joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )

    load_pan_tilt_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["pan_tilt_controller", "--controller-manager", "/controller_manager"],
    )
    
    # 7. PUENTE HACIA EL ARDUINO NANO
    arduino_bridge_node = Node(
        package='turret_pkg',
        executable='arduino_bridge',
        name='arduino_bridge',
        output='screen',
        parameters=[{'port': '/dev/ttyUSB0', 'baudrate': 115200}]
    )

    # =========================================================================
    # EVENTOS DE CADENA (Secuencia de inicio estricta)
    # =========================================================================
    
    delay_broadcaster_after_spawn = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[load_joint_state_broadcaster],
        )
    )

    delay_controller_after_broadcaster = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=load_joint_state_broadcaster,
            on_exit=[load_pan_tilt_controller],
        )
    )

    return LaunchDescription([
        set_env_gazebo_model,
        robot_state_publisher,
        gazebo,
        spawn_entity,
        clock_bridge,
        #delay_broadcaster_after_spawn, # <-- Descomentar para control con ros
        #delay_controller_after_broadcaster # <-- Descomentar para control con ros
    ])
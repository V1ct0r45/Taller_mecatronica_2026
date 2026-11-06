import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, AppendEnvironmentVariable, TimerAction
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
    
    # 1. ROBOT STATE PUBLISHER (Sincronizado al reloj de Gazebo)
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

    # 2. GAZEBO (Con argumentos modernos de Harmonic para asegurar que lance el GUI)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': 'empty.sdf -r -v 3'
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
    
    # 4. PUENTE DEL RELOJ 
    # (Para Harmonic, es fundamental que el bridge lea el tópico de simulación y lo pase a ROS 2)
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image'
        ],
        output='screen'
    )

# 5. CONTROLADOR DE ESTADOS
    load_joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )
    delay_broadcaster = TimerAction(period=15.0, actions=[load_joint_state_broadcaster])

    # 6. CONTROLADOR DE MOTORES
    load_pan_tilt_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["pan_tilt_controller", "--controller-manager", "/controller_manager"],
    )
    delay_controller = TimerAction(period=18.0, actions=[load_pan_tilt_controller])

    return LaunchDescription([
        set_env_gazebo_model,
        robot_state_publisher,
        gazebo,
        spawn_entity,
        clock_bridge,
        delay_broadcaster,
        delay_controller
    ])
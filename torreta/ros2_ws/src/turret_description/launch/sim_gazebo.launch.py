import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, AppendEnvironmentVariable
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
    
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(Command(['xacro ', xacro_file]), value_type=str)
        }]
    )

    # Regresamos al mundo vacío nativo de Gazebo (Estabilidad total)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': '-r empty.sdf'}.items()
    )

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

    return LaunchDescription([
        set_env_gazebo_model,
        robot_state_publisher,
        gazebo,
        spawn_entity
    ])
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from webots_ros2_driver.webots_controller import WebotsController
from webots_ros2_driver.webots_launcher import WebotsLauncher
from webots_ros2_driver.wait_for_controller_connection import WaitForControllerConnection


def generate_launch_description():
    package = get_package_share_directory('practice04_localization')
    turtlebot = get_package_share_directory('webots_ros2_turtlebot')
    arguments = [
        DeclareLaunchArgument('localization_mode', default_value='global', choices=['global', 'initial']),
        DeclareLaunchArgument('error_x', default_value='0.1'),
        DeclareLaunchArgument('error_y', default_value='-0.1'),
        DeclareLaunchArgument('error_yaw', default_value='0.2'),
        DeclareLaunchArgument('min_particles', default_value='500'),
        DeclareLaunchArgument('max_particles', default_value='1000'),
        DeclareLaunchArgument('duration', default_value='240.0'),
        DeclareLaunchArgument('position_threshold', default_value='0.15'),
        DeclareLaunchArgument('angle_threshold', default_value='0.15'),
        DeclareLaunchArgument('confirmation_time', default_value='10.0'),
        DeclareLaunchArgument('results_dir', default_value=os.path.join(os.getcwd(), 'results')),
        DeclareLaunchArgument('run_name', default_value='global_low'),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('mode', default_value='realtime'),
    ]
    particle_parameters = {
        'min_particles': ParameterValue(LaunchConfiguration('min_particles'), value_type=int),
        'max_particles': ParameterValue(LaunchConfiguration('max_particles'), value_type=int),
    }
    experiment_parameters = {'use_sim_time': True}
    for name in ['localization_mode', 'results_dir', 'run_name']:
        experiment_parameters[name] = ParameterValue(LaunchConfiguration(name), value_type=str)
    for name in ['error_x', 'error_y', 'error_yaw', 'duration', 'position_threshold', 'angle_threshold', 'confirmation_time']:
        experiment_parameters[name] = ParameterValue(LaunchConfiguration(name), value_type=float)
    experiment_parameters.update(particle_parameters)
    webots = WebotsLauncher(
        world=os.path.join(package, 'worlds', 'digits_10.wbt'),
        gui=LaunchConfiguration('gui'),
        mode=LaunchConfiguration('mode'),
        ros2_supervisor=False,
    )
    state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'use_sim_time': True,
            'robot_description': '<robot name="turtlebot"><link name="base_link"/></robot>',
        }],
        output='screen',
    )
    supervisor = WebotsController(
        robot_name='ground_truth_supervisor',
        parameters=[{
            'robot_description': os.path.join(package, 'urdf', 'ground_truth_supervisor.urdf'),
            'use_sim_time': True,
        }],
    )
    driver = WebotsController(
        robot_name='TurtleBot3Burger',
        parameters=[
            {
                'robot_description': os.path.join(turtlebot, 'resource', 'turtlebot_webots.urdf'),
                'use_sim_time': True,
                'set_robot_state_publisher': True,
            },
            os.path.join(turtlebot, 'resource', 'ros2control.yml'),
        ],
        remappings=[
            ('/diffdrive_controller/cmd_vel', '/cmd_vel'),
            ('/diffdrive_controller/odom', '/odom'),
        ],
    )
    controllers = [
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=[
                'diffdrive_controller', '--controller-manager-timeout', '50',
                '--controller-ros-args=-p diffdrive_controller:wheel_separation_multiplier:=1.1',
            ],
            output='screen',
        ),
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster', '--controller-manager-timeout', '50'],
            output='screen',
        ),
    ]
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        parameters=[{
            'use_sim_time': True,
            'yaml_filename': os.path.join(package, 'maps', 'digits_10.yaml'),
        }],
        output='screen',
    )
    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        parameters=[
            os.path.join(package, 'config', 'amcl.yaml'),
            {'use_sim_time': True},
            particle_parameters,
        ],
        output='screen',
    )
    lifecycle = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        parameters=[{
            'use_sim_time': True,
            'autostart': True,
            'node_names': ['map_server', 'amcl'],
        }],
        output='screen',
    )
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', os.path.join(package, 'rviz', 'config.rviz')],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('use_rviz')),
        output='screen',
    )
    experiment = Node(
        package='practice04_localization',
        executable='experiment',
        parameters=[experiment_parameters],
        output='screen',
    )
    return LaunchDescription(arguments + [
        RegisterEventHandler(OnProcessExit(
            target_action=experiment,
            on_exit=[EmitEvent(event=Shutdown(reason='Experiment finished'))],
        )),
        RegisterEventHandler(OnProcessExit(
            target_action=webots,
            on_exit=[EmitEvent(event=Shutdown(reason='Webots closed'))],
        )),
        webots, state_publisher, supervisor, driver,
        WaitForControllerConnection(target_driver=driver, nodes_to_start=controllers),
        map_server, amcl, lifecycle, rviz, experiment,
    ])

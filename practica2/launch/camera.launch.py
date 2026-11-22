"""
Launch de la cámara: publica las imágenes con usb_cam y las muestra.

Arranca el driver usb_cam con los parámetros de config/usb_cam_params.yaml y
un visor rqt_image_view suscrito a la imagen. El driver publica sus topics con
nombres relativos (image_raw, camera_info), así que al meterlo en el espacio de
nombres CAMERA_NAMESPACE quedan en /usb_cam/image_raw y /usb_cam/camera_info.

Uso:
    ros2 launch practica2 camera.launch.py video_device:=/dev/video0
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


PACKAGE_NAME = 'practica2'
CAMERA_PARAMS_FILE = 'usb_cam_params.yaml'
CAMERA_NAMESPACE = 'usb_cam'
DEFAULT_VIDEO_DEVICE = '/dev/video0'
IMAGE_TOPIC = f'/{CAMERA_NAMESPACE}/image_raw'


def generate_launch_description() -> LaunchDescription:
    """
    Describe los nodos de la cámara y del visor.

    Returns
    -------
    LaunchDescription
        Argumento video_device, el driver usb_cam y el visor rqt_image_view.

    """
    camera_params = os.path.join(
        get_package_share_directory(PACKAGE_NAME), 'config', CAMERA_PARAMS_FILE)
    video_device = LaunchConfiguration('video_device')

    camera_node = Node(
        package='usb_cam',
        executable='usb_cam_node_exe',
        name='usb_cam',
        namespace=CAMERA_NAMESPACE,
        output='screen',
        # El orden importa: el diccionario va después del YAML para que el
        # argumento del launch sobrescriba el dispositivo del fichero.
        parameters=[camera_params, {'video_device': video_device}],
    )

    viewer_node = Node(
        package='rqt_image_view',
        executable='rqt_image_view',
        name='image_viewer',
        output='screen',
        arguments=[IMAGE_TOPIC],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'video_device',
            default_value=DEFAULT_VIDEO_DEVICE,
            description='Dispositivo de la cámara, por ejemplo /dev/video0',
        ),
        camera_node,
        viewer_node,
    ])

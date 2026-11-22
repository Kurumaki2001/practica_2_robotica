# practica_2_robotica

Práctica 2 de Robótica y Automatización Inteligente (Máster en Computación y Sistemas Inteligentes, Universidad de Deusto): ingesta, calibración y procesamiento de imágenes con ROS 2 Jazzy.

Autores: Jon y Alvar.

## Estado

| Parte | Responsable | Estado |
|---|---|---|
| Publicador de imágenes con `usb_cam` | Jon | Hecho |
| Suscriptor que guarda 10 imágenes distintas | Jon | Hecho |
| Calibración con `camera_calibration` | Alvar | Pendiente |
| Aplicación de la calibración con OpenCV y `cv_bridge` | Alvar | Pendiente |

## Estructura del repositorio

```
practica_2_robotica/
├── README.md
├── .gitignore
└── practica2/              # Paquete ROS 2 de tipo ament_python
    ├── practica2/
    │   └── image_ingestor.py   # Suscriptor que guarda 10 imágenes distintas
    ├── launch/
    │   └── camera.launch.py    # usb_cam + visor rqt_image_view
    ├── config/
    │   └── usb_cam_params.yaml # Parámetros del driver usb_cam
    ├── package.xml
    ├── setup.py
    └── test/               # Tests de estilo (flake8, pep257, copyright)
```

## Dependencias

Dentro del contenedor del laboratorio ya están `usb_cam`, `cv_bridge`, `rqt_image_view` y OpenCV. El paquete `camera_calibration` no viene instalado:

```bash
sudo apt update && sudo apt install -y ros-jazzy-camera-calibration
```

## Compilación

```bash
cd ~/ros_workspace
colcon build --packages-select practica2
source install/setup.bash
```

## Parte 1: captura e ingesta de imágenes

### Publicar y ver la cámara

```bash
ros2 launch practica2 camera.launch.py video_device:=/dev/video0
```

Arranca el driver `usb_cam` con `config/usb_cam_params.yaml` (640×480, YUYV convertido a `rgb8`, 30 fps) y abre `rqt_image_view`. El driver va en el espacio de nombres `usb_cam`, así que publica:

| Topic | Tipo |
|---|---|
| `/usb_cam/image_raw` | `sensor_msgs/msg/Image` |
| `/usb_cam/camera_info` | `sensor_msgs/msg/CameraInfo` |

Para saber qué dispositivo es la cámara: `ls /dev/video*` (el contenedor tiene que tener acceso a `/dev`).

### Guardar 10 imágenes distintas

Con la cámara publicando, desde la raíz del repositorio:

```bash
ros2 run practica2 image_ingestor
```

El nodo convierte cada `Image` a OpenCV con `cv_bridge` y la compara en escala de grises con todas las ya guardadas: solo la guarda si la diferencia absoluta media por píxel (0-255) supera `min_difference` con cada una. Así las 10 imágenes son distintas entre sí y el ruido del sensor no basta para que dos fotogramas de una escena quieta cuenten como diferentes. Para que se llenen las 10, hay que mover la cámara o algo delante de ella. Al terminar, el nodo se cierra solo.

Las imágenes quedan en `data/images/<AAAA-MM-DD_hh-mm-ss>/image_01.png` … `image_10.png`.

| Parámetro | Por defecto | Significado |
|---|---|---|
| `image_topic` | `/usb_cam/image_raw` | Topic de entrada |
| `images_to_save` | `10` | Número de imágenes que se guardan |
| `min_difference` | `5.0` | Diferencia media mínima (0-255) con cada imagen guardada |
| `output_directory` | `data/images` | Carpeta de salida (relativa a donde se lanza) |

Ejemplo: `ros2 run practica2 image_ingestor --ros-args -p min_difference:=10.0`

Para probarlo sin cámara, se puede simular una con imágenes en movimiento:

```bash
ros2 run image_tools cam2image --ros-args -p burger_mode:=true -r image:=/usb_cam/image_raw
```

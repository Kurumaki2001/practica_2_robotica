# practica_2_robotica

Práctica 2 de Robótica y Automatización Inteligente (Máster en Computación y Sistemas Inteligentes, Universidad de Deusto): ingesta, calibración y procesamiento de imágenes con ROS 2 Jazzy.

Autores: Jon y Alvar.

## Estado

| Parte | Responsable | Estado |
|---|---|---|
| Publicador de imágenes con `usb_cam` | Jon | Pendiente |
| Suscriptor que guarda 10 imágenes distintas | Jon | Pendiente |
| Calibración con `camera_calibration` | Alvar | Pendiente |
| Aplicación de la calibración con OpenCV y `cv_bridge` | Alvar | Pendiente |

## Estructura del repositorio

```
practica_2_robotica/
├── README.md
├── .gitignore
└── practica2/              # Paquete ROS 2 de tipo ament_python
    ├── practica2/          # Código Python de los nodos
    ├── launch/             # Ficheros launch
    ├── config/             # Parámetros de la cámara y fichero de calibración
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

#!/usr/bin/python3
"""
Nodo de ROS 2 que ingiere y guarda imágenes distintas de la cámara.

Se suscribe al topic de imagen que publica usb_cam, convierte cada mensaje
sensor_msgs/Image a una imagen de OpenCV con cv_bridge y guarda en disco las
primeras N imágenes (10 por defecto) que sean diferentes entre sí.

Para decidir si una imagen es diferente se compara, en escala de grises, con
todas las que ya se han guardado: se calcula la diferencia absoluta píxel a
píxel y se hace la media, que va de 0 (imágenes idénticas) a 255. La imagen
solo se guarda si esa media supera min_difference con cada una de las
anteriores. Así no basta con el ruido del sensor (unas pocas unidades) para
que dos fotogramas de una escena quieta cuenten como distintos.

Las imágenes se guardan en PNG, que no pierde calidad, dentro de una carpeta
por ejecución: <output_directory>/<AAAA-MM-DD_hh-mm-ss>/image_01.png, etc.
Cuando ha guardado todas, el nodo termina.
"""

import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import cv2
from cv_bridge import CvBridge, CvBridgeError
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


NODE_NAME = 'image_ingestor'
DEFAULT_IMAGE_TOPIC = '/usb_cam/image_raw'
DEFAULT_IMAGES_TO_SAVE = 10
DEFAULT_MIN_DIFFERENCE = 5.0
DEFAULT_OUTPUT_DIRECTORY = 'data/images'
OPENCV_ENCODING = 'bgr8'
IMAGE_FILE_EXTENSION = '.png'
LOCAL_TIMEZONE = 'Europe/Madrid'
SESSION_DIR_FORMAT = '%Y-%m-%d_%H-%M-%S'


class ImageIngestor(Node):
    """
    Nodo que guarda las primeras imágenes diferentes entre sí que recibe.

    Guarda en memoria la versión en grises de cada imagen guardada para
    comparar con ella las siguientes. Cuando llega al número pedido, destruye
    la suscripción y avisa con is_finished() de que ha terminado.
    """

    def __init__(self) -> None:
        """Declara los parámetros, prepara la carpeta de salida y se suscribe."""
        super().__init__(NODE_NAME)

        self._image_topic: str = self.declare_parameter(
            'image_topic', DEFAULT_IMAGE_TOPIC).value
        self._images_to_save: int = self.declare_parameter(
            'images_to_save', DEFAULT_IMAGES_TO_SAVE).value
        self._min_difference: float = self.declare_parameter(
            'min_difference', DEFAULT_MIN_DIFFERENCE).value
        output_directory = Path(self.declare_parameter(
            'output_directory', DEFAULT_OUTPUT_DIRECTORY).value)

        # Una carpeta por ejecución, para no mezclar ni sobrescribir capturas.
        session_name = datetime.datetime.now(ZoneInfo(LOCAL_TIMEZONE)).strftime(
            SESSION_DIR_FORMAT)
        self._session_directory: Path = output_directory / session_name

        self._bridge = CvBridge()
        self._saved_gray_images: list[np.ndarray] = []
        self._discarded_count: int = 0

        # QoS de sensor (best effort): si se pierde un fotograma no se
        # reenvía, que para una cámara es lo deseable. Es compatible tanto con
        # publicadores best effort como reliable.
        self._subscription = self.create_subscription(
            Image, self._image_topic, self._image_callback, qos_profile_sensor_data)

        self.get_logger().info(
            f'Esperando imágenes en {self._image_topic}. Se guardarán '
            f'{self._images_to_save} imágenes distintas en {self._session_directory}')

    def is_finished(self) -> bool:
        """
        Indica si ya se han guardado todas las imágenes pedidas.

        Returns
        -------
        bool
            True cuando el número de imágenes guardadas llega a images_to_save.

        """
        return len(self._saved_gray_images) >= self._images_to_save

    def _image_callback(self, msg: Image) -> None:
        """
        Convierte la imagen recibida y la guarda si es distinta de las anteriores.

        Parameters
        ----------
        msg : Image
            Imagen publicada por la cámara.

        """
        if self.is_finished():
            return

        try:
            image = self._bridge.imgmsg_to_cv2(msg, desired_encoding=OPENCV_ENCODING)
        except CvBridgeError as error:
            self.get_logger().error(f'No se ha podido convertir la imagen: {error}')
            return

        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        difference = self._difference_to_closest_saved(gray_image)
        if difference <= self._min_difference:
            self._discarded_count += 1
            return

        self._save_image(image, gray_image, difference)
        if self.is_finished():
            self._finish()

    def _difference_to_closest_saved(self, gray_image: np.ndarray) -> float:
        """
        Calcula la diferencia con la imagen guardada que más se le parece.

        Parameters
        ----------
        gray_image : np.ndarray
            Imagen candidata en escala de grises.

        Returns
        -------
        float
            Mínimo, entre todas las imágenes guardadas, de la diferencia
            absoluta media por píxel (0-255). Infinito si aún no hay ninguna,
            para que la primera imagen siempre se guarde.

        """
        if not self._saved_gray_images:
            return float('inf')
        # cv2.mean devuelve una media por canal; en grises solo cuenta la primera.
        return min(
            cv2.mean(cv2.absdiff(gray_image, saved_image))[0]
            for saved_image in self._saved_gray_images
        )

    def _save_image(self, image: np.ndarray, gray_image: np.ndarray, difference: float) -> None:
        """
        Escribe la imagen en disco y guarda su versión en grises para comparar.

        Parameters
        ----------
        image : np.ndarray
            Imagen en color (BGR) que se escribe en disco.
        gray_image : np.ndarray
            La misma imagen en grises, que se usa en las comparaciones.
        difference : float
            Diferencia con la imagen guardada más parecida, para el log.

        """
        self._session_directory.mkdir(parents=True, exist_ok=True)
        image_number = len(self._saved_gray_images) + 1
        file_path = self._session_directory / f'image_{image_number:02d}{IMAGE_FILE_EXTENSION}'

        # cv2.imwrite no lanza excepciones: devuelve False si no puede escribir.
        if not cv2.imwrite(str(file_path), image):
            self.get_logger().error(f'No se ha podido escribir {file_path}')
            return

        self._saved_gray_images.append(gray_image)
        self.get_logger().info(
            f'Guardada {file_path.name} ({image_number}/{self._images_to_save}), '
            f'diferencia {difference:.1f}, descartadas hasta ahora {self._discarded_count}')

    def _finish(self) -> None:
        """Deja de recibir imágenes y resume el resultado en el log."""
        self.destroy_subscription(self._subscription)
        self.get_logger().info(
            f'Ingesta terminada: {self._images_to_save} imágenes en '
            f'{self._session_directory} ({self._discarded_count} descartadas por '
            f'parecerse demasiado a otra)')


def main(args: list[str] | None = None) -> None:
    """
    Arranca el nodo y lo atiende hasta que guarda todas las imágenes o se pulsa Ctrl+C.

    Parameters
    ----------
    args : list[str] | None
        Argumentos de línea de comandos para ROS. Si es None, se usan los
        del proceso.

    """
    rclpy.init(args=args)
    node = ImageIngestor()
    try:
        # spin_once en lugar de spin para poder salir en cuanto termine.
        while rclpy.ok() and not node.is_finished():
            rclpy.spin_once(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()

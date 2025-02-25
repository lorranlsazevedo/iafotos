import os
import cv2
import easyocr

# Ajuste os caminhos dos classificadores Haar
FACE_CASCADE_PATH = "models/haarcascade_frontalface_default.xml"
PLATE_CASCADE_PATH = "models/haarcascade_russian_plate_number.xml"

def blur_region(image, x, y, w, h, ksize=(25, 25)):
    """
    Aplica um blur gaussiano na região delimitada.
    :param image: imagem em formato OpenCV (BGR).
    :param x, y: coordenadas do canto superior esquerdo da bounding box.
    :param w, h: largura e altura da bounding box.
    :param ksize: tamanho do kernel para blur.
    :return: None (imagem é alterada inplace).
    """
    region = image[y:y + h, x:x + w]
    if region.size == 0:
        print(f"Região vazia detectada em x={x}, y={y}, w={w}, h={h}. Ignorando...")
        return
    blurred = cv2.GaussianBlur(region, (85, 85), 0)
    image[y:y + h, x:x + w] = blurred

def detect_faces_and_plates(img_bgr):
    """
    Detecta rostos e placas usando Haar Cascades.
    Retorna listas com bounding boxes de rostos e de placas.
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
    plate_cascade = cv2.CascadeClassifier(PLATE_CASCADE_PATH)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )

    plates = plate_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(30, 30)
    )

    return faces, plates

def detect_text(img_bgr):
    """
    Usa EasyOCR para detectar texto na imagem e retorna bounding boxes aproximadas.
    Cada bounding box será dada como [(x1, y1), (x2, y2), ...].
    Aqui simplificamos para pegar x_min, y_min, x_max, y_max.
    """
    reader = easyocr.Reader(['pt', 'en'])
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    results = reader.readtext(img_rgb)

    text_bboxes = []
    for (coords, text, conf) in results:
        x_values = [p[0] for p in coords]
        y_values = [p[1] for p in coords]
        x_min, x_max = int(min(x_values)), int(max(x_values))
        y_min, y_max = int(min(y_values)), int(max(y_values))
        text_bboxes.append((x_min, y_min, x_max - x_min, y_max - y_min))

    return text_bboxes

def resize_keep_aspect(img, desired_landscape=(640, 480), desired_portrait=(480, 640)):
    """
    Redimensiona a imagem para um dos padrões:
      - paisagem (640x480) ou
      - retrato (480x640),
    mantendo a proporção e ajustando para que pelo menos um dos lados seja exato.
    """
    h, w = img.shape[:2]

    # Se a imagem for mais larga que alta, usamos o padrão paisagem
    if w >= h:
        target_w, target_h = desired_landscape  # (640, 480)

        # Tenta fixar a largura em 640, recalculando a altura
        new_h = int(h * (target_w / w))
        if new_h > target_h:
            # Se a altura ficou maior que 480, fixamos a altura e recalculamos a largura
            new_h = target_h
            new_w = int(w * (target_h / h))
        else:
            new_w = target_w
    else:
        # Caso seja mais alto que largo, usamos o padrão retrato
        target_w, target_h = desired_portrait  # (480, 640)

        # Tenta fixar a altura em 640, recalculando a largura
        new_w = int(w * (target_h / h))
        if new_w > target_w:
            # Se a largura ficou maior que 480, fixamos a largura e recalculamos a altura
            new_w = target_w
            new_h = int(h * (target_w / w))
        else:
            new_h = target_h

    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized

def process_image(input_path, output_path):
    """
    Carrega imagem, detecta rostos, placas e textos, aplica blur e salva resultado.
    Em seguida, redimensiona para 640x480 (se horizontal) ou 480x640 (se vertical), mantendo proporção.
    """
    img_bgr = cv2.imread(input_path)
    if img_bgr is None:
        print(f"Erro ao carregar imagem: {input_path}")
        return

    # 1) Detectar rostos, placas e texto na resolução original
    faces, plates = detect_faces_and_plates(img_bgr)
    text_boxes = detect_text(img_bgr)

    # 2) Borrar regiões detectadas
    for (x, y, w, h) in faces:
        blur_region(img_bgr, x, y, w, h)
    for (x, y, w, h) in plates:
        blur_region(img_bgr, x, y, w, h)
    for (x, y, w, h) in text_boxes:
        blur_region(img_bgr, x, y, w, h)

    # 3) Redimensionar após o blur (mantendo a proporção)
    final_img = resize_keep_aspect(img_bgr)

    # 4) Salvar a imagem final
    cv2.imwrite(output_path, final_img)
    print(f"Imagem processada e salva em: {output_path}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Detecção e blur automático de rostos, placas e texto, com redimensionamento final."
    )
    parser.add_argument("--input_dir", type=str, required=True, help="Pasta com as imagens de entrada.")
    parser.add_argument("--output_dir", type=str, required=True, help="Pasta de saída para as imagens borradas.")
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    for file_name in os.listdir(input_dir):
        if file_name.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
            in_path = os.path.join(input_dir, file_name)
            out_path = os.path.join(output_dir, file_name)
            process_image(in_path, out_path)

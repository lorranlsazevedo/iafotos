import os
import sys
import cv2
import easyocr


def resource_path(relative_path):
    """
    Retorna o caminho absoluto para um recurso,
    funcionando tanto em modo desenvolvimento quanto em modo "frozen" (PyInstaller).
    """
    if hasattr(sys, 'frozen'):
        # Quando executado pelo PyInstaller, os recursos estão em sys._MEIPASS
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# Use resource_path para garantir que os arquivos sejam encontrados
FACE_CASCADE_PATH = resource_path("models/haarcascade_frontalface_default.xml")
PLATE_CASCADE_PATH = resource_path("models/haarcascade_russian_plate_number.xml")


def blur_region(image, x, y, w, h):
    region = image[y:y + h, x:x + w]
    if region.size == 0:
        print(f"Região vazia detectada em x={x}, y={y}, w={w}, h={h}. Ignorando...")
        return
    # Aplica o blur com kernel 85x85
    blurred = cv2.GaussianBlur(region, (85, 85), 0)
    image[y:y + h, x:x + w] = blurred


def detect_faces_and_plates(img_bgr):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
    plate_cascade = cv2.CascadeClassifier(PLATE_CASCADE_PATH)

    if face_cascade.empty():
        print(f"Erro: Não foi possível carregar o classificador de faces em {FACE_CASCADE_PATH}")
    if plate_cascade.empty():
        print(f"Erro: Não foi possível carregar o classificador de placas em {PLATE_CASCADE_PATH}")

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
    reader = easyocr.Reader(['pt', 'en'])
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    results = reader.readtext(img_rgb)
    boxes = []
    for (coords, text, conf) in results:
        xs = [p[0] for p in coords]
        ys = [p[1] for p in coords]
        x_min, x_max = int(min(xs)), int(max(xs))
        y_min, y_max = int(min(ys)), int(max(ys))
        boxes.append((x_min, y_min, x_max - x_min, y_max - y_min))
    return boxes


def resize_keep_aspect(img, desired_landscape=(640, 480), desired_portrait=(480, 640)):
    """
    Redimensiona a imagem para:
      - 640x480 (paisagem) se a imagem for mais larga,
      - 480x640 (retrato) se for mais alta,
    mantendo a proporção e ajustando para que pelo menos um dos lados seja exato.
    """
    h, w = img.shape[:2]
    if w >= h:
        target_w, target_h = desired_landscape
        new_h = int(h * (target_w / w))
        if new_h > target_h:
            new_h = target_h
            new_w = int(w * (target_h / h))
        else:
            new_w = target_w
    else:
        target_w, target_h = desired_portrait
        new_w = int(w * (target_h / h))
        if new_w > target_w:
            new_w = target_w
            new_h = int(h * (target_w / w))
        else:
            new_h = target_h
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized


def process_image_cv2(img_bgr):
    """
    Processa a imagem aplicando:
      1. Detecção e blur de rostos, placas e textos;
      2. Redimensionamento da imagem mantendo a proporção.
    Retorna a imagem final processada.
    """
    # Detecta as regiões
    faces, plates = detect_faces_and_plates(img_bgr)
    text_boxes = detect_text(img_bgr)
    # Aplica o blur em cada região detectada
    for (x, y, w, h) in faces:
        blur_region(img_bgr, x, y, w, h)
    for (x, y, w, h) in plates:
        blur_region(img_bgr, x, y, w, h)
    for (x, y, w, h) in text_boxes:
        blur_region(img_bgr, x, y, w, h)
    # Redimensiona a imagem final
    final_img = resize_keep_aspect(img_bgr)
    return final_img


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Detecção e blur automático de rostos, placas e textos, com redimensionamento final."
    )
    parser.add_argument("--input_dir", type=str, required=True, help="Pasta com as imagens de entrada.")
    parser.add_argument("--output_dir", type=str, required=True, help="Pasta de saída para as imagens processadas.")
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    for file_name in os.listdir(input_dir):
        if file_name.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
            in_path = os.path.join(input_dir, file_name)
            out_path = os.path.join(output_dir, file_name)
            img = cv2.imread(in_path)
            if img is None:
                print(f"Erro ao carregar imagem: {in_path}")
                continue
            final_img = process_image_cv2(img)
            cv2.imwrite(out_path, final_img)
            print(f"Imagem processada e salva em: {out_path}")

from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import cv2
import zipfile
import io
import shutil  # Para limpar pastas

from backend.detector import process_image_cv2 as process_image

app = Flask(__name__, template_folder="templates", static_folder="static")

# Define pastas para upload e processamento
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)


def clear_folder(folder):
    """Remove todos os arquivos e subpastas do diretório especificado."""
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Falha ao remover {file_path}: {e}")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    return app.send_static_file('img/favicon.ico')


@app.route("/process_edit", methods=["POST"])
def process_edit():
    """
    Etapa 1: Insere a legenda nas imagens e salva na pasta PROCESSED_FOLDER.
    Antes de iniciar, limpa as pastas de upload e processamento.
    """
    # Limpa arquivos antigos
    clear_folder(UPLOAD_FOLDER)
    clear_folder(PROCESSED_FOLDER)

    files = request.files.getlist("images")
    if not files:
        return jsonify({"error": "Nenhuma imagem recebida"}), 400

    legend = request.form.get("legend", "")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            filename = secure_filename(file.filename)
            input_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(input_path)

            # Carrega a imagem
            img = cv2.imread(input_path)
            if img is None:
                continue

            # Insere a legenda, se fornecida
            if legend:
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 1
                thickness = 2
                color = (255, 0, 0)  # azul em BGR
                cv2.putText(img, legend, (10, 30), font, font_scale, color, thickness, cv2.LINE_AA)

            # Salva a imagem editada na pasta de processamento
            output_path = os.path.join(PROCESSED_FOLDER, filename)
            cv2.imwrite(output_path, img)
            zip_file.write(output_path, arcname=filename)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='imagens_editadas.zip'
    )


@app.route("/process_blur_resize", methods=["POST"])
def process_blur_resize():
    """
    Etapa 2: Recebe imagens novas, limpa as pastas, salva os arquivos enviados,
    processa-os (aplica blur e redimensiona) e os salva na pasta PROCESSED_FOLDER.
    """
    # Limpa as pastas antes de iniciar o processamento
    clear_folder(UPLOAD_FOLDER)
    clear_folder(PROCESSED_FOLDER)

    files = request.files.getlist("images")
    if not files:
        return jsonify({"error": "Nenhuma imagem recebida"}), 400

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            filename = secure_filename(file.filename)
            input_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(input_path)

            # Carrega a imagem
            img = cv2.imread(input_path)
            if img is None:
                continue

            # Processa a imagem (aplica blur e redimensionamento)
            processed_img = process_image(img)
            output_path = os.path.join(PROCESSED_FOLDER, filename)
            cv2.imwrite(output_path, processed_img)
            zip_file.write(output_path, arcname=filename)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='imagens_borradas_redimensionadas.zip'
    )


if __name__ == "__main__":
    app.run(debug=True)

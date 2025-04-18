from flask import *
from DWT import *
from werkzeug.utils import secure_filename
import uuid, threading, base64
from dop_alg import *

app = Flask(__name__)
app.config["SECRET_KEY"] = "yandexlyceum_secret_key"


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/upload/<task_id>')
def send_output_file(task_id):
    temp_dir = os.path.join(tempfile.gettempdir(), f"upload_{task_id}")
    zip_path = os.path.join(tempfile.gettempdir(), f"{task_id}.zip")
    @after_this_request
    def cleanup(response):
        threading.Timer(5, clean, args=(zip_path, )).start()
        threading.Timer(0, clean, args=(temp_dir, )).start()
        return response
    return send_file(zip_path, as_attachment=True)


@app.route('/send_file/<ext>')
def send(ext):
    filename = f'restored.{ext}'

    @after_this_request
    def schedule_file_deletion(response):
        threading.Timer(5, clean, args=(filename,)).start()
        return response

    return send_file(filename, as_attachment=True)


@app.route('/encrypt', methods=['GET', 'POST'])
def encrypt():
    if request.method == 'POST':
        messages = []
        password = request.form.get('password')

        if not password:
            messages.append('Пароль обязателен')

        task_id = str(uuid.uuid4())
        upload_folder = os.path.join(tempfile.gettempdir(), f"upload_{task_id}")
        os.makedirs(upload_folder, exist_ok=True)

        data_file = request.files.get('data')
        if not data_file or not data_file.filename:
            messages.append('Файл с данными обязателен')

        if messages:
            shutil.rmtree(upload_folder)
            return render_template('shifr.html', message=messages)

        data_path = os.path.join(upload_folder, secure_filename(data_file.filename))
        data_file.save(data_path)

        image_ndarrays = []

        image = request.files.get('image')
        if image and image.filename:
            img_filename = secure_filename(image.filename)
            img_path = os.path.join(upload_folder, img_filename)
            image.save(img_path)
            img_np = cv2.imread(img_path)
            if img_np is not None:
                image_ndarrays.append(img_np)

        folder = request.files.getlist('files[]')
        for file in folder:
            if file and file.filename.lower().split('.')[-1] in ['png', 'jpeg', 'jpg', 'svg', 'webp', 'tif', 'tiff']:
                img_filename = secure_filename(file.filename)
                img_path = os.path.join(upload_folder, img_filename)
                file.save(img_path)
                img_np = cv2.imread(img_path)
                if img_np is not None:
                    image_ndarrays.append(img_np)

        if not image_ndarrays:
            default_image = 'кот_в_сапогах.jpg'
            if os.path.exists(default_image):
                default_np = cv2.imread(default_image)
                if default_np is not None:
                    image_ndarrays.append(default_np)

        try:
            with open(data_path, 'rb') as f:
                modified_images = steg.embed(image_ndarrays, f, password)
        except ValueError as ve:
            messages.append(f'Ошибка при внедрении: {ve}')
            return render_template('shifr.html', message=messages)
        except Exception as e:
            messages.append(f'Непредвиденная ошибка: {e}')
            return render_template('shifr.html', message=messages)

        out_paths = []
        for idx, img in enumerate(modified_images):
            out_name = f"stego_{idx}.png"
            out_path = os.path.join(upload_folder, out_name)
            cv2.imwrite(out_path, img)
            out_paths.append(out_path)

        zip_path = os.path.join(tempfile.gettempdir(), f"{task_id}.zip")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for img_path in out_paths:
                zipf.write(img_path, os.path.basename(img_path))

        return redirect(url_for('send_output_file', task_id=task_id))

    return render_template('shifr.html', message=[])



@app.route('/decrypt', methods=['GET', 'POST'])
def decrypt():
    if request.method == 'POST':
        file = request.files.get('data')
        password = request.form.get('key')

        if not file or file.filename == '':
            return render_template('deshifr.html', message=["Выберите архив с изображениями."])

        if not password:
            return render_template('deshifr.html', message=["Введите пароль."])

        try:
            images = extract_and_read_images(file)
            data, ext = steg.extract(images, password)

            filename = f'restored.{ext}'
            with open(filename, 'wb') as out:
                out.write(data)

            return redirect(url_for('send', ext=ext))

        except ValueError as ve:
            return render_template('deshifr.html', message=[f"Ошибка: {str(ve)}"])

        except Exception as e:
            return render_template('deshifr.html', message=[
                "Произошла непредвиденная ошибка при извлечении данных.",
                f"Детали: {str(e)}"
            ])

    return render_template('deshifr.html', message="")


@app.route('/api/enc', methods=['POST'])
def enc_api():
    try:
        data = request.json
        image_array = data['images']
        password = data['password']
        datta_b64 = data['datta']

        images_np = [np.array(img, dtype=np.uint8) for img in image_array]

        datta_bytes = base64.b64decode(datta_b64)
        with open('input.txt', 'wb') as f:
            f.write(datta_bytes)

        with open('input.txt', 'rb') as f:
            steg.embed(images_np, f, password)

        _, buffer = cv2.imencode('.png', images_np[0])
        result_b64 = base64.b64encode(buffer).decode('utf-8')

        return jsonify({'image': result_b64})
    except Exception as e:
        print(f"Ошибка в API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dec', methods=['POST'])
def dec_api():
    try:
        data = request.json
        image_array = data['images']
        password = data['password']

        images_np = [np.array(img, dtype=np.uint8) for img in image_array]

        res, ext = steg.extract(images_np, password)
        res_b64 = base64.b64encode(res).decode('utf-8')
        return jsonify({'data': res_b64, 'ext': ext})
    except Exception as e:
        print(f"Ошибка в API декодирования: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    steg = DWTSteganography()
    app.run(debug=True)

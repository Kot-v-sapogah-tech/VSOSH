# VSOSH
При спользовании сайтом пользователь соглашается с [пользовательским соглашением](https://github.com/Kot-v-sapogah-tech/VSOSH/blob/main/%D0%9F%D0%BE%D0%BB%D1%8C%D0%B7%D0%BE%D0%B2%D0%B0%D1%82%D0%B5%D0%BB%D1%8C%D1%81%D0%BA%D0%BE%D0%B5%20%D1%81%D0%BE%D0%B3%D0%BB%D0%B0%D1%88%D0%B5%D0%BD%D0%B8%D0%B5)
# Содержание
- [Инструкция по использованию сайта](#Инструкция-по-использованию-сайта)
- [Инструкция по использованию API](#Инструкция-по-использованию-API)

# Инструкция по использованию сайта
На главном экране пользователь может выбрать одну из основных опций: Зашифровать или Расшифровать. Первая опция позволяет спрятать данные в изображении, вторая - достать их. <br>
Для того, чтобы спрятать изображения пользователь должен выбрать в какое изображение/изображения будут внесены данные, ключ шифрования данных (реализованно автоматическое создание пароля), сами данные, которые будут спрятаны. После этого данные будут зашифрованы алгоритмом "Кузнечик" и внесены в изображения при помощи алгоритма дискретного вейвлет преобразования. На выходе пользователь получает zip архив с полученным изображением.<br>
Если пользователь хочет достать данные, он должен выбрать zip архив и ключ шифрования. На выходе пользователь получает исходные данные.
Сайт реагирует на различные ситуации, такие как невозможность спрятать данные в картинке всязи с резмером, неверный ключ шифрования (при расшифровке), недостаток каких-либо данных и дак далее.
## Рекомендации
При внедрении данных в изображение вес файла увеличится, поэтому стоит использовать большие изображения с высокой глубиной цвета, чтобы разница в  весе была не столь заметна. Вес файла должен быть меньше, чем вес изображения.
# Инструкция по использованию API
``` python
import cv2
import requests
import base64
import numpy as np

def encrypt():
    # Открываем файл
    image = cv2.imread('название_изображения.png')
    image_array = image.tolist() # необходимо перевести в массив, чтобы можно было положить в JSON

    #открываем файл с данными
    with open('название_файла.txt', 'rb') as f:
        file_binary = f.read()
        file_b64 = base64.b64encode(file_binary).decode('utf-8') #необходимо перевести из битовых строк, чтобы можно было положить в JSON

    payload = {
        'images': [image_array],
        'password': Ваш пароль,
        'datta': file_b64  
    }
    
    res = requests.post('http://127.0.0.1:5000/api/enc', json=payload).json()['image']# получение изображения в виде base64 код
    # преобразование и сохрание данных
    img_bytes = base64.b64decode(res)
    img_np = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    cv2.imwrite('stego_result.png', img)


def decrypt():
    #аналогично шифрованию
    image = cv2.imread('stego_result.png')
    image_array = image.tolist()

    payload = {
        'images': [image_array],
        'password': 'asdf'
    }

    response = requests.post('http://127.0.0.1:5000/api/dec', json=payload)
    try:
        # получение данных и их расширения
        data_b64 = response.json()['data']
        ext = response.json()['ext']

        # расшифровка данных и запись в файл 
        decoded_bytes = base64.b64decode(data_b64)
        with open('11extracted_result.' + ext, 'wb') as f:
            f.write(decoded_bytes)
    except:
        # вывод ошибки
        print(response.json()['error'])
```

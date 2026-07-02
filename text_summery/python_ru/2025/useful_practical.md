# Полезная практическая информация из текстовых файлов (2025)

## Содержание

1. [Python — советы и трюки](#python--советы-и-трюки)
2. [Python — библиотеки и инструменты](#python--библиотеки-и-инструменты)
3. [Python — задачи с собеседований](#python--задачи-с-собеседований)
4. [Docker](#docker)
5. [Linux](#linux)
6. [SQL](#sql)
7. [Машинное обучение и ИИ](#машинное-обучение-и-ии)
8. [Базы данных](#базы-данных)
9. [Безопасность и шифрование](#безопасность-и-шифрование)
10. [Полезные ссылки и курсы](#полезные-ссылки-и-курсы)

---

## Python — советы и трюки

### Словарь вместо длинного if-else

```python
# Вместо:
def get_day(num):
    if num == 1:
        return "Понедельник"
    elif num == 2:
        return "Вторник"
    # ... и так далее

# Лучше:
days = {1: "Понедельник", 2: "Вторник", 3: "Среда"}
result = days.get(num, "Неизвестный день")
```

### Безопасное извлечение из вложенных словарей

```python
from functools import reduce

def deep_get(dictionary, keys, default=None):
    return reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys, dictionary)

data = {"user": {"profile": {"email": "test@example.com"}}}
email = deep_get(data, ["user", "profile", "email"])
```

### Перехват stdout через контекстный менеджер

```python
from contextlib import contextmanager
import sys
import io

@contextmanager
def capture_stdout():
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        yield buffer
    finally:
        sys.stdout = old_stdout

with capture_stdout() as out:
    print("Это вывод, который перехвачен")

captured_output = out.getvalue()
```

### "".join() вместо конкатенации строк

```python
# Плохо (медленно на больших данных):
result = ""
for w in words:
    result += w + " "

# Хорошо (быстро и питонично):
result = " ".join(words)
```

### Динамическое добавление методов в класс (monkey patching)

```python
class User:
    def __init__(self, name):
        self.name = name

def greet(self):
    return f"Hello, {self.name}!"

User.greet = greet
u = User("Alice")
print(u.greet())  # Hello, Alice!
```

### Динамическое создание классов через type()

```python
MyDynamicClass = type(
    "MyDynamicClass",
    (object,),
    {
        "x": 10,
        "hello": lambda self: f"Hello, x = {self.x}"
    }
)

obj = MyDynamicClass()
print(obj.hello())  # Hello, x = 10
```

### Генерация QR-кодов

```python
import qrcode

qr = qrcode.make("https://example.com/")
qr.save("qr_code.png")
```

### Fuzzy-поиск с difflib

```python
from difflib import SequenceMatcher

def fuzzy_match(query, products, threshold=0.6):
    matches = []
    for product in products:
        ratio = SequenceMatcher(None, query.lower(), product.lower()).ratio()
        if ratio >= threshold:
            matches.append((product, f"{ratio:.2f}"))
    return matches
```

### Быстрый парсинг HTML через selectolax

```python
from selectolax.parser import HTMLParser

html = "<html><body><h1>Hello</h1><p class='msg'>World</p></body></html>"
tree = HTMLParser(html)
print(tree.css_first("h1").text())   # Hello
print(tree.css_first("p.msg").text())  # World
```

### Ленивая загрузка больших JSON с ijson

```python
import ijson

with open('huge.json', 'rb') as f:
    for obj in ijson.items(f, 'item'):
        process(obj)  # Обработка на лету без загрузки всего файла в память
```

### Контекстные менеджеры для управления ресурсами

```python
from contextlib import contextmanager

@contextmanager
def open_file(filename):
    try:
        f = open(filename, 'r')
        yield f
    finally:
        f.close()

with open_file('example.txt') as file:
    data = file.read()
```

### Загрузка файлов по SSH (paramiko)

```python
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("your-server.com", port=22, username="user", password="pass")

sftp = ssh.open_sftp()
sftp.put("local_file.txt", "/remote/path/file.txt")
sftp.close()
ssh.close()
```

### Анализ CSV-данных ( замена Excel)

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("sales.csv", parse_dates=["date"])
print("Выручка:", df["revenue"].sum())
print(df.groupby("product")["revenue"].sum().sort_values(ascending=False).head(5))

daily = df.groupby(df["date"].dt.date)["revenue"].sum()
daily.plot(title="Выручка по дням")
plt.tight_layout(); plt.show()
```

### Отладка: f"{var=}"

```python
user = "Santa"
count = 3
items = ["cookie", "gift", "star"]

print(f"{user=}")     # user='Santa'
print(f"{count=}")    # count=3
print(f"{items=}")    # items=['cookie', 'gift', 'star']
```

### Оптимизация TCP-отправки (Python)

```python
import os
import socket
from contextlib import contextmanager

HAS_MSG_MORE = hasattr(socket, "MSG_MORE")

def send_with_coalescing(sock: socket.socket, parts: list[bytes]):
    if HAS_MSG_MORE:
        for chunk in parts[:-1]:
            sock.sendall(chunk, socket.MSG_MORE)
        sock.sendall(parts[-1])
    else:
        sock.sendall(b"".join(parts))
```

---

## Python — библиотеки и инструменты

### Профилирование Python-кода

| Инструмент | Что профилирует | Подходит для |
|-----------|----------------|-------------|
| `cProfile` | Время (встроенно) | Быстрый старт, базовый анализ |
| `py-spy` | Время (sampling) | Прод, чужие процессы, flame graphs |
| `Scalene` | Время + память + аллокации | Глубокий анализ по строкам |
| `memory_profiler` | Только память | Data science, отладка RAM |

```bash
# cProfile
python -m cProfile your_script.py

# py-spy
py-spy top --pid <PID>
py-spy record -o profile.svg -- python your_script.py

# Scalene
scalene your_script.py
```

### cuML — ускорение scikit-learn на GPU

```bash
conda install -c rapidsai -c conda-forge -c nvidia cuml rapids-build-backend
```

```python
import cuml.patch
cuml.patch.apply()

# Дальше используйте sklearn как обычно — автоматическое ускорение на GPU
```

### Podcastfy — текст в аудио-подкаст

```bash
pip install podcastfy
```

### LLM-Reasoner — пошаговые рассуждения

```bash
pip install llm-reasoner
```

```python
from llm_reasoner import ReasonChain
import asyncio

async def main():
    chain = ReasonChain(model="gpt-4", min_steps=3, temperature=0.2, timeout=30.0)
    async for step in chain.generate_with_metadata("Why is the sky blue?"):
        print(f"Step {step.number}: {step.title}")
        print(f"Confidence: {step.confidence:.2f}")
        print(step.content)

asyncio.run(main())
```

### MarkItDown — конвертация файлов в Markdown

```python
# Поддерживаемые форматы: PDF, PowerPoint, Word, Excel, изображения (OCR), аудио, HTML, CSV, JSON, XML
```

### Beam — serverless деплой AI-задач

```bash
uv add beam
```

### selectolax — быстрый HTML-парсер

```bash
pip install selectolax
```

### ijson — потоковый парсинг JSON

```bash
pip install ijson
```

### Qwen-ASR Toolkit — транскрипция аудио

```bash
pip install qwen3-asr-toolkit
```

---

## Python — задачи с собеседований

### Задача 1: Ловушка замыканий

```python
def create_funcs():
    funcs = []
    for i in range(3):
        def f():
            return i
        funcs.append(f)
    return funcs

for func in create_funcs():
    print(func())
# Вывод: 2 2 2 (не 0 1 2!)
# Решение: def f(i=i): return i
```

### Задача 2: Изменяемый аргумент по умолчанию

```python
def append_item(item, lst=[]):
    lst.append(item)
    return lst

result1 = append_item(1)  # [1]
result2 = append_item(2)  # [1, 2]  — неожиданно!
result3 = append_item(3)  # [1, 2, 3]

# Правильно:
def append_item(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst
```

### Задача 3: Список-призрак (matrix)

```python
matrix = [[0] * 3] * 3
matrix[0][0] = 1
# Вывод: [1, 0, 0] для всех строк — все строки ссылаются на один список!

# Правильно:
matrix = [[0] * 3 for _ in range(3)]
```

### Задача 4: Кэширование int в Python

```python
a = 256
b = 256
c = 257
d = 257

print(a is b)  # True  (int от -5 до 256 кэшируются)
print(c is d)  # False (257 не кэшируется)
print(True + True + True == 3)  # True
print(True is 1)   # False (разные типы)
print(False == 0)  # True
print(False is 0)  # False
```

### Задача 5: Поведение списков и кортежей с +=

```python
# Списки:
a = [1, 2, 3]
b = a
a += [4, 5]
print(a)  # [1, 2, 3, 4, 5]
print(b)  # [1, 2, 3, 4, 5] — мутирует на месте!

# Кортежи:
a = (1, 2, 3)
b = a
a += (4, 5)
print(a)  # (1, 2, 3, 4, 5)
print(b)  # (1, 2, 3) — создаёт новый объект!
```

### Задача 6: defaultdict с изменяемым значением

```python
from collections import defaultdict

def make_dict():
    return {"count": 0}

d = defaultdict(make_dict)
d["a"]["count"] += 1
d["b"]["count"] += 1
d["a"]["count"] += 1
print(d)  # {'a': {'count': 2}, 'b': {'count': 1}}

# Ошибка: если использовать lambda: some_shared_dict — все ключи ссылаются на один объект!
```

---

## Docker

### Команды для очистки

```bash
docker container prune          # Удалить остановленные контейнеры
docker image prune              # Удалить неиспользуемые образы
docker image prune -a           # Удалить все неиспользуемые образы
docker network prune            # Удалить неиспользуемые сети
docker volume prune             # Удалить неиспользуемые тома
docker system prune             # Комплексная очистка
docker system prune -a          # Полная очистка

# Автоматизация (cron раз в неделю):
0 * * 0 /usr/bin/docker system prune -f
```

### Основные команды

```bash
docker ps                       # Запущенные контейнеры
docker ps -a                    # Все контейнеры
docker images                   # Список образов
docker pull nginx               # Скачать образ
docker run nginx                # Запустить контейнер
docker run -d nginx             # Запустить в фоне
docker run -p 8080:80 nginx     # Проброс порта
docker exec -it <id> sh         # Зайти внутрь
docker logs <id>                # Посмотреть логи
docker stop <id>                # Остановить
docker rm <id>                  # Удалить контейнер
docker rmi <image>              # Удалить образ
docker build -t myapp .         # Собрать образ
docker compose up -d            # Поднять сервисы
docker compose down             # Остановить и удалить
```

### Dockerfile для Python

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

### Контейнеризация Python-приложений

```bash
docker build -t my-python-app .
docker run -it my-python-app
```

---

## Linux

### Поиск файлов, занимающих место

```bash
du -ahx / | sort -rh | head -n 20
```

### Найти удалённый файл, который держит процесс

```bash
lsof | grep deleted
# Пример: python3 12345 user txt REG 8,1 20480 /tmp/log.txt (deleted)
kill 12345  # Освободить диск
```

### Восстановление удалённого скрипта

```bash
lsof -c 'script.sh'           # Найти PID и FD
cat /proc/<PID>/fd/<FD>       # Прочитать содержимое
```

### Мониторинг процессов

```bash
ps aux --sort=-%mem | head        # Топ по памяти
ps -eo pid,comm,%cpu --sort=-%cpu | head  # Топ по CPU
ps -eo pid,comm,etime,lstart --sort=etime  # Аптайм процессов
ps --forest -eo pid,ppid,cmd      # Дерево процессов
ps -ef | grep python              # Поиск по ключевому слову
top -p <PID>                      # Следить за процессом
```

### Поиск IP-адресов в логах

```bash
grep -Eo '([0-9]{1,3}\.){3}[0-9]{1,3}' /var/log/nginx/access.log
# Сортировка по частоте:
grep -Eo '([0-9]{1,3}\.){3}[0-9]{1,3}' /var/log/nginx/access.log | sort | uniq -c | sort -nr | head
```

### Установка Python

```bash
# Windows
winget install Python.Python

# macOS
brew install python

# Ubuntu/Debian
sudo apt install python3 python3-pip
```

---

## SQL

### Не ломай индексы функциями

```sql
-- Плохо: индекс по email НЕ используется
SELECT * FROM users WHERE LOWER(email) = 'user@example.com';

-- Хорошо: нормализуем значение заранее
SELECT * FROM users WHERE email = 'user@example.com';

-- Или создаём функциональный индекс (PostgreSQL)
CREATE INDEX idx_users_email_lower ON users (LOWER(email));
```

### Топ-3 самых популярных товара (пример на Python)

```python
from collections import Counter

orders = [
    {"user": "alice", "items": ["apple", "banana", "apple"]},
    {"user": "bob", "items": ["banana", "orange"]},
    {"user": "carol", "items": ["banana", "apple", "orange", "banana"]},
    {"user": "dave", "items": ["apple"]},
]

all_items = []
for order in orders:
    all_items.extend(order["items"])

item_counts = Counter(all_items)
top_3 = item_counts.most_common(3)
print(top_3)  # [('banana', 4), ('apple', 4), ('orange', 2)]
```

### Лучшие базы данных и их применение

| База данных | Тип | Применение |
|------------|-----|-----------|
| PostgreSQL | Реляционная | Бизнес-приложения, аналитика, геоданные |
| SQLite | Встраиваемая | Мобильные приложения, локальное хранение, тесты |
| MySQL/MariaDB | Реляционная | Сайты, CMS, WordPress, LAMP |
| MongoDB | NoSQL документы | JSON-подобные данные, прототипы |
| Redis | Key-value | Кеширование, очереди, real-time |
| ClickHouse | Колоночная | Аналитика, логи, BI-дашборды |
| Neo4j | Графовая | Социальные графы, рекомендации |
| TimescaleDB | Time-series | Телеметрия, мониторинг, IoT |
| Cassandra | NoSQL | High-availability, терабайты данных |
| DuckDB | Аналитическая | Локальный OLAP, ML-воркфлоу |

---

## Машинное обучение и ИИ

### 5 ИИ-проектов за выходные

1. **Голосовой ассистент** — Whisper + GPT + озвучка
2. **Чат-бот для PDF** — LangChain + FAISS + OpenAI
3. **Генератор картинок** — Stable Diffusion + Gradio
4. **Подписи к фото** — BLIP + HuggingFace
5. **TL;DR бот** — BART/GPT для суммаризации текста

### Клонирование голоса (Coqui TTS)

```bash
pip install TTS soundfile torchaudio
```

```python
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

voice_sample_path = "your_voice.wav"
text = input("Введите текст на русском: ")

config = XttsConfig()
model = Xtts.init_from_config(config)
model.load_checkpoint("tts_models/multilingual/multi-dataset/xtts_v2")

speaker_embedding = model.get_speaker_embedding(voice_sample_path)
output_wav = model.tts(text, speaker_embedding=speaker_embedding)
model.save_wav(output_wav, "output_russian.wav")
```

### Телеграм-бот с ChatGPT

```python
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

OPENAI_API_KEY = "sk-..."
TELEGRAM_TOKEN = "123456789:ABC..."

client = OpenAI(api_key=OPENAI_API_KEY)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_text}]
    )
    await update.message.reply_text(response.choices[0].message.content)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
```

### Тестирование Python-кода (pytest)

```bash
# Запуск только изменённых тестов
pytest --lf
```

Комбинация: `pytest` + `fixtures` + `hypothesis` (property-based testing).

---

## Безопасность и шифрование

### AES — симметричное шифрование

```python
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

key = get_random_bytes(16)
cipher = AES.new(key, AES.MODE_CBC)

data = b"Secret message"
padded = pad(data, AES.block_size)
encrypted = cipher.encrypt(padded)

iv = cipher.iv
cipher_dec = AES.new(key, AES.MODE_CBC, iv)
decrypted = unpad(cipher_dec.decrypt(encrypted), AES.block_size)
```

### RSA — асимметричное шифрование

```python
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

ciphertext = public_key.encrypt(
    message,
    padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
)

plaintext = private_key.decrypt(
    ciphertext,
    padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
)
```

### ChaCha20-Poly1305 — поточное шифрование

```python
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import os

key = ChaCha20Poly1305.generate_key()
nonce = os.urandom(12)

chacha = ChaCha20Poly1305(key)
encrypted = chacha.encrypt(nonce, b"Secret message", None)
decrypted = chacha.decrypt(nonce, encrypted, None)
```

### Какой алгоритм выбрать

| Задача | Алгоритм |
|--------|----------|
| Шифрование файлов | AES |
| Безопасная передача ключа | RSA |
| Быстрое шифрование в сети | ChaCha20-Poly1305 |
| Цифровая подпись | RSA, ECDSA |

### Безопасный запуск чужого Python-кода (песочница)

```python
# Варианты изоляции:
# 1. Docker: docker run --rm --net=none --memory=128m
# 2. Firejail / chroot / seccomp / AppArmor
# 3. subprocess с ограничениями через resource, signal, ast

# Блокировка опасных импортов:
# - Запретить import os, subprocess, eval, exec, open, globals()
# - AST-парсер удаляет запрещённые ноды до запуска
```

---

## Полезные ссылки и курсы

### Курсы

- **Машинное обучение** — он-лайн учебник Виктора Китова (ВМК МГУ): deepmachinelearning@yandex.ru
- **Google Python Course** — https://developers.google.com/edu/python/set-up
- **Microsoft Generative AI** — https://github.com/microsoft/generative-ai-for-beginners
- **PostgreSQL для разработчиков** — Stepik курс
- **Think Python** — книга от O'Reilly (3 издание)
- **CodeEasy Python Essentials** — практический курс
- **python-course.eu** — структурированный текстовый курс

### Инструменты и проекты

- **Maigret** — OSINT: поиск профилей в 2000+ сервисах
- **Botasaurus** — web-scraping с обходом Cloudflare
- **NocoDB** — no-code база данных (Airtable-альтернатива)
- **DocuSeal** — open-source альтернатива DocuSign
- **PdfDing** — PDF-менеджер с тёмным режимом
- **Oh My Git** — игра для изучения Git
- **rendergit** — просмотр GitHub-репозиториев как HTML

### Open-source Deep Research агенты

1. DeerFlow (Bytedance)
2. Alita — самообучающийся агент
3. WebThinker — автономный веб-поиск
4. SimpleDeepSearcher (RUCAIBox)
5. AgenticSeek — приватный on-device ассистент
6. Suna — универсальный ассистент
7. DeepResearcher (GAIR-NLP)
8. Search-R1 — RL-агент
9. ReCall — RL-фреймворк для инструментов
10. OWL — мультиагентная система (CAMEL-AI)

import eventlet  # Importando o eventlet para modo assíncrono
# Habilitar o eventlet
eventlet.monkey_patch()

import yt_dlp
from flask import Flask, request, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO
import os
import threading
import time
import requests

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')  # Usando eventlet

UPLOAD_FOLDER = 'downloads'
CACHE_FOLDER = 'cache'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CACHE_FOLDER'] = CACHE_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(CACHE_FOLDER):
    os.makedirs(CACHE_FOLDER)

def baixar_arquivo(url, local_path):
    """Baixa o arquivo apenas se não existir."""
    if not os.path.exists(local_path):
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(response.content)
        else:
            print(f"Erro ao baixar {url}: {response.status_code}")

def carregar_arquivos_cache():
    """Baixa e armazena os arquivos JSON no cache, apenas se o Flask já estiver rodando."""
    arquivos = {
        "tv_player_api.json": "http://127.0.0.1:5000/static/tv-player-api.json",
        "ios_playes_api.json": "http://127.0.0.1:5000/static/ios-playes-api.json",
        "webpage.json": "http://127.0.0.1:5000/static/webpage.json",
        "tv_client_config.json": "http://127.0.0.1:5000/static/tv-client-config.json",
    }
    
    for nome_arquivo, url in arquivos.items():
        local_path = os.path.join(CACHE_FOLDER, nome_arquivo)
        baixar_arquivo(url, local_path)

def progress_hook(d):
    """Função chamada durante o download para enviar o progresso ao front-end."""
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0%').strip()
        speed = d.get('_speed_str', '0 KiB/s')
        eta = d.get('_eta_str', '0s')
        socketio.emit('progress', {'percent': percent, 'speed': speed, 'eta': eta}, namespace='/')

def baixar_playlist(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(app.config['UPLOAD_FOLDER'], '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'progress_hooks': [progress_hook],
        'ignoreerrors': True,
        'noplaylist': False,
        'extract_flat': False,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            if not info_dict:
                return "Erro: Não foi possível extrair informações da URL."
            file_name = ydl.prepare_filename(info_dict)
            file_name = os.path.basename(file_name).replace(' ', '_')
            file_name = os.path.splitext(file_name)[0] + ".mp3"
        socketio.emit('progress', {'percent': '100%', 'speed': 'Finalizado', 'eta': '0s'}, namespace='/')
        return file_name
    except Exception as e:
        return f"Erro ao processar a URL: {e}"

def excluir_arquivo(file_path, delay=999):
    threading.Timer(delay, lambda: os.remove(file_path) if os.path.exists(file_path) else None).start()

@app.route('/download/<filename>')
def download_file(filename):
    filename = filename.replace('_', ' ')
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "Arquivo não encontrado!"}), 404
    excluir_arquivo(file_path)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        if not url:
            return jsonify({"error": "Por favor, insira a URL da playlist."}), 400
        file_name = baixar_playlist(url)
        if "Erro" in file_name:
            return jsonify({"error": file_name}), 500
        return jsonify({"message": "Download concluído!", "file": file_name})
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app)  # O Passenger gerenciará isso
    carregar_arquivos_cache()  # Agora é chamado após o servidor iniciar

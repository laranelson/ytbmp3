import yt_dlp
from flask import Flask, request, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO
import os
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

UPLOAD_FOLDER = 'downloads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def progress_hook(d):
    """Função chamada durante o download para enviar o progresso ao front-end."""
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0%').strip()
        speed = d.get('_speed_str', '0 KiB/s')
        eta = d.get('_eta_str', '0s')

        # Enviar progresso ao front-end
        socketio.emit('progress', {'percent': percent, 'speed': speed, 'eta': eta}, namespace='/')
        #time.sleep(0.1)  # Força um pequeno atraso para garantir atualizações frequentes

def baixar_playlist(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(app.config['UPLOAD_FOLDER'], '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'progress_hooks': [progress_hook],  # Hook para progresso
        'ignoreerrors': True,
        'noplaylist': False,
        'extract_flat': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info_dict)
            file_name = os.path.basename(file_name).replace(' ', '_')
            file_name = os.path.splitext(file_name)[0] + ".mp3"

        socketio.emit('progress', {'percent': '100%', 'speed': 'Finalizado', 'eta': '0s'}, namespace='/')  
        return file_name
    except Exception as e:
        return f"Erro ao processar a URL: {e}"

def excluir_arquivo(file_path, delay=30):
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
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

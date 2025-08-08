import os
from flask import Flask, request, jsonify
import yt_dlp
import speech_recognition as sr
from pydub import AudioSegment

# Inicializamos la aplicación Flask
app = Flask(__name__)

def transcribir_video(url_video, chunk_length_ms=60000):
    """
    Función de transcripción adaptada para la API.
    Descarga, transcribe y devuelve el texto.
    """
    opciones_descarga = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav'}],
        'outtmpl': 'audio_temp.%(ext)s',
        'noplaylist': True,
    }

    print(f"API: Descargando audio de {url_video}...")
    try:
        with yt_dlp.YoutubeDL(opciones_descarga) as ydl:
            ydl.download([url_video])
        nombre_audio = "audio_temp.wav"
        print("API: Descarga completa.")
    except Exception as e:
        return f"Error al descargar el video: {e}"

    if not os.path.exists(nombre_audio):
        return "Error: El archivo de audio no se encontró."

    print("API: Procesando y transcribiendo...")
    audio = AudioSegment.from_wav(nombre_audio)
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
    recognizer = sr.Recognizer()
    texto_completo = ""

    for i, chunk in enumerate(chunks):
        chunk_filename = f"chunk_{i}.wav"
        chunk.export(chunk_filename, format="wav")
        try:
            with sr.AudioFile(chunk_filename) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language='es-ES')
                texto_completo += text + " "
        except Exception as e:
            print(f"API: Error en fragmento {i+1}: {e}")
            texto_completo += "[fragmento no reconocido] "
        finally:
            os.remove(chunk_filename)
    
    os.remove(nombre_audio)
    print("API: Proceso finalizado.")
    return texto_completo.strip()

# Definimos el endpoint de nuestra API
@app.route('/transcribe', methods=['POST'])
def transcribe_endpoint():
    """
    Este es el endpoint que llamaremos.
    Espera un JSON con la clave "url".
    """
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'Falta el parámetro "url" en el cuerpo de la solicitud.'}), 400

    video_url = data['url']
    print(f"API: Solicitud recibida para transcribir: {video_url}")
    
    # Advertencia: Esto puede tardar y bloquear la respuesta.
    # Para videos largos, podría dar timeout.
    transcripcion = transcribir_video(video_url)

    if "Error:" in transcripcion:
        return jsonify({'error': transcripcion}), 500
    
    return jsonify({'transcripcion': transcripcion})

if __name__ == "__main__":
    # Esto permite ejecutar la app localmente para pruebas
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
import os
from flask import Flask, request, jsonify
import yt_dlp
import speech_recognition as sr
from pydub import AudioSegment
from groq import Groq

# Inicializamos la aplicación Flask
app = Flask(__name__)

# Inicializamos el cliente de Groq
# La clave se toma automáticamente de la variable de entorno GROQ_API_KEY
try:
    groq_client = Groq()
    GROQ_API_ENABLED = True
except Exception as e:
    print(f"Advertencia: No se pudo inicializar el cliente de Groq. Causa: {e}")
    print("Las funciones de análisis y creación de guion estarán deshabilitadas.")
    GROQ_API_ENABLED = False

def analizar_texto(texto_transcrito):
    """
    Analiza el texto usando un modelo avanzado para extraer tema,
    puntos clave y público objetivo.
    """
    if not GROQ_API_ENABLED:
        return {"error": "La función de análisis no está disponible."}
    
    print("API: Analizando texto con Groq...")
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto analista de contenido. Tu tarea es analizar la siguiente transcripción y devolver un objeto JSON con tres claves: 'tema_central', 'puntos_clave' (una lista de strings), y 'publico_objetivo'."
                },
                {
                    "role": "user",
                    "content": f"Analiza el siguiente texto: \n\n{texto_transcrito}",
                }
            ],
            model="llama3-8b-8192",
            temperature=0.5,
            max_tokens=1024,
            top_p=1,
            stop=None,
            response_format={"type": "json_object"},
        )
        print("API: Análisis completado.")
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"API: Error durante el análisis con Groq: {e}")
        return {"error": f"Error en el análisis: {e}"}

def crear_guion_reel(analisis):
    """
    Crea un guion para un Reel de Instagram basado en el análisis del texto.
    """
    if not GROQ_API_ENABLED or 'error' in analisis:
        return {"error": "La función de creación de guion no está disponible."}

    print("API: Creando guion de Reel con Groq...")
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto creador de contenido para redes sociales. Tu tarea es crear un guion para un Reel de Instagram de 30 segundos basado en el análisis de un video. El guion debe ser dinámico y visual. Devuelve un objeto JSON con dos claves: 'titulo_reel' y 'guion' (una lista de strings, donde cada string es una escena con descripción visual y narración)."
                },
                {
                    "role": "user",
                    "content": f"Crea un guion de Reel basado en este análisis: \n\n{analisis}",
                }
            ],
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stop=None,
            response_format={"type": "json_object"},
        )
        print("API: Creación de guion completada.")
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"API: Error durante la creación de guion con Groq: {e}")
        return {"error": f"Error en la creación de guion: {e}"}


def transcribir_video(url_video, chunk_length_ms=60000):
    """
    Función principal que orquesta la descarga, transcripción y análisis.
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
        return {"error": f"Error al descargar el video: {e}"}

    if not os.path.exists(nombre_audio):
        return {"error": "El archivo de audio no se encontró."}

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
    print("API: Transcripción finalizada.")
    
    transcripcion = texto_completo.strip()
    
    # Llamadas a las nuevas funciones de IA
    analisis_contenido = analizar_texto(transcripcion)
    guion_reel = crear_guion_reel(analisis_contenido)

    return {
        "transcripcion": transcripcion,
        "analisis": analisis_contenido,
        "guion_reel": guion_reel
    }

@app.route('/transcribe', methods=['POST'])
def transcribe_endpoint():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'Falta el parámetro "url" en el cuerpo de la solicitud.'}), 400

    video_url = data['url']
    print(f"API: Solicitud recibida para procesar: {video_url}")
    
    resultado_completo = transcribir_video(video_url)

    if "error" in resultado_completo:
        return jsonify(resultado_completo), 500
    
    return jsonify(resultado_completo)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

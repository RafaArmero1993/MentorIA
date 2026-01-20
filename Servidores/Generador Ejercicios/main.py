#Se cargan las librerías:
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse

from pydantic import BaseModel, Field
import pandas as pd
from google import genai
import json
from pathlib import Path
from google.genai import types
import base64
import time
import qrcode
from bs4 import BeautifulSoup
from io import BytesIO
from elevenlabs.client import ElevenLabs
import random

#Se lee el fichero .env:
load_dotenv()

#Se inicializa FastAPI:
app = FastAPI(title="Mi API")

#Establecemos los parámetros de entrada a la API:
class ExercisesRequest(BaseModel):
    n_ejercicios: str = Field(..., alias="n_ejercicios")
    nivel_academico: str = Field(..., alias="nivel_academico")
    asignatura: str = Field(..., alias="asignatura")
    unidad: str = Field(..., alias="unidad")
    intereses: str = Field(..., alias="intereses")
    document_id: str = Field(..., alias="document_id")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "n_ejercicios": "10",
                    "nivel_academico": "4º ESO",
                    "asignatura": "Biología",
                    "unidad": "Animales vertebrados",
                    "intereses": "Me gusta la bici, la pesca y los videojuegos",
                    "document_id": "1234"
                }
            ]
        }
    }

#Se cargan las variables necesarias:
GOOGLE_CLOUD_GEMINI_API_KEY=os.getenv("GOOGLE_CLOUD_GEMINI_API_KEY")
ELEVENLABS_API_KEY=os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID=os.getenv("ELEVENLABS_VOICE_ID")
ELEVENLABS_MODEL_ID=os.getenv("ELEVENLABS_MODEL_ID")
AUDIOS_FOLDER_NAME=os.getenv("AUDIOS_FOLDER_NAME")
EXERCISES_FOLDER_NAME = os.getenv("EXERCISES_FOLDER_NAME")
DOCUMENTS_FOLDER_NAME = os.getenv("DOCUMENTS_FOLDER_NAME")

#Se cargan los diferentes JSON de configuración:
with open("config/html_components.json", "r", encoding="utf-8") as f:
    HTML_COMPONENTS = json.load(f)

#Hacemso lo mismo con los formatos CSS
with open("config/style.css", "r", encoding="utf-8") as f:
    CSS_RULES = f.read()
CSS_RULES = F'<style>{CSS_RULES}</style>'

#Se establece la conexión con ElevenLabs:
elevenLabclient = ElevenLabs(api_key=ELEVENLABS_API_KEY)

#Se establece la conexión con VertexAI (Google Cloud Platform):
client = genai.Client(vertexai=True,api_key=GOOGLE_CLOUD_GEMINI_API_KEY)

#Creamos una variable con el Path de la carpetya de audios:
AUDIO_DIR = Path(f"{AUDIOS_FOLDER_NAME}").resolve()

#Se realiza la llamada para descargar archivos:
@app.get("/audios/{audio_id}")
def descargar_audio(audio_id: str):
    audio_name =  f"Audio_{audio_id}.mp3"
    file_path = (AUDIO_DIR / audio_name).resolve()
    return FileResponse(
        path=str(file_path),
        media_type="application/octet-stream",
        filename=file_path.name,
    )

@app.get("/exercises/{exercise_id}",response_class=HTMLResponse)
def descargar_ejercicio(exercise_id: str):
    exercise_name =  f"Exercise_{exercise_id}.html"
    file_path = (Path(EXERCISES_FOLDER_NAME) / exercise_name)
    return file_path.read_text(encoding="utf-8")

# Se realiza la llamada principal
@app.post("/generar_ejercicios")
def generar_ejercicios(req: ExercisesRequest):
     
     #Se pasan las variables:
    N_EJERCICIOS= int(req.n_ejercicios)
    NIVEL_ACADEMICO = req.nivel_academico
    ASIGNATURA = req.asignatura
    UNIDAD = req.unidad
    INTERESES_ALUMNO = req.intereses
    DOCUMENT_ID = req.document_id

    #Cragamos el documento especificado:
    document_pdf_path = Path(f"{DOCUMENTS_FOLDER_NAME}/Documento_{DOCUMENT_ID}.pdf")
    DOCUMENT_BASE64 = base64.b64encode(document_pdf_path.read_bytes()).decode("ascii")

    #Se define la estructura que tendrá el documento de salida:
    structure = ["cabecera","unidad","capitulo"]
    for i in range(N_EJERCICIOS):
        structure += ["seccion","ejercicio","qr"]

    #Se generan los ejercicios usando inteligencia artificial :
    model = "gemini-2.5-flash"

    generate_content_config = types.GenerateContentConfig(
        temperature = 0.8,
        top_p = 0.95,
        seed = 0,
        max_output_tokens = 65535,
        safety_settings = [
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH",threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT",threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT",threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",threshold="OFF")
        ],
        response_mime_type = "application/json",
        response_schema = {"type":"OBJECT","properties":{"exercise":{"type":"STRING","description":"Enunciado del ejercicio planteado al alumno en formato HTML."}},"required":["exercise"]},
    )

    ejercicios=[]
    ejercicios_txt=[]
    for i in range (N_EJERCICIOS):

        parts=[
                types.Part.from_text(text=f"Eres un profesor en educación secundaria que está generando una batería de preguntas para sus alumnos de {NIVEL_ACADEMICO}."),
                types.Part.from_text(text=f"Esa batería de preguntas se basa en el contenido del siguiente documento PDF:"),
                types.Part.from_bytes(data=base64.b64decode(DOCUMENT_BASE64),mime_type="application/pdf")
            ]

        if len(ejercicios_txt) > 0:
            parts+=[
                    types.Part.from_text(text="Por el momento, ya has realizado los siguientes ejercicios, con lo que tenlo en mente para no repetir la temática"),
                ]
            for jdx, ejercicio in enumerate(ejercicios_txt):
                parts+=[
                        types.Part.from_text(text=f"Ejercicio #{jdx+1}: {ejercicio}"),
                    ]
        parts+=[
                types.Part.from_text(text="Genera un nuevo ejercicio para evaluar al alumno sobre algún aspecto que no hubieras preguntado todavía."),
                types.Part.from_text(text="Intenta que el ejercicio sea original y tenga en cuenta lso intereses del alumno:"),
                types.Part.from_text(text=INTERESES_ALUMNO),
                types.Part.from_text(text="Tu tarea"),
                types.Part.from_text(text="- Identifica una temática interesante en base al contenido del documento y los intereses del alumno."),
                types.Part.from_text(text="Importante"),
                types.Part.from_text(text="- El ejercicio debe ser breve con lo que EVITA SALUDARLE Y VE AL GRANO."),
                types.Part.from_text(text="- Las referencias que hagas sobre los intereses del alumno deben ser sutiles. El alumno no tiene que saber que el ejercicio ha sido hecho por y para él. Probablemente se sienta más cómodo si, por ejemplo, destacar en negrita lso términos relacionados con sus intereses."),
                types.Part.from_text(text="- Proporciona la respuesta usando HTML que únicamente utilice las etiquetas <p>, <b>, <i>, <u>, <ul>, <ol> y <li>). No incluyas ningún otro tipo de etiqueta HTML ni estilos CSS."),
        ]

        contents = [
            types.Content(
                role="user",
                parts=parts
            )
        ]

        if "3.0" in model:
            time.sleep(60)
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config
        )

        output=response.candidates[0].content.parts[0].text
        output = json.loads(output)
        exercise = output.get("exercise")
        soup = BeautifulSoup(exercise, "html.parser")
        exercise_text = soup.get_text(" ", strip=True)
        ejercicios.append(exercise)
        ejercicios_txt.append(exercise_text)
    
    #A continuación generamos unas pistas en formato audio con Gemini-2.5-Flash e ElevenLabs:
    model = "gemini-2.5-flash"
    generate_content_config = types.GenerateContentConfig(
        temperature = 1,
        top_p = 0.95,
        seed = 0,
        max_output_tokens = 65535,
        safety_settings = [
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH",threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT",threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT",threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",threshold="OFF")
        ],
        response_mime_type = "application/json",
        response_schema = {"type":"OBJECT","properties":{"hint":{"type":"STRING","description":"Pista para la resolución del ejercicio planteado al alumno."}},"required":["hint"]},
    )

    for idx, ejercicio_txt in enumerate(ejercicios_txt):
        parts=[
                types.Part.from_text(text=f"Eres Luca, una profesora en educación secundaria que está ayudando a un alumno de {NIVEL_ACADEMICO} a resolver el siguiente ejercicio."),
                types.Part.from_text(text=ejercicio_txt),
                types.Part.from_text(text=f"La respuesta a dicho ejercicio debería encontrarse en el siguiente documento PDF (contenido formativo):"),
                types.Part.from_bytes(data=base64.b64decode(DOCUMENT_BASE64),mime_type="application/pdf"),
                types.Part.from_text(text="Tu tarea"),
                types.Part.from_text(text="- Presentate al usuario como su profesora, Luca."),
                types.Part.from_text(text="- Proporciona una pista breve y concisa que ayude al alumno a resolver el ejercicio."),
                types.Part.from_text(text="Importante"),
                types.Part.from_text(text="- La pista debe hacer reflexionar al alumno hasta encontrar la respuesta por sus propios medios."),
        ]

        contents = [
            types.Content(
                role="user",
                parts=parts
            )
        ]

        if "3.0" in model:
            time.sleep(60)
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config
        )

        output=response.candidates[0].content.parts[0].text
        output = json.loads(output)
        hint = output.get("hint")
        
        audio = elevenLabclient.text_to_speech.convert(
            text=hint,
            voice_id=ELEVENLABS_VOICE_ID,
            model_id=ELEVENLABS_MODEL_ID,
            output_format="mp3_44100_128",
            language_code = "es"
        )

        audio_document = Path(f"{AUDIOS_FOLDER_NAME}/Audio_{idx+1}.mp3")
        if audio_document.exists():
                audio_document.unlink(missing_ok=True)
        with open(f"{AUDIOS_FOLDER_NAME}/Audio_{idx+1}.mp3", "wb") as f:
            if isinstance(audio, (bytes, bytearray)):
                f.write(audio)
            else:
                for chunk in audio:
                    f.write(chunk)

    #Tras esto lo que hacemos es generar el contenido html:
    html_content=f"<!doctype html><html lang=\"es\"><head>{CSS_RULES}</head><body><div class=\"dina4\">"
    exercise_component_index = 0
    for component in structure:
        if component == "cabecera":
            html_content+=HTML_COMPONENTS[component]["html"].replace("#asignatura#",ASIGNATURA).replace("#nivel_academico#",NIVEL_ACADEMICO)
        elif component == "unidad":
                html_content+=HTML_COMPONENTS[component]["html"].replace("#content#",UNIDAD)
        elif component == "capitulo":
                html_content+=HTML_COMPONENTS[component]["html"].replace("#content#","Ejercicios")
        elif component == "seccion":
                html_content+=HTML_COMPONENTS[component]["html"].replace("#content#",f"Ejercicio {exercise_component_index+1}:")
        elif component == "ejercicio":
            html_content+=HTML_COMPONENTS[component]["html"].replace("#content#",ejercicios[exercise_component_index])
            exercise_component_index+=1
        elif component == "qr":
                url = f"http://127.0.0.1:8000/{AUDIOS_FOLDER_NAME}/" + str(exercise_component_index) + ".mp3"
                qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=10,border=4,)
                qr.add_data(url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
                pixels = img.getdata()
                new_pixels = []
                for r, g, b, a in pixels:
                    if (r, g, b) == (255, 255, 255):
                        new_pixels.append((255, 255, 255, 0))
                    else:
                        new_pixels.append((r, g, b, 255))
                img.putdata(new_pixels)
                buf = BytesIO()
                img.save(buf, format="PNG")
                b64_string = base64.b64encode(buf.getvalue()).decode("utf-8")
                html_content+=HTML_COMPONENTS[component]["html"].replace("#qr_image#",b64_string)
    html_content+="</div></body></html>"
    exercise_id = random.randint(1, 10000000)
    with open(f"{EXERCISES_FOLDER_NAME}/Exercise_{exercise_id}.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    return JSONResponse(content={"exercise_id": exercise_id})




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
class ContentRequest(BaseModel):
    nivel_academico: str = Field(..., alias="nivel_academico")
    asignatura: str = Field(..., alias="asignatura")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "nivel_academico": "4º ESO",
                    "asignatura": "Biología"
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
IMAGE_PROMPTING= os.getenv("IMAGE_PROMPTING")
ADDITIONAL_SECTION_PAGES= int(os.getenv("ADDITIONAL_SECTION_PAGES"))
TEMARIO_FOLDER_NAME= os.getenv("TEMARIO_FOLDER_NAME")
TEMPLATES_FOLDER_NAME= os.getenv("TEMPLATES_FOLDER_NAME")

#Se cargan los diferentes JSON de configuración:
with open("config/html.json", "r", encoding="utf-8") as f:
    HTML_JSON = json.load(f)

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

@app.get("/documents/{document_id}",response_class=HTMLResponse)
def descargar_documento(document_id: str):
    document_name =  f"Document_{document_id}.html"
    file_path = (Path(DOCUMENTS_FOLDER_NAME) / document_name)
    return file_path.read_text(encoding="utf-8")

# Se realiza la llamada principal
@app.post("/generar_contenido")
def generar_contenido(req: ContentRequest):
     
     #Se pasan las variables:
    NIVEL_ACADEMICO = req.nivel_academico
    ASIGNATURA = req.asignatura

    #Cargamos el temario (que ahora es insertado a modo de XLSX peor a futuro tendrá que venir desde la llamada a la API):
    document_name = f"{TEMARIO_FOLDER_NAME}/Temario.xlsx"
    sheet_name="Hoja1"
    document = Path(document_name)
    if not document.exists():
        raise FileNotFoundError(f"No existe el archivo: {document.resolve()}")
    temario = pd.read_excel(document, sheet_name=sheet_name, engine="openpyxl")

    #Calculamos la extensión de las secciones mediante la IA y si no ha sido especificado por el profesor:
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
        response_schema = {"type":"OBJECT","properties":{"extension":{"type":"INTEGER","description":"Número de páginas que debe tener la sección a realizar."}},"required":["extension"]},
    )
    for idx, rowi in temario.iterrows():
    
        if pd.isna(rowi['Extensión']):

            current_content = ""
            current_content += "\t-Unidad: " + str(rowi["Unidad"])
            current_content += "\n\t\t-Capítulo: " + str(rowi["Capítulo"])
            current_content += "\n\t\t-Sección: " + str(rowi["Sección"])

            previous_extensions = ""
            for jdx, rowj in temario.iterrows():
                if jdx < idx:
                    previous_extensions += "\t-Unidad: " + str(rowj["Unidad"])
                    previous_extensions += "\n\t\t-Capítulo: " + str(rowj["Capítulo"])
                    previous_extensions += "\n\t\t-Sección: " + str(rowj["Sección"])
                    previous_extensions += "\n\t\t\t-Contenido: " + str(rowj["Contenido"])
                    previous_extensions += "\n\t\t\t-Extensión (Páginas): " + str(rowj["Extensión"])

            if previous_extensions == "":
                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=f"Eres un editor de contenido formativo para alumnos de {NIVEL_ACADEMICO}."),
                            types.Part.from_text(text="El contenido formativo se encuentra estructurado en unidades, capítulos y secciones."),
                            types.Part.from_text(text="Tu trabajo es ir sección por sección indicándoles a tus compañeros de edición el número de páginas que cada sección tendrá en base a su contenido."),
                            types.Part.from_text(text="La siguiente sobre la cual debes indicar la extensión (númeor de páginas) es la siguiente:"),
                            types.Part.from_text(text=current_content),
                            types.Part.from_text(text="La temática sobre la que tratará dicha sección es la siguiente:"),
                            types.Part.from_text(text=rowi["Contenido"]),
                            types.Part.from_text(text="Tu tarea:"),
                            types.Part.from_text(text="Determina la extensión de dicha sección (número de páginas)"),
                            types.Part.from_text(text="Importante:"),
                            types.Part.from_text(text=f"\tFormato de respuesta: Por favor, porciona solo el número de páginas que consideras debería tener dicha sección sabiendo que se trata de un documento educativo orientado a alumnos de {NIVEL_ACADEMICO} pero que a la vez debe ser académico y formal."),
                        ]
                    )
                ]
            else:
                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=f"Eres un editor de contenido formativo para alumnos de {NIVEL_ACADEMICO}."),
                            types.Part.from_text(text="El contenido formativo se encuentra estructurado en unidades, capítulos y secciones."),
                            types.Part.from_text(text="Tu trabajo es ir sección por sección indicándoles a tus compañeros de edición el número de páginas que cada sección tendrá en base a su contenido."),
                            types.Part.from_text(text="Por el momento, el contenido formativo que se ha ido redactando tiene la siguiente estructura (unidades, capítulos, sección y contenido) y extensiones (número de páginas)"),
                            types.Part.from_text(text=previous_extensions),
                            types.Part.from_text(text="La siguiente sobre la cual debes indicar la extensión (númeor de páginas) es la siguiente:"),
                            types.Part.from_text(text=current_content),
                            types.Part.from_text(text="La temática sobre la que tratará dicha sección es la siguiente:"),
                            types.Part.from_text(text=rowi["Contenido"]),
                            types.Part.from_text(text="Tu tarea:"),
                            types.Part.from_text(text="Determina la extensión de dicha sección (número de páginas)"),
                            types.Part.from_text(text="Importante:"),
                            types.Part.from_text(text=f"\tFormato de respuesta: Por favor, porciona solo el número de páginas que consideras debería tener dicha sección sabiendo que se trata de un documento educativo orientado a alumnos de {NIVEL_ACADEMICO} pero que a la vez debe ser académico y formal."),
                        ]
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
            extension = output.get("extension")
            temario.at[idx, 'Extensión'] = str(extension + ADDITIONAL_SECTION_PAGES)

    #Identificamos, la tipología de cada hoja (Inicio, Cierre, Continuación, ...):
    temario_plantillas = pd.DataFrame()
    pagina=0
    for idx, row in temario.iterrows():
        tipo_plantilla=""
        if idx == 0 or temario.iloc[idx-1]["Unidad"] != row["Unidad"]:
            for jdx in range (int(row["Extensión"])):
                pagina+=1
                if jdx == 0 and int(row["Extensión"]) == 1:
                    tipo_plantilla = 'Inicio Unidad y Cierre'
                elif jdx == 0:
                    tipo_plantilla = 'Inicio Unidad'
                elif jdx == int(row["Extensión"]) - 1:
                    tipo_plantilla = 'Cierre'
                else:
                    tipo_plantilla = 'Continuación'
                nueva_fila = {
                    "Unidad": row["Unidad"],
                    "Capítulo": row["Capítulo"],
                    "Sección": row["Sección"],
                    "Página": pagina,
                    "Página Sección": jdx + 1,
                    "Extensión Sección": int(row["Extensión"]),
                    "Tipo Plantilla": tipo_plantilla
                }
                temario_plantillas = pd.concat([temario_plantillas, pd.DataFrame([nueva_fila])], ignore_index=True)
        elif temario.iloc[idx-1]["Capítulo"] != row["Capítulo"]:
            for jdx in range (int(row["Extensión"])):
                pagina+=1
                if jdx == 0 and int(row["Extensión"]) == 1:
                    tipo_plantilla = 'Inicio Capítulo y Cierre'
                elif jdx == 0:
                    tipo_plantilla = 'Inicio Capítulo'
                elif jdx == int(row["Extensión"]) - 1:
                    tipo_plantilla = 'Cierre'
                else:
                    tipo_plantilla = 'Continuación'
                nueva_fila = {
                    "Unidad": row["Unidad"],
                    "Capítulo": row["Capítulo"],
                    "Sección": row["Sección"],
                    "Página": pagina,
                    "Página Sección": pagina,
                    "Página Sección": jdx + 1,
                    "Extensión Sección": int(row["Extensión"]),
                    "Tipo Plantilla": tipo_plantilla
                }
                temario_plantillas = pd.concat([temario_plantillas, pd.DataFrame([nueva_fila])], ignore_index=True)
        elif temario.iloc[idx-1]["Sección"] != row["Sección"]:
            for jdx in range (int(row["Extensión"])):
                pagina+=1
                if jdx == 0 and int(row["Extensión"]) == 1:
                    tipo_plantilla = 'Inicio Sección y Cierre'
                elif jdx == 0:
                    tipo_plantilla = 'Inicio Sección'
                elif jdx == int(row["Extensión"]) - 1:
                    tipo_plantilla = 'Cierre'
                else:
                    tipo_plantilla = 'Continuación'
                nueva_fila = {
                    "Unidad": row["Unidad"],
                    "Capítulo": row["Capítulo"],
                    "Sección": row["Sección"],
                    "Página": pagina,
                    "Página Sección": pagina,
                    "Página Sección": jdx + 1,
                    "Extensión Sección": int(row["Extensión"]),
                    "Tipo Plantilla": tipo_plantilla
                }
                temario_plantillas = pd.concat([temario_plantillas, pd.DataFrame([nueva_fila])], ignore_index=True)

    temario_plantillas=temario_plantillas.reset_index(drop=True)

    #A continuación se define el contenido de cada plantilla utilizando de nuevo la IA:
    model = "gemini-2.5-pro"

    tools = [
        types.Tool(google_search=types.GoogleSearch()),
    ]

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
        tools = tools,
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
        response_mime_type = "application/json",
        response_schema = {"type":"OBJECT","properties":{"content":{"type":"STRING","description":"Contenido de la página actual."}},"required":["content"]},
    )

    all_content=""
    for idx, rowi in temario.iterrows():
        unidad = rowi["Unidad"]
        capitulo = rowi["Capítulo"]
        seccion = rowi["Sección"]
        contenido = rowi["Contenido"]
        all_content+= f"\t- Unidad: {unidad}"
        all_content+= f"\n\t\t- Capitulo: {capitulo}"
        all_content+= f"\n\t\t\t- Sección: {seccion}"
        all_content+= f"\n\t\t\t\t- Contenido: {contenido}"

    temario_plantillas["Contenido"] = ""
    for idx, rowi in temario_plantillas.iterrows():
        
        old_content = ""
        for jdx, rowj in temario_plantillas.iterrows():
            if jdx < idx :
                if jdx == 0:
                    unidad = temario_plantillas.at[jdx, "Unidad"]
                    capitulo = temario_plantillas.at[jdx, "Capítulo"]
                    seccion = temario_plantillas.at[jdx, "Sección"]
                    old_content+= f"\t- Unidad: {unidad}"
                    old_content+= f"\n\t\t- Capitulo: {capitulo}"
                    old_content+= f"\n\t\t\t- Sección: {seccion}"
                else:
                    if temario_plantillas.at[jdx-1, "Unidad"] != temario_plantillas.at[jdx, "Unidad"]:
                        unidad = temario_plantillas.at[jdx, "Unidad"]
                        capitulo = temario_plantillas.at[jdx, "Capítulo"]
                        seccion = temario_plantillas.at[jdx, "Sección"]
                        old_content+= f"\t- Unidad: {unidad}"
                        old_content+= f"\n\t\t- Capitulo: {capitulo}"
                        old_content+= f"\n\t\t\t- Sección: {seccion}"
                    elif temario_plantillas.at[jdx-1, "Capítulo"] != temario_plantillas.at[jdx, "Capítulo"]:
                        capitulo = temario_plantillas.at[jdx, "Capítulo"]
                        seccion = temario_plantillas.at[jdx, "Sección"]
                        old_content+= f"\n\t\t- Capitulo: {capitulo}"
                        old_content+= f"\n\t\t\t- Sección: {seccion}"
                    elif temario_plantillas.at[jdx-1, "Sección"] != temario_plantillas.at[jdx, "Sección"]:
                        seccion = temario_plantillas.at[jdx, "Sección"]
                        old_content+= f"\n\t\t\t- Sección: {seccion}"
                pagina = temario_plantillas.at[jdx, "Página"]
                contenido = temario_plantillas.at[jdx, "Contenido"]
                old_content+= f"\n\t\t\t\t- Página: {pagina}"
                old_content+= f"\n\t\t\t\t- contenido: {contenido}"

        current_content = ""
        unidad = rowi["Unidad"]
        capitulo = rowi["Capítulo"]
        seccion = rowi["Sección"]
        pagina = rowi["Página"]
        seccion_no_pages = rowi["Extensión Sección"]
        seccion_page = rowi["Página Sección"]

        current_content+= f"\t- Unidad: {unidad}"
        current_content+= f"\n\t\t- Capitulo: {capitulo}"
        current_content+= f"\n\t\t\t- Sección: {seccion}"
        current_content+= f"\n\t\t\t\t- Página: {pagina}"

        temario_filtered = temario[(temario["Unidad"] == unidad) & (temario["Capítulo"] == capitulo) & (temario["Sección"] == seccion)]
        temario_filtered=temario_filtered.reset_index(drop=True)
        contenido = temario_filtered.at[0, "Contenido"]

        parts =[]
        parts+=[
            types.Part.from_text(text="Eres un trabajador en una editorial encargado de redactar el documento de las diferentes páginas de un documento educativo."),
            types.Part.from_text(text="Tienes que redactar un documento educativo y sabes que la estructura y contenido de todo el documento es el siguiente:"),
            types.Part.from_text(text=all_content),
        ]
        
        if old_content == "":
            parts+=[
                types.Part.from_text(text="Por el momento no has redactado ninguna página del documento educativo.")
            ]
        else:
            if old_content == "":
                parts+=[
                    types.Part.from_text(text="Por el momento, el contenido que has redactado del documento educativo es el siguiente"),
                    types.Part.from_text(text=old_content),
                ]

        parts+=[
            types.Part.from_text(text=f"Te dispones a redactar la siguiente página:"),
            types.Part.from_text(text=current_content),
            types.Part.from_text(text=f"Sabes que esa sección la componen {seccion_no_pages} páginas y la que vas a redactar es la número {seccion_page} dentor de dicha sección."),
            types.Part.from_text(text="Tu tarea:"),
            types.Part.from_text(text="\t 1. Analiza con detalle todo el contenido sobre el que tiene que tratar el documento educativo."),
            types.Part.from_text(text="\t 2. Observa todas las secciones que se han redactado hasta ahora (si aplica)."),
            types.Part.from_text(text="\t 3. Analiza el contenido de la sección que vas a redactar."),
            types.Part.from_text(text="\t 4. Redacta el contenido de la página."),
            types.Part.from_text(text="Importante:"),
            types.Part.from_text(text=f"\t El contenido educativo va destinado a alumnos de {NIVEL_ACADEMICO} con lo que el contenido que refleje debe adaptarse a dicha audiencia en cuanto a nivel de profundidad pero debe ser un texto académico, formal y en un solo bloque de información."),
            types.Part.from_text(text=f"\t Procura enlazar el contenido de una página con el de las secciones anteriores para que la narrativa tenga continuidad."),
            types.Part.from_text(text="Muy importante:"),
            types.Part.from_text(text=f"\t El contenido de cada hoja debe tener entre 1000 y 2000 palabras."),
            types.Part.from_text(text=f"\t El contenido no debe contener títulos de secciones ni subsecciones, debe ser directamente el contenido.")
        ]

        contents = [
            types.Content(
                role="user",
                parts=parts
            )
        ]

        grounded_answer = False
        while not grounded_answer:
            try:
                if "3.0" in model:
                    time.sleep(60)
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=generate_content_config
                )
                output=response.candidates[0].content.parts[0].text
                content = json.loads(output)
                content = content['content']   
                grounded_answer = True   
            except Exception as e:
                pass 
        temario_plantillas.at[idx, 'Contenido'] = str(content)

    #Se escoge la mejor plantilla para cada página (este proceso debería automatizarse y quitar la dependencia con respecto a PowerPoint):
    model = "gemini-2.5-pro"

    temario_plantillas["Diapositiva"] = ""
    for idx, rowi in temario_plantillas.iterrows():

        carpeta = Path(f"{TEMPLATES_FOLDER_NAME}/{rowi['Tipo Plantilla']}/")
        plantillas = sorted(p.name for p in carpeta.iterdir() if p.is_file() and p.suffix.lower() == ".jpg")

        parts=[]

        parts+=[
            types.Part.from_text(text="Eres un ilustrador en una editorial que tiene que escoger la plantilla adecuada para una página de un documento educativo."),
            types.Part.from_text(text="Te han dicho que el contenido de dicha página será el siguiente:"),
            types.Part.from_text(text=rowi["Contenido"]),
            types.Part.from_text(text="A continuación adjunto el listado de plantillas de entre las que puedes escoger:"),
            ]

        for plantilla in plantillas:
            fichero = Path(f"{TEMPLATES_FOLDER_NAME}/{rowi['Tipo Plantilla']}/{plantilla}")
            b64_string = base64.b64encode(fichero.read_bytes()).decode("utf-8")
            parts+=[
                types.Part.from_text(text=f"{plantilla}:"),
                types.Part.from_bytes(data=base64.b64decode(b64_string),mime_type="image/jpg")
            ]

        parts+=[
            types.Part.from_text(text="Tu tarea:"),
            types.Part.from_text(text="\t1. Debes analizar al detalle el contenido de cada plantilla sabiendo que:"),
            types.Part.from_text(text="\t\t  - El texto en color negro con el Lorem Ipsum es un texto de relleno que posteriromente será reemplazado con el contenido real de la página."),
            types.Part.from_text(text="\t\t  - El texto en color azul con el Lorem Ipsum es un texto de relleno que posteriromente será reemplazado con ejemplos relacionados al contenido de la página."),
            types.Part.from_text(text="\t\t  - El texto en color verde será posteriormente reemplazado con información sobre la sección, el capítulo, etc."),
            types.Part.from_text(text="\t\t  - Las posibles imágenes en el cuerpo principal del documento proporcionan información serán posteriormente reemplazadas pro imágenes relacionadas con el contenido explicado."),
            types.Part.from_text(text="\t 2. Debes revisar el contenido sobre el que se quiere profundizar en la página."),
            types.Part.from_text(text="\t 3. Debes identificar la plantilla que mejor se ajuste al futuro contenido de la página."),
            types.Part.from_text(text="Importante:"),
            types.Part.from_text(text=f"\t El contenido educativo va destinado a alumnos de {NIVEL_ACADEMICO}. Ten en cuenta esto a la hora de escoger la plantilla."),
            types.Part.from_text(text=f"\t Proporciona el nombre de la plantilla que mejor se ajuste."),
        ]

        contents = [
            types.Content(
                role="user",
                parts=parts
            )
        ]

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
            response_schema = {"type":"OBJECT","properties":{"template":{"type":"STRING","description":"Nombre de la plantilla que mejor se ajusta al contenido de la página.","enum": plantillas}},"required":["template"]},
        )

        if "3.0" in model:
            time.sleep(60)
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config
        )

        output=response.candidates[0].content.parts[0].text
        output = json.loads(output)
        template = output.get("template")
        temario_plantillas.at[idx, 'Diapositiva'] = str(template)

    #Se genera el contenido HTML:
    html_content=F"<!doctype html><html lang=\"es\"><head>{CSS_RULES}</head><body><div class=\"dina4\">"
    qr_count=0
    keep_content = ""
    for idx, rowi in temario_plantillas.iterrows():
        diapositiva = rowi["Diapositiva"].lower().replace("diapositiva","").replace(".jpg","")
        html_components = HTML_JSON[rowi["Tipo Plantilla"]][diapositiva]
        length=[]
        for component in html_components:
            #Lo primero que hacemos es generar el contenido en formato texto para dicha diapositiva:
            if "texto" in component:
                for text_length in HTML_COMPONENTS[component]["text_lengths"]:
                    length.append(text_length)
        #Una vez sabemos el texto, lo que hacemos es pedirle a Gemini que genere el contenido de dichos fragmentos:
        properties_schema_json={}
        required_schema_json=[]
        for jdx, text_item in enumerate(length):
            properties_schema_json[f"text{jdx+1}"] = {"type":"STRING","description":f"Contenido del bloque de texto #{jdx+1}."}
            required_schema_json.append(f"text{jdx+1}")

        model = "gemini-2.5-pro"

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
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
            response_mime_type = "application/json",
            response_schema = {"type":"OBJECT","properties":properties_schema_json,"required":required_schema_json},
        )

        parts=[
            types.Part.from_text(text=f"Eres un editor de contenido formativo para alumnos de {NIVEL_ACADEMICO}."),
            types.Part.from_text(text="Te han encomentado la tarea de redactar el contenido de una página que trata sobre lo siguiente:"),
            types.Part.from_text(text=rowi["Contenido"]),
            types.Part.from_text(text="A continuación te indico el número de bloques de texto que debes redactar y el tamaño, en caracteres, de cada uno de ellos:"),
        ]

        for jdx, len_item in enumerate(length):
            parts+=[
                types.Part.from_text(text=f"\t Bloque # {jdx+1}"),
                types.Part.from_text(text=f"\t\t Longitud aproximada:  {len_item} caracteres.")
            ]

        parts+=[
            types.Part.from_text(text="El contenido debe estar redactado en formato html puro sin reglas CSS ni estilos adicionales."),
            types.Part.from_text(text="Únicamente podrás redactar con las etiquetas HTML que te indique a continuación: <p>, <ul>, <li>, <ol>, <b>, <i>"),
            types.Part.from_text(text="Tu tarea:"),
            types.Part.from_text(text=f"Redacta el contenido de los {len(length)} bloques de texto en formato html siguiendo las instrucciones anteriormente indicadas"),
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

        text_content=[]
        for jdx, text_item in enumerate(length):
            text_content.append(output.get("text"+str(jdx+1)))

        #Lo siguiente que hacemos es redactar los ejemplos y para ello tenemos que saber lo que se ha hablado anteriormente:
        texto_component_index=0
        written_text=""
        sample_content=[]
        for component in html_components:
            if "texto" in component:
                written_text += text_content[texto_component_index]   
                keep_content += text_content[texto_component_index]
                texto_component_index+=1
            elif "ejemplo" in component:

                soup = BeautifulSoup(written_text, "html.parser")
                written_text = soup.get_text(" ", strip=True)

                model = "gemini-2.5-pro"

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
                    thinking_config=types.ThinkingConfig(thinking_budget=-1),
                    response_mime_type = "application/json",
                    response_schema = {"type":"OBJECT","properties":{"ejemplo":{"type":"STRING","description":"Ejemplo que se incluirá en el documento formativo."}},"required":["ejemplo"]},
                )

                parts=[
                    types.Part.from_text(text=f"Eres un editor de contenido formativo para alumnos de {NIVEL_ACADEMICO}."),
                    types.Part.from_text(text="Te han encomentado la tarea de redactar un ejemplo que permita a los alumnos entender los siguientes fragmentos que aparecen en el contenido formativo principal:"),
                    types.Part.from_text(text=written_text),
                    types.Part.from_text(text="El contenido debe estar redactado en formato html puro sin reglas CSS ni estilos adicionales."),
                    types.Part.from_text(text="Únicamente podrás redactar con las etiquetas HTML que te indique a continuación: <p>, <ul>, <li>, <ol>, <b>, <i>"),
                    types.Part.from_text(text="Tu tarea:"),
                    types.Part.from_text(text=f"Redacta el contenido del ejemplo en base al contenido principal deltexto en formato html siguiendo las instrucciones anteriormente indicadas")
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
                sample_content.append(output.get("ejemplo"))
                written_text+=""

            elif component == "qr":

                soup = BeautifulSoup(keep_content, "html.parser")
                keep_content = soup.get_text(" ", strip=True)

                model = "gemini-2.5-pro"

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
                    thinking_config=types.ThinkingConfig(thinking_budget=-1),
                    response_mime_type = "application/json",
                    response_schema = {"type":"OBJECT","properties":{"explicacion":{"type":"STRING","description":"Explicación del contenido del bloque formativo"}},"required":["explicacion"]},
                )

                parts=[
                    types.Part.from_text(text=f"Eres un locutor de contenido formativo para alumnos de {NIVEL_ACADEMICO} llamado Luca."),
                    types.Part.from_text(text="Te han encomentado la tarea de exlicar el siguiente fragmento de texto a un alumno para que lo comprenda:"),
                    types.Part.from_text(text=keep_content),
                    types.Part.from_text(text="Tu tarea:"),
                    types.Part.from_text(text=f"Proporciona una explicación breve pero cocisa sobre el contenido formativo anteriormente indicado para que un alumno de {NIVEL_ACADEMICO} pueda comprenderlo mejor."),
                    types.Part.from_text(text="Importante:"),
                    types.Part.from_text(text="DEBES explicar todo el contenido relevante del bloque formativo sin dejarte información."),
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
                explicacion= output.get("explicacion")

            
                audio = elevenLabclient.text_to_speech.convert(
                    text=explicacion,
                    voice_id=ELEVENLABS_VOICE_ID,
                    model_id=ELEVENLABS_MODEL_ID,
                    output_format="mp3_44100_128",
                    language_code = "es"
                )

                qr_count+=1
                audio_document = Path(f"{AUDIOS_FOLDER_NAME}/Audio_{qr_count}.mp3")
                if audio_document.exists():
                        audio_document.unlink(missing_ok=True)
                with open(f"{AUDIOS_FOLDER_NAME}/Audio_{qr_count}.mp3", "wb") as f:
                    if isinstance(audio, (bytes, bytearray)):
                        f.write(audio)
                    else:
                        for chunk in audio:
                            f.write(chunk)

                keep_content = ""


        #Por último se generarán las imágenes necesarias, y para ello:
        texto_component_index=0
        sample_component_index=0
        written_text=""
        image_content=[]
        for component in html_components:
            if "texto" in component and not "imagen" in component:
                written_text+=text_content[texto_component_index]
                texto_component_index+=1
            elif "ejemplo" in component and not "imagen" in component:
                written_text+=sample_content[sample_component_index]
                sample_component_index+=1
            elif component == "imagen_texto" or component == "texto_imagen":
                written_text=text_content[texto_component_index]
                texto_component_index+=1
            elif component == "imagen_ejemplo" or component == "ejemplo_imagen":
                written_text=sample_content[sample_component_index]
                sample_component_index+=1
            
            if "imagen" in component:

                soup = BeautifulSoup(written_text, "html.parser")
                written_text = soup.get_text(" ", strip=True)

                model = "gemini-2.5-flash-image"

                parts=[
                    types.Part.from_text(text=f"Eres un editor gráfico que elabora ilustraciones para contenido formativo para alumnos de {NIVEL_ACADEMICO}."),
                    types.Part.from_text(text="Te han encomentado la tarea de ilustrar una imagen relacionada con el siguiente bloque de texto de una unidad formativa:"),
                    types.Part.from_text(text=written_text),
                    types.Part.from_text(text="Para llevar esta tarea a cabo tomas como referencia las siguientes instrucciones gráficas:"),
                    types.Part.from_text(text=IMAGE_PROMPTING),
                ]
            
                parts+=[
                    types.Part.from_text(text="Muy importante:"),
                    types.Part.from_text(text="- El contenido de la imagen generada NO debe contener letras ni números. Si tiene un solo carácter alfanumérico."),
                    types.Part.from_text(text="Repito, NADA de letras o números en la imagen."),
                ]

                contents = [
                    types.Content(
                        role="user",
                        parts=parts
                    )
                ]

                if component == "imagen":
                    aspect_ratio = "16:9"
                else:
                    aspect_ratio = "1:1"

                generate_content_config = types.GenerateContentConfig(
                    temperature = 1,
                    top_p = 0.95,
                    max_output_tokens = 32768,
                    response_modalities = ["IMAGE"],
                    safety_settings = [
                        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH",threshold="OFF"),
                        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT",threshold="OFF"),
                        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT",threshold="OFF"),
                        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",threshold="OFF")
                    ],
                    image_config=types.ImageConfig(aspect_ratio=aspect_ratio,image_size="1K",output_mime_type="image/png",),
                )

                if "3.0" in model:
                    time.sleep(60)
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=generate_content_config
                )

                output=response.candidates[0].content.parts[0].inline_data
                b64_string = base64.b64encode(output.data).decode("ascii")
                image_content.append(b64_string)
                written_text = ""

        #Lo siguiente será transcribirlo:
        texto_component_index=0
        sample_component_index=0
        image_component_index=0
        qr_component_index=0
        for component in html_components:
            if component == "cabecera":
                html_content+=HTML_COMPONENTS[component]["html"].replace("#asignatura#",ASIGNATURA).replace("#nivel_academico#",NIVEL_ACADEMICO)
            elif component == "unidad":
                html_content+=HTML_COMPONENTS[component]["html"].replace("#content#",rowi["Unidad"])
            elif component == "capitulo":
                html_content+=HTML_COMPONENTS[component]["html"].replace("#content#",rowi["Capítulo"])
            elif component == "seccion":
                html_content+=HTML_COMPONENTS[component]["html"].replace("#content#",rowi["Sección"])
            elif component == "texto":
                html_content+=HTML_COMPONENTS[component]["html"].replace("#content#",text_content[texto_component_index])
                texto_component_index+=1
            elif component == "ejemplo":
                html_content+=HTML_COMPONENTS[component]["html"].replace("#content#",sample_content[sample_component_index])
                sample_component_index+=1
            elif component == "imagen":
                html_content+=HTML_COMPONENTS[component]["html"].replace("#base64_image#",str(image_content[image_component_index]))
                image_component_index+=1
            elif component == "imagen_texto" or component == "texto_imagen":
                html_content+=HTML_COMPONENTS[component]["html"].replace("#base64_image#",str(image_content[image_component_index])).replace("#content#",text_content[texto_component_index])
                texto_component_index+=1
                image_component_index+=1
            elif component == "imagen_ejemplo" or component == "ejemplo_imagen":
                html_content+=HTML_COMPONENTS[component]["html"].replace("#base64_image#",str(image_content[image_component_index])).replace("#content#",sample_content[sample_component_index])
                sample_component_index+=1
                image_component_index+=1
            elif component == "qr":
                qr_component_index+=1
                url = "https://127.0.0.1/audios/" + str(qr_component_index) + ".mp3"
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

    document_id = random.randint(1, 10000000)
    with open(f"{DOCUMENTS_FOLDER_NAME}/Document_{document_id}.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    return JSONResponse(content={"document_id": document_id})

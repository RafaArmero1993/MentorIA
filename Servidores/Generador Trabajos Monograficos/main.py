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
import random

#Se lee el fichero .env:
load_dotenv()

#Se inicializa FastAPI:
app = FastAPI(title="Mi API")

#Establecemos los parámetros de entrada a la API:
class WorkRequest(BaseModel):
    nivel_academico: str = Field(..., alias="nivel_academico")
    asignatura: str = Field(..., alias="asignatura")
    unidad: str = Field(..., alias="unidad")
    intereses: str = Field(..., alias="intereses")
    document_id: str = Field(..., alias="document_id")
    degree_id: str = Field(..., alias="degree_id")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "nivel_academico": "4º ESO",
                    "asignatura": "Biología",
                    "unidad": "Animales vertebrados",
                    "intereses": "Me gusta la bici, la pesca y los videojuegos",
                    "document_id": "1234",
                    "degree_id": "5678"
                }
            ]
        }
    }

#Se cargan las variables necesarias:
GOOGLE_CLOUD_GEMINI_API_KEY=os.getenv("GOOGLE_CLOUD_GEMINI_API_KEY")
WORKS_FOLDER_NAME = os.getenv("WORKS_FOLDER_NAME")
DOCUMENTS_FOLDER_NAME = os.getenv("DOCUMENTS_FOLDER_NAME")
DEGREES_FOLDER_NAME = os.getenv("DEGREES_FOLDER_NAME")

#Se cargan los diferentes JSON de configuración:
with open("config/html_components.json", "r", encoding="utf-8") as f:
    HTML_COMPONENTS = json.load(f)

#Hacemso lo mismo con los formatos CSS
with open("config/style.css", "r", encoding="utf-8") as f:
    CSS_RULES = f.read()
CSS_RULES = F'<style>{CSS_RULES}</style>'

#Se establece la conexión con VertexAI (Google Cloud Platform):
client = genai.Client(vertexai=True,api_key=GOOGLE_CLOUD_GEMINI_API_KEY)

#SDe realiza una llamada para descargar el trabajo:
@app.get("/works/{work_id}",response_class=HTMLResponse)
def descargar_trabajo(work_id: str):
    work_name =  f"Work_{work_id}.html"
    file_path = (Path(WORKS_FOLDER_NAME) / work_name)
    return file_path.read_text(encoding="utf-8")

# Se realiza la llamada principal
@app.post("/generar_trabajo")
def generar_trabajo(req: WorkRequest):
     
     #Se pasan las variables:
    NIVEL_ACADEMICO = req.nivel_academico
    ASIGNATURA = req.asignatura
    UNIDAD = req.unidad
    INTERESES_ALUMNO = req.intereses
    DOCUMENT_ID = req.document_id
    DEGREE_ID = req.degree_id

    #Cragamos el documento especificado:
    document_pdf_path = Path(f"{DOCUMENTS_FOLDER_NAME}/Documento_{DOCUMENT_ID}.pdf")
    DOCUMENT_BASE64 = base64.b64encode(document_pdf_path.read_bytes()).decode("ascii")

    #Cragamos el grado especificado:
    degree_pdf_path = Path(f"{DEGREES_FOLDER_NAME}/Grado_{DEGREE_ID}.pdf")
    DEGREE_BASE64 = base64.b64encode(degree_pdf_path.read_bytes()).decode("ascii")

    #Se define la estructura que tendrá el documento de salida:
    structure = ["cabecera","unidad","capitulo","trabajo"]

    #Se generan los trabajos usando inteligencia artificial :
    model = "gemini-2.5-pro"

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
        response_schema = {"type":"OBJECT","properties":{"trabajo":{"type":"STRING","description":"Enunciado del trabajo monográfico planteado al alumno en formato HTML."}},"required":["trabajo"]},
    )

    parts=[
            types.Part.from_text(text=f"Eres un profesor en educación secundaria que está generando un trabajo monográfico para uno de sus alumnos de {NIVEL_ACADEMICO}."),
            types.Part.from_text(text=f"Ese trabajo monográfico se basa en el contenido del siguiente documento PDF:"),
            types.Part.from_bytes(data=base64.b64decode(DOCUMENT_BASE64),mime_type="application/pdf"),
            types.Part.from_text(text="Genera el contenido del trabajo monográfico para evaluar al alumno."),
            types.Part.from_text(text="Intenta que el trabajo monográfico sea original y tenga en cuenta los intereses del alumno:"),
            types.Part.from_text(text=INTERESES_ALUMNO),
            types.Part.from_text(text="Este alumno está pensando en realizar el siguiente grado formativo una vez concluya sus estudios en educación secundaria:"),
            types.Part.from_bytes(data=base64.b64decode(DEGREE_BASE64),mime_type="application/pdf"),
            types.Part.from_text(text="Tu tarea"),
            types.Part.from_text(text="- Identifica una temática interesante en base al contenido del documento, los intereses del alumno y las salidas profesionales del grado."),
            types.Part.from_text(text="- Proporciona información sobre el objetivo del trabajo monográfico y la finalidad que se persigue con éste."),
            types.Part.from_text(text="- Establece paso a paso (en forma de lista ordenada) las tareas que el alumno debería realizar para llevar a cabo el trabajo monográfico."),
            types.Part.from_text(text="- Sabiendo que el trabajo monográfico tendrá una duración aproximada de 1 mes, establece una duración aproximada para cada una de las diferentes tareas a realizar (sabiendo que a lo sumo se espera que el alumno pueda dedicarle entre 1 y 2 horas a la semana)."),
            types.Part.from_text(text="- Por último, y muy importante, indicale la utilidad del trabajo monográfico en base a la relación que guarda con el grado que tiene pensado estudiar. Es conveniente que le indiques que lo aprendido en este trabajo le puede ayudar en su futuro profesional proporcionando ejemplos concretos."),
            types.Part.from_text(text="Importante"),
            types.Part.from_text(text="- El trabajo monográfico debe ser extenso. EVITA SALUDARLE Y VE AL GRANO."),
            types.Part.from_text(text="- Las referencias que hagas sobre los intereses del alumno deben ser sutiles. El alumno no tiene que saber que el trabajo monográfico ha sido hecho por y para él. Probablemente se sienta más cómodo si, por ejemplo, destacar en negrita los términos relacionados con sus intereses."),
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
    trabajo = output.get("trabajo")
    soup = BeautifulSoup(trabajo, "html.parser")

    #Se aplantilla el trabajo en formato HTML:
    html_content=f"<!doctype html><html lang=\"es\"><head>{CSS_RULES}</head><body><div class=\"dina4\">"
    for component in structure:
        if component == "cabecera":
            html_content+=HTML_COMPONENTS[component]["html"].replace("#asignatura#",ASIGNATURA).replace("#nivel_academico#",NIVEL_ACADEMICO)
        elif component == "unidad":
                html_content+=HTML_COMPONENTS[component]["html"].replace("#content#",UNIDAD)
        elif component == "capitulo":
                html_content+=HTML_COMPONENTS[component]["html"].replace("#content#","Trabajo Monográfico")
        elif component == "trabajo":
            html_content+=HTML_COMPONENTS[component]["html"].replace("#content#",trabajo)
    html_content+="</div></body></html>"

    work_id = random.randint(1, 10000000)
    with open(f"{WORKS_FOLDER_NAME}/Work_{work_id}.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    return JSONResponse(content={"work_id": work_id})

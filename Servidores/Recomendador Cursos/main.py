#Se cargan las librerías:
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import requests
from bs4 import BeautifulSoup
import requests
import pandas as pd
from google import genai
from google.genai import types
import googlemaps
from datetime import datetime, time
import time as time_lib
import json
import random
import base64
from pathlib import Path
from pptx import Presentation
from typing import List

#Se lee el fichero .env:
load_dotenv()

#Se inicializa FastAPI:
app = FastAPI(title="Mi API")

#Establecemos los parámetros de entrada a la API:
class DegreesRequest(BaseModel):
    tipo_grado: str = Field(..., alias="tipo_grado")
    localidad: str = Field(..., alias="localidad")
    provincia: str = Field(..., alias="provincia")
    modalidad: str = Field(..., alias="modalidad")
    turno: str = Field(..., alias="turno")
    vehiculo: str = Field(..., alias="vehiculo")
    intereses: str = Field(..., alias="intereses")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tipo_grado": "Grado Básico",
                    "localidad": "Puerto de Sagunto, Valencia/València, Comunidad Valenciana (ES)",
                    "provincia": "Valencia/València",
                    "modalidad": "Centro público",
                    "turno": "mañana",
                    "vehiculo": "driving",
                    "intereses": "Me interesan sobre todo dos cosas, aunque últimamente me cueste reconocerlo: la tecnología (el móvil, las apps, los videojuegos y editar vídeos) y las actividades prácticas donde puedo aprender haciendo y ver un resultado claro. Cuando estoy con la tecnología, por un rato se me va la cabeza de los problemas de casa y me gusta aprender por mi cuenta con tutoriales, porque ahí noto que mejoro sin que nadie me juzgue. Y cuando hago cosas prácticas —arreglar, montar, construir algo sencillo— siento control y la sensación de que valgo para algo. En el instituto he perdido la motivación porque muchas veces siento que voy tarde, que no encajo y que si lo intento voy a fallar otra vez, pero con estos dos intereses, si alguien me acompaña y me lo pone por pasos, sí puedo engancharme y volver a empezar."
                }
            ]
        }
    }

#Se cargan las variables necesarias:
GOOGLE_CLOUD_GEMINI_API_KEY=os.getenv("GOOGLE_CLOUD_GEMINI_API_KEY")
GOOGLE_CLOUD_MAPS_API_KEY=os.getenv("GOOGLE_CLOUD_MAPS_API_KEY")
FACTOR_DISTANCIA_1=int(os.getenv("FACTOR_DISTANCIA_1"))
NO_ITERACIONES_INTERESES_PERFILES = int(os.getenv("NO_ITERACIONES_INTERESES_PERFILES"))
MAX_DISTANCIA_MINUTOS = int(os.getenv("MAX_DISTANCIA_MINUTOS"))

#Se cargan lso diferentes JSON de configuración:
with open("config/ccaas.json", "r", encoding="utf-8") as f:
    CCAAS = json.load(f)

with open("config/enlaces.json", "r", encoding="utf-8") as f:
    ENLACES = json.load(f)

with open("config/provincias.json", "r", encoding="utf-8") as f:
    PROVINCIAS = json.load(f)

#Se establece la conexión con Google Maps:
gmaps = googlemaps.Client(key=GOOGLE_CLOUD_MAPS_API_KEY)

#Se establece la conexión con VertexAI (Google Cloud Platform):
client = genai.Client(vertexai=True,api_key=GOOGLE_CLOUD_GEMINI_API_KEY)

# Se realiza la llamada principal
@app.post("/salidas_profesionales")
def salidas_profesionales(req: DegreesRequest):
     
     #Se pasan las variables:
    TIPO_GRADO = req.tipo_grado 
    LOCALIDAD = req.localidad
    PROVINCIA = req.provincia
    MODALIDAD = [req.modalidad]
    TURNO = req.turno
    VEHICULO = req.vehiculo
    INTERESES = req.intereses

    #Se extrae, mediante WebScrapping, lso diferentes grados disponibles del Ministerio de Cultura (www.todofp.es):
    url = ENLACES[TIPO_GRADO]
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    #Se genera un dataframe en pandas con todo el contenido en formato tabla:
    contenedor_div = soup.find('div', {'id': 'contenedor'})
    content={}
    df = pd.DataFrame()
    if contenedor_div:
        table = contenedor_div.find('table')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if cells:
                    for cell in cells:
                        links = cell.find_all('a')
                        if links:                            
                            link_array = []
                            for link in links:
                                if link['href'].startswith('http'):
                                    link_url = link['href']
                                else:
                                    link_url = 'https://www.todofp.es' + link['href']
                                if cell.get("headers", [])[0] == "real-decreto":
                                    if link.get_text() == "":
                                        link_array.append({"BOE":link_url})
                                    else:
                                        link_array.append({link.get_text():link_url})
                                link_array.append(link_url)
                            content[cell.get("headers", [])[0]]=link_array
                if content != {}:
                    df_json = pd.json_normalize(content)
                    df = pd.concat([df.reset_index(drop=True), df_json.reset_index(drop=True)], axis=0)
    df=df.reset_index(drop=True)
    df["titulacion"] = df["titulacion"].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None)
    df["curriculo-mecd"] = df["curriculo-mecd"].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None)
    df["curriculo-ccaa"] = df["curriculo-ccaa"].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None)
    df["perfiles-profesionales"] = df["perfiles-profesionales"].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None)
    df["donde-estudiar"] = df["donde-estudiar"].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None)

    #Se expande el dataframe para obtener los centros en lso que se imparten las formaciones y se verifica si concuerdan con lso intereses del usuario:
    df_expanded=pd.DataFrame()
    for idx, row in df.iterrows():
        if len(row["donde-estudiar"])>0:
            response = requests.get(row["donde-estudiar"])
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table')
            if table:
                rows_table = table.find_all('tr')
                for row_table in rows_table:
                    cells = row_table.find_all('td')
                    if cells:
                        if cells[0].get_text(strip=True) in PROVINCIAS[PROVINCIA] and cells[5].get_text(strip=True) in MODALIDAD:
                            if cells[2].get_text() != "" and cells[3].get_text() != "":
                                centro = cells[2].get_text() + ' ' + cells[3].get_text()
                            elif cells[2].get_text() != "":
                                centro = cells[2].get_text()
                            elif cells[3].get_text() != "":
                                centro = cells[3].get_text()
                            df_json = pd.json_normalize({"real-decreto":row["real-decreto"],"curriculo-mecd":row["curriculo-mecd"],"curriculo-ccaa":row["curriculo-ccaa"],"perfiles-profesionales":row["perfiles-profesionales"], "ccaa": CCAAS[cells[0].get_text()], "provincia": cells[0].get_text(),"localidad": cells[1].get_text(),"centro": centro})
                            df_expanded = pd.concat([df_expanded.reset_index(drop=True), df_json.reset_index(drop=True)], axis=0)
    df_expanded=df_expanded.reset_index(drop=True)

    #Se filtran las localidades cercanas al usuario en base a sus medios de desplazamiento:
    llegada = datetime.now()
    if TURNO == "mañana":
        llegada = datetime.combine(llegada.date(), time(8, 0))
    elif TURNO == "tarde":
        llegada = datetime.combine(llegada.date(), time(15, 0))
    llegada = int(llegada.timestamp())

    places_tmp=[]
    places=[]
    for idx, row in df_expanded.iterrows():
        places_tmp.append(row["localidad"]+', ' + row["provincia"] +', ' + row["ccaa"] + ' (ES)')
    places_tmp=list(set(places_tmp))

    for place in places_tmp:
        try:
            distance=gmaps.distance_matrix(
                    LOCALIDAD,
                    place, 
                    mode=VEHICULO,      
                    arrival_time=llegada,
                    language='es'
                )
            distance=distance['rows'][0]['elements'][0]['duration']['value']/60
            if distance <= MAX_DISTANCIA_MINUTOS*(1+FACTOR_DISTANCIA_1/100):
                places.append(place)
        except:
            pass

    concatFields = (df_expanded["localidad"].astype(str) + ", " + df_expanded["provincia"].astype(str) + ", " + df_expanded["ccaa"].astype(str) + " (ES)")
    mask = concatFields.isin(places)
    df_filtrado = df_expanded[mask].copy() 
    df_filtrado=df_filtrado.reset_index(drop=True)

    places_tmp=[]
    places=[]
    for idx, row in df_filtrado.iterrows():
        places_tmp.append(row["centro"]+', ' +row["localidad"]+', ' + row["provincia"] +', ' + row["ccaa"] + ' (ES)')
    places_tmp=list(set(places_tmp))
    places_tmp

    for place in places_tmp:
        try:
            distance=gmaps.distance_matrix(
                    LOCALIDAD,
                    place, 
                    mode=VEHICULO,      
                    arrival_time=llegada,
                    language='es'
                )
            distance=distance['rows'][0]['elements'][0]['duration']['value']/60
            if distance <= MAX_DISTANCIA_MINUTOS:
                places.append(place)
        except:
            pass

    concatFields = (df_filtrado["centro"].astype(str) + ", " + df_filtrado["localidad"].astype(str) + ", " + df_filtrado["provincia"].astype(str) + ", " + df_filtrado["ccaa"].astype(str) + " (ES)")
    mask = concatFields.isin(places)
    df_filtrado = df_filtrado[mask].copy() 
    df_filtrado=df_filtrado.reset_index(drop=True)
    df_filtrado
  
    #Se extraen los curriculos de las comunidades autónomas:
    curriculos_ccaa=[]
    for idx, row in df_filtrado.iterrows():
        curriculos_ccaa.append(row["curriculo-ccaa"])
    curriculums_ccaa=list(set(curriculos_ccaa))
    curriculums_ccaa

    pd_curriculumns_ccaa=pd.DataFrame()
    for curriculum_ccaa in curriculums_ccaa:
        response = requests.get(curriculum_ccaa)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        elementos = soup.find_all('div', class_='elemento')    
        for elemento in elementos:
            ccaa = elemento.find('p', class_='titulo')
            if ccaa:
                bloque_enlaces = elemento.find_all('div', class_='cte') 
                if bloque_enlaces:
                    for bloque in bloque_enlaces:
                        links=[]
                        enlaces = bloque.find_all('a')
                        for enlace in enlaces:
                            href = enlace.get('href')
                            if not href.startswith('http'):
                                href = 'https://www.todofp.es' + href
                            links.append({enlace.get_text():href})
                        if links != []:
                            df_json = pd.json_normalize({"curriculo-ccaa":curriculum_ccaa, "ccaa_alt":ccaa.getText(), "links-curriculo-ccaa":links})
                            pd_curriculumns_ccaa = pd.concat([pd_curriculumns_ccaa.reset_index(drop=True), df_json.reset_index(drop=True)], axis=0)

    df_final = df_filtrado.merge(pd_curriculumns_ccaa,how="left",on="curriculo-ccaa")
    df_final = df_final[df_final["ccaa"].eq(df_final["ccaa_alt"])].copy()
    df_final = df_final.drop(columns=["ccaa", "ccaa_alt", "curriculo-ccaa","provincia"])
    df_final = df_final.rename(columns={"links-curriculo-ccaa": "curriculo-ccaa"})
    df_final=df_final.reset_index(drop=True)
    df_final

    #Se evalua el potencial interés que podría tener un curso para el usuario mediante Inteligencia Artificial:
    pd_eval = pd.DataFrame()
    for idx, row in df_final.iterrows():

        model = "gemini-2.5-flash"

        document = types.Part.from_uri(
            file_uri=row["perfiles-profesionales"],
            mime_type="application/pdf",
        )

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="Actúa como un orientador vocacional experto en formación profesional y análisis de perfiles laborales."),
                    types.Part.from_text(text="Mi perfil: Soy un estudiante con los siguientes intereses y habilidades:"),
                    types.Part.from_text(text=INTERESES),
                    types.Part.from_text(text="Tu tarea:"),
                    types.Part.from_text(text="\t 1. Accede y analiza el contenido del siguiente documento sobre las salidas profesionales de un Grado Formativo:"),
                    document,
                    types.Part.from_text(text="\t 2. Comparte una puntuación de 0 a 100 que represente el nivel de afinidad entre mis intereses y lo que este grado ofrece profesionalmente."),
                    types.Part.from_text(text="Para tu análisis, utiliza estos criterios:"),
                    types.Part.from_text(text="\t · Afinidad Directa: ¿Las tareas del trabajo coinciden con lo que me gusta hacer?"),
                    types.Part.from_text(text="\t · Proyección de Futuro: ¿Este perfil profesional me permitirá desarrollar mis intereses a largo plazo?"),
                    types.Part.from_text(text="\t · Puntos de Fricción: Identifica qué partes del perfil profesional podrían NO gustarme según mis intereses."),
                    types.Part.from_text(text="Formato de respuesta: Por favor, y muy importante, proporciona solo la puntuación (número entero del 0 a 100)."),
                ]
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
            #thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
            response_mime_type = "application/json",
            response_schema = {"type":"OBJECT","properties":{"puntuacion_afinidad":{"type":"INTEGER","description":"Un valor entero de 0 a 100 que representa el grado de coincidencia entre los intereses del usuario y los perfiles profesionales del grado."}},"required":["puntuacion_afinidad"]},
        )
        

        for iter in range(1):

            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=generate_content_config
            )

            output=response.candidates[0].content.parts[0].text
            output = json.loads(output)
            puntuacion = output.get("puntuacion_afinidad")

            df_json = pd.json_normalize({"perfiles-profesionales":row["perfiles-profesionales"], "puntuacion":puntuacion})
            pd_eval = pd.concat([pd_eval.reset_index(drop=True), df_json.reset_index(drop=True)], axis=0)
            #time_lib.sleep(60)

    pd_eval=pd_eval.reset_index(drop=True)
    pd_eval

    #Tomamos los 5 valroes con un posible mayr impacto para el usuario y volvemos a evaluarlos:
    pd_eval = pd_eval.sort_values(by='puntuacion', ascending=False).head(5)
    pd_eval2 = pd.DataFrame()
    for idx, rowi in pd_eval.iterrows():
        for jdx, rowj in pd_eval.iterrows():
            if idx > jdx:
                

                model = "gemini-2.5-flash"

                document1 = types.Part.from_uri(
                    file_uri=rowi["perfiles-profesionales"],
                    mime_type="application/pdf",
                )

                document2 = types.Part.from_uri(
                    file_uri=rowj["perfiles-profesionales"],
                    mime_type="application/pdf",
                )

                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text="Actúa como un orientador vocacional experto en formación profesional y análisis de perfiles laborales."),
                            types.Part.from_text(text="Mi perfil: Soy un estudiante con los siguientes intereses y habilidades:"),
                            types.Part.from_text(text=INTERESES),
                            types.Part.from_text(text="Tu tarea:"),
                            types.Part.from_text(text="\t 1. Accede y analiza el contenido del siguiente documento sobre las salidas profesionales de un Grado Formativo:"),
                            document1,
                            types.Part.from_text(text="\t 2. Accede y analiza el contenido del siguiente documento sobre las salidas profesionales de otro Grado Formativo:"),
                            document2,
                            types.Part.from_text(text="\t 3. Indica qué curso tiene un mayor grado de afinidad en relación a mis intereses y lo que ambos grados ofrecen profesionalmente."),
                            types.Part.from_text(text="Para tu análisis, utiliza estos criterios:"),
                            types.Part.from_text(text="\t · Afinidad Directa: ¿Las tareas del trabajo coinciden con lo que me gusta hacer?"),
                            types.Part.from_text(text="\t · Proyección de Futuro: ¿Este perfil profesional me permitirá desarrollar mis intereses a largo plazo?"),
                            types.Part.from_text(text="\t · Puntos de Fricción: Identifica qué partes del perfil profesional podrían NO gustarme según mis intereses."),
                            types.Part.from_text(text="Formato de respuesta: Por favor, y muy importante, dependiendo si el grado de mayor afinidad es el indicado en el punto 1 o en el punto 2, proporciona solo el número del grado que me puede generar un mayor interés."),
                        ]
                    )
                ]

        generate_content_config = types.GenerateContentConfig(
            temperature = 0.5,
            top_p = 0.95,
            seed = random.randint(0,100000),
            max_output_tokens = 65535,
            safety_settings = [
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH",threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT",threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT",threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",threshold="OFF")
            ],
            #thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
            response_mime_type = "application/json",
            response_schema = {"type":"OBJECT","properties":{"grado_de_mayor_interes":{"type":"INTEGER","description":"Un valor entero que admite solo los valores 1 o 2, devolviendo 1 en aquellos casos que el documento citado en el primer punto me pueda resultar más interesante o en caso contrario 2 si el documento en el segundo punto es más interesante en base a mis intereses."}},"required":["grado_de_mayor_interes"]},
        )
        

        for iter in range(NO_ITERACIONES_INTERESES_PERFILES):

            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=generate_content_config
            )

            output=response.candidates[0].content.parts[0].text
            output = json.loads(output)
            grado_de_mayor_interes = str(output.get("grado_de_mayor_interes"))

            if grado_de_mayor_interes == "1":
                df_json = pd.json_normalize({"perfiles-profesionales":rowi["perfiles-profesionales"]})
            else:
                df_json = pd.json_normalize({"perfiles-profesionales":rowj["perfiles-profesionales"]})

            pd_eval2 = pd.concat([pd_eval2.reset_index(drop=True), df_json.reset_index(drop=True)], axis=0)
            #time_lib.sleep(60)

    pd_eval2=pd_eval2.reset_index(drop=True)
    top_vals = (pd_eval2["perfiles-profesionales"].value_counts(dropna=False).head(3).index)
    df_final_applied = df_final[df_final["perfiles-profesionales"].isin(top_vals)]
    df_final_applied=df_final_applied.reset_index(drop=True)
    df_final_applied

    #Porporcionamos la respuesta:
    data = df_final_applied.to_dict(orient="records")  # [{col: val, ...}, ...]
    return JSONResponse(content={"rows": data, "n": len(data)})
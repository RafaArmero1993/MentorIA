# Generador de Ejercicios Personalizados

API desarrollada con FastAPI para generar ejercicios educativos personalizados en formato HTML. Utiliza IA (Gemini 2.5 Flash) para crear ejercicios adaptados a los intereses del alumno y genera pistas en formato audio mediante text-to-speech (ElevenLabs).

## Instalación y Ejecución

### Opción 1: Ejecutar con Docker
```bash
docker run --rm -p 8000:8000 --env-file .env generador-ejercicios:latest
```

### Opción 2: Ejecutar directamente
```bash
py -m venv .venv
.\.venv\Scripts\Activate.ps1   
pip install --no-cache-dir -r requirements.txt
pip install elevenlabs==2.31.0
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Documentación Swagger
Se pueden probar los endpoints en el Swagger: http://127.0.0.1:8000/docs

## Endpoints

### POST `/generar_ejercicios`

Genera una batería de ejercicios personalizados en formato HTML basándose en un documento PDF de referencia, el nivel académico, la asignatura y los intereses del alumno. Cada ejercicio incluye un código QR que enlaza a un audio con pistas para su resolución.

#### Parámetros de entrada

| Parámetro | Tipo | Obligatorio | Descripción |
|-----------|------|-------------|-------------|
| `n_ejercicios` | string | Sí | Número de ejercicios a generar (ej: "10") |
| `nivel_academico` | string | Sí | Nivel académico del alumno (ej: "4º ESO", "1º Bachillerato") |
| `asignatura` | string | Sí | Asignatura de los ejercicios (ej: "Biología", "Matemáticas") |
| `unidad` | string | Sí | Unidad didáctica o tema (ej: "Animales vertebrados") |
| `intereses` | string | Sí | Descripción de los intereses personales del alumno |
| `document_id` | string | Sí | ID del documento PDF de referencia ubicado en la carpeta `documents/` |

#### Ejemplo de petición

```json
{
  "n_ejercicios": "10",
  "nivel_academico": "4º ESO",
  "asignatura": "Biología",
  "unidad": "Animales vertebrados",
  "intereses": "Me gusta la bici, la pesca y los videojuegos",
  "document_id": "1234"
}
```

#### Respuesta

Devuelve un JSON con el identificador único del ejercicio generado.

**Estructura de respuesta:**

```json
{
  "exercise_id": 5252638
}
```

**Campos de la respuesta:**

| Campo | Descripción |
|-------|-------------|
| `exercise_id` | Identificador único del ejercicio generado (aleatorio entre 1-10000000) |

#### Proceso interno

1. **Carga del documento**: Lee el documento PDF especificado de la base de datos de documentos (`documents/Documento_{document_id}.pdf`)
2. **Generación de ejercicios**: Utiliza Gemini 2.5 Flash para crear ejercicios originales basados en:
   - El contenido del documento PDF
   - Los intereses del alumno (integrados de forma sutil)
   - Ejercicios previamente generados (para evitar repeticiones)
3. **Generación de pistas de audio**: Crea audios con ElevenLabs mediante:
   - Texto generado por Gemini 2.5 Flash con pistas breves para cada ejercicio
   - Voz de la profesora virtual "Luca"
   - Formato MP3 (44100 Hz, 128 kbps)
4. **Creación del HTML**: Genera un documento HTML con:
   - Estructura personalizada (cabecera, unidad, capítulo, secciones)
   - Ejercicios con formato HTML limitado (`<p>`, `<b>`, `<i>`, `<u>`, `<ul>`, `<ol>`, `<li>`)
   - Códigos QR que enlazan a los audios con pistas
   - Estilos CSS cargados desde `config/style.css`
5. **Almacenamiento**: Guarda el HTML en `exercises/Exercise_{exercise_id}.html` y los audios en `audios/Hint_{n}.mp3`

#### Códigos de respuesta

| Código | Descripción |
|--------|-------------|
| 200 | Éxito - Devuelve el ID del ejercicio generado |
| 422 | Error de validación - Parámetros incorrectos |
| 500 | Error interno del servidor |

---

### GET `/exercises/{exercise_id}`

Descarga el archivo HTML del ejercicio generado.

#### Parámetros de entrada

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `exercise_id` | string | ID del ejercicio a descargar |

#### Respuesta

Devuelve el contenido HTML del ejercicio como respuesta HTML.

---

### GET `/audios/{filename}`

Descarga un archivo de audio generado.

#### Parámetros de entrada

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `filename` | string | Nombre del archivo de audio (ej: "Audio_1.mp3") |

#### Respuesta

Devuelve el archivo de audio en formato MP3.


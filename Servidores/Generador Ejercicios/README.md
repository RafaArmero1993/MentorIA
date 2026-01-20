# Generador de Ejercicios Personalizados

API desarrollada con FastAPI para generar ejercicios educativos personalizados en formato HTML. Utiliza IA (Gemini 2.5 Flash) para crear ejercicios adaptados a los intereses del alumno y genera pistas en formato audio mediante text-to-speech (ElevenLabs).

## Requisitos Previos

- Python 3.11 o superior
- Cuenta de Google Cloud Platform con acceso a Gemini API
- Cuenta de ElevenLabs con acceso a su API

## Instalación y Ejecución

### Configuración de Variables de Entorno

Modifica el archivo `.env` introduciéndole las siguientes variables:

```env
GOOGLE_CLOUD_GEMINI_API_KEY=tu_api_key_aqui
ELEVENLABS_API_KEY=tu_api_key_aqui
```

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

## Documentación Interactiva

Accede a la documentación Swagger interactiva en: http://127.0.0.1:8000/docs

## Endpoints

### POST `/generar_ejercicios`

Genera una batería de ejercicios personalizados en formato HTML basándose en un contenido formativo de referencia, el nivel académico, la asignatura y los intereses del alumno. Cada ejercicio incluye un código QR que enlaza a un audio con pistas para su resolución en caso de tener dificultades para la resolución.La API proporciona un identificador del documento generado (**exercise_id**).

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

**Ejemplo de respuesta:**

```json
{
  "exercise_id": 5252638
}
```

### GET `/exercises/{exercise_id}`

Visualiza el archivo HTML del ejercicio generado.

### GET `/audios/{audio_id}`

Permite acceder a uno de los audios de ayuda para la resolución de lso ejercicios generados en formato MP3 y accesibles a través del QR.

#### Parámetros de entrada

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `audio_id` | string | ID del audio explicativo a descargar |

---

#### Códigos de respuesta

| Código | Descripción |
|--------|-------------|
| 200 | Éxito |
| 422 | Error de validación |
| 500 | Error interno del servidor |





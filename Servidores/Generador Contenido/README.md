# Generador de Contenido Educativo

API desarrollada con FastAPI para generar contneido educativos en formato HTML. Utiliza IA (Gemini 2.5 Flash y Gemini 2.5 Pro) para crear temarios en base a las indicaciones del profesorado. Complementa esta formación con contenido multimedia (imágenes y audio explicativo).


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
docker run --rm -p 8000:8000 --env-file .env generador-contenido:latest
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

### POST `/generar_contenido`

Genera el documento HTML completo con todo el temario y almacenarlo en la carpeta documents (a futuro una base de datos documental). Cada sección cuenta con una explicación por voz para aquellos alumnso que lo puedan requerir. La API proporciona un identificador del documento generado (**document_id**).

#### Parámetros de entrada

| Parámetro | Tipo | Obligatorio | Descripción |
|-----------|------|-------------|-------------|
| `nivel_academico` | string | Sí | Nivel académico del alumno (ej: "4º ESO", "1º Bachillerato") |
| `asignatura` | string | Sí | Asignatura del trabajo (ej: "Biología", "Matemáticas") |

#### Ejemplo de petición

```json
{
  "nivel_academico": "4º ESO",
  "asignatura": "Biología"
}
```

**Ejemplo de respuesta:**
```json
{
  "document_id": "1234"
}
```

### GET `/documents/{document_id}`

Permite visualizar un contenido determinado.

#### Parámetros de entrada

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `document_id` | string | ID del contenido formativo a descargar |


### GET `/audios/{audio_id}`

Permite acceder a uno de los audios explicativos generados en formato MP3 y accesibles a través del QR.

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

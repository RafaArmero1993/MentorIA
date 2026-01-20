# Generador de Trabajos Monográficos Personalizados

API desarrollada con FastAPI para generar trabajos monográficos educativos personalizados en formato HTML. Utiliza IA (Gemini 2.5 Pro) para crear trabajos monográficos adaptados a los intereses del alumno y orientados hacia su futuro grado formativo.

## Requisitos Previos

- Python 3.11 o superior
- Cuenta de Google Cloud Platform con acceso a Gemini API

## Instalación y Ejecución

### Configuración de Variables de Entorno

Modifica el archivo `.env` introduciéndole las siguientes variables:

```env
GOOGLE_CLOUD_GEMINI_API_KEY=tu_api_key_aqui
```

### Opción 1: Ejecutar con Docker

```bash
docker build -t generador-trabajos:latest .
docker run --rm -p 8000:8000 --env-file .env generador-trabajos:latest
```

### Opción 2: Ejecutar directamente

```bash
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --no-cache-dir -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Documentación Interactiva

Accede a la documentación Swagger interactiva en: http://127.0.0.1:8000/docs

## Endpoints

### POST `/generar_trabajo`

Genera un trabajo monográfico personalizado en formato HTML basándose en un documento formativo de referencia , el nivel académico, la asignatura, los intereses del alumno y el grado formativo que desea estudiar. Lo que genera es un JSON con un identificado del trabajo monográfico (**work_id**).

#### Parámetros de entrada

| Parámetro | Tipo | Obligatorio | Descripción |
|-----------|------|-------------|-------------|
| `nivel_academico` | string | Sí | Nivel académico del alumno (ej: "4º ESO", "1º Bachillerato") |
| `asignatura` | string | Sí | Asignatura del trabajo (ej: "Biología", "Matemáticas") |
| `unidad` | string | Sí | Unidad didáctica o tema del trabajo (ej: "Animales vertebrados") |
| `intereses` | string | Sí | Descripción de los intereses personales del alumno |
| `document_id` | string | Sí | ID del documento PDF de referencia ubicado en `documents/Documento_{document_id}.pdf` |
| `degree_id` | string | Sí | ID del grado formativo ubicado en `degrees/Grado_{degree_id}.pdf` |

#### Ejemplo de petición

```json
{
  "nivel_academico": "4º ESO",
  "asignatura": "Biología",
  "unidad": "Animales vertebrados",
  "intereses": "Me gusta la bici, la pesca y los videojuegos",
  "document_id": "1234",
  "degree_id": "5678"
}
```

#### Ejemplo de respuesta

```json
{
  "work_id": 2005790
}
```

### GET `/works/{work_id}`

Descarga el archivo HTML del trabajo monográfico generado.

#### Parámetros de entrada

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `work_id` | string | ID del trabajo a descargar |

---

#### Códigos de respuesta

| Código | Descripción |
|--------|-------------|
| 200 | Éxito |
| 422 | Error de validación |
| 500 | Error interno del servidor |




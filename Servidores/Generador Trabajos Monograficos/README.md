# Generador de Trabajos Monográficos Personalizados

API desarrollada con FastAPI para generar trabajos monográficos educativos personalizados en formato HTML. Utiliza IA (Gemini 2.5 Pro) para crear trabajos monográficos adaptados a los intereses del alumno y orientados hacia su futuro grado formativo.

## Descripción

Esta aplicación genera trabajos monográficos personalizados para estudiantes de educación secundaria, considerando:
- El contenido de un documento PDF de referencia
- Los intereses personales del alumno
- El grado formativo que desea cursar en el futuro
- La conexión entre el trabajo y las salidas profesionales del grado

## Requisitos Previos

- Python 3.8 o superior
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

Genera un trabajo monográfico personalizado en formato HTML basándose en un documento PDF de referencia, el nivel académico, la asignatura, los intereses del alumno y el grado formativo que desea estudiar.

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

#### Respuesta

Devuelve un JSON con el identificador único del trabajo generado.

**Estructura de respuesta:**

```json
{
  "work_id": 2005790
}
```

**Campos de la respuesta:**

| Campo | Descripción |
|-------|-------------|
| `work_id` | Identificador único del trabajo monográfico generado (aleatorio entre 1-10000000) |

#### Proceso interno

1. **Carga de documentos**: 
   - Lee el documento PDF de referencia desde `documents/Documento_{document_id}.pdf`
   - Lee el PDF del grado formativo desde `degrees/Grado_{degree_id}.pdf`

2. **Generación del trabajo monográfico con IA**: Utiliza Gemini 2.5 Pro para crear un trabajo original que incluye:
   - Identificación de una temática relacionada con el contenido, los intereses del alumno y las salidas profesionales
   - Descripción del objetivo y finalidad del trabajo
   - Lista ordenada de tareas a realizar
   - Planificación temporal (1 mes, 1-2 horas semanales)
   - Explicación de la utilidad del trabajo para el futuro profesional del alumno
   
3. **Personalización sutil**: 
   - Los intereses del alumno se integran de forma natural (ej: términos en negrita)
   - El trabajo se conecta con las salidas profesionales del grado elegido

4. **Creación del documento HTML**: 
   - Estructura personalizada con cabecera, unidad, capítulo y contenido
   - Formato HTML limitado a etiquetas: `<p>`, `<b>`, `<i>`, `<u>`, `<ul>`, `<ol>`, `<li>`
   - Estilos CSS cargados desde `config/style.css`
   
5. **Almacenamiento**: Guarda el trabajo en `works/Work_{work_id}.html`

#### Códigos de respuesta

| Código | Descripción |
|--------|-------------|
| 200 | Éxito - Devuelve el ID del trabajo generado |
| 422 | Error de validación - Parámetros incorrectos |
| 500 | Error interno del servidor |

---

### GET `/works/{work_id}`

Descarga el archivo HTML del trabajo monográfico generado.

#### Parámetros de entrada

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `work_id` | string | ID del trabajo a descargar |

#### Respuesta

Devuelve el contenido HTML del trabajo monográfico como respuesta HTML.

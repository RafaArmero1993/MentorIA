# API de Recomendación de Salidas Formativas

API desarrollada con FastAPI para recomendar grados de Formación Profesional basándose en los intereses del usuario, ubicación y disponibilidad de centros educativos.

## Requisitos Previos

- Python 3.11 o superior
- Cuenta de Google Cloud Platform con acceso a Gemini API y a Distance Matrix API

## Instalación y Ejecución

### Configuración de Variables de Entorno

Modifica el archivo `.env` introduciéndole las siguientes variables:

```env
GOOGLE_CLOUD_GEMINI_API_KEY=tu_api_key_aqui
GOOGLE_CLOUD_MAPS_API_KEY=tu_api_key_aqui
```

### Opción 1: Ejecutar con Docker
```bash
docker run --rm -p 8000:8000 --env-file .env mi-api:latest
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

### POST `/salidas_profesionales`

Obtiene los grados formativos recomendados según los intereses del alumno, los tipo de grado (*básico*, *medio* o *superior*), ubicación geográfica, modalidad (*mañanas* o *tardes*)y medios de transporte disponibles (*propio*  o *público*).

#### Parámetros de entrada

| Parámetro | Tipo | Obligatorio | Descripción |
|-----------|------|-------------|-------------|
| `tipo_grado` | string | Sí | Tipo de grado formativo (ej: "Grado Básico", "Grado Medio", "Grado Superior") |
| `localidad` | string | Sí | Localidad del usuario en formato: "Ciudad, Provincia, Comunidad Autónoma (ES)" |
| `provincia` | string | Sí | Provincia del usuario (ej: "Valencia/València") |
| `modalidad` | string | Sí | Modalidad de centro educativo (ej: "Centro público", "Centro privado") |
| `turno` | string | Sí | Turno preferido ("mañana" o "tarde") |
| `vehiculo` | string | Sí | Medio de transporte disponible (ej: "driving", "bicycling") |
| `intereses` | string | Sí | Descripción detallada de los intereses del alumno |

#### Ejemplo de petición

```json
{
  "tipo_grado": "Grado Básico",
  "localidad": "Puerto de Sagunto, Valencia/València, Comunidad Valenciana (ES)",
  "provincia": "Valencia/València",
  "modalidad": "Centro público",
  "turno": "mañana",
  "vehiculo": "driving",
  "intereses": "Me interesan sobre todo dos cosas, aunque últimamente me cueste reconocerlo: la tecnología (el móvil, las apps, los videojuegos y editar vídeos) y las actividades prácticas donde puedo aprender haciendo y ver un resultado claro. Cuando estoy con la tecnología, por un rato se me va la cabeza de los problemas de casa y me gusta aprender por mi cuenta con tutoriales, porque ahí noto que mejoro sin que nadie me juzgue. Y cuando hago cosas prácticas —arreglar, montar, construir algo sencillo— siento control y la sensación de que valgo para algo. En el instituto he perdido la motivación porque muchas veces siento que voy tarde, que no encajo y que si lo intento voy a fallar otra vez, pero con estos dos intereses, si alguien me acompaña y me lo pone por pasos, sí puedo engancharme y volver a empezar."
}
```

**Ejemplo de respuesta:**

```json
{
  "data": [
    {
      "real-decreto": "https://www.boe.es/eli/es/rd/2018/02/19/73",
      "curriculo-mecd": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2019-10843",
      "perfiles-profesionales": "[URL del PDF con perfiles profesionales](https://www.todofp.es/dam/jcr:9d8091d9-f6c4-4b81-9580-c09c45d6e9bf/t-tulo-profesional-b-sico-en-acceso-y-conservaci-n-e.pdf)",
      "localidad": "Xàtiva",
      "centro": "Instituto de Educación Secundaria | JOSEP DE RIBERA",
      "curriculo-ccaa": "https://dogv.gva.es/datos/2025/08/13/pdf/2025_32763_es.pdf",
    }
  ]
}
```

---

#### Códigos de respuesta

| Código | Descripción |
|--------|-------------|
| 200 | Éxito |
| 422 | Error de validación |
| 500 | Error interno del servidor |







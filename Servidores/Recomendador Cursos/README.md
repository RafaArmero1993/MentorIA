# API de Recomendación de Salidas Formativas

API desarrollada con FastAPI para recomendar grados de Formación Profesional basándose en los intereses del usuario, ubicación y disponibilidad de centros educativos.

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

## Documentación Swagger
Se pueden probar los endpoints en el Swagger: http://127.0.0.1:8000/docs

## Endpoints

### POST `/salidas_profesionales`

Obtiene los grados formativos recomendados según el perfil del usuario, considerando tipo de grado, ubicación, modalidad, intereses personales y medios de transporte disponibles.

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

#### Respuesta

Devuelve un JSON con los grados formativos recomendados que mejor se ajustan al perfil del usuario.

**Estructura de respuesta:**

```json
{
  "data": [
    {
      "real-decreto": "URL del Real Decreto",
      "curriculo-mecd": "URL del currículo del Ministerio",
      "perfiles-profesionales": "URL del PDF con perfiles profesionales",
      "localidad": "Localidad del centro",
      "centro": "Nombre del centro educativo",
      "curriculo-ccaa": "URL del currículo de la Comunidad Autónoma",
    }
  ]
}
```

**Campos de la respuesta:**

| Campo | Descripción |
|-------|-------------|
| `real-decreto` | Enlace al Real Decreto que regula el grado |
| `curriculo-mecd` | Enlace al currículo oficial del Ministerio de Educación |
| `perfiles-profesionales` | Enlace al documento PDF con las salidas profesionales |
| `localidad` | Localidad donde se imparte el grado |
| `centro` | Nombre del centro educativo |
| `curriculo-ccaa` | URLs con documentos curriculares específicos de la Comunidad Autónoma |

#### Proceso interno

1. **Extracción de datos**: Realiza web scraping en www.todofp.es para obtener los grados formativos disponibles
2. **Filtrado geográfico**: Filtra centros por provincia y modalidad especificada
3. **Cálculo de distancias**: Utiliza Google Maps API para calcular tiempos de desplazamiento según el medio de transporte
4. **Evaluación de afinidad**: Emplea IA (Gemini 2.5 Flash/Pro) para analizar la afinidad entre los intereses del usuario y las salidas profesionales
5. **Ranking**: Compara los 5 grados con mayor puntuación (Gemini 2.5 Flash/Pro) y selecciona los más relevantes mediante análisis comparativo

#### Códigos de respuesta

| Código | Descripción |
|--------|-------------|
| 200 | Éxito - Devuelve los grados recomendados |
| 422 | Error de validación - Parámetros incorrectos |
| 500 | Error interno del servidor |





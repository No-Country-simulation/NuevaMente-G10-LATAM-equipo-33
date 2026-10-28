# 🧠 NuevaMente — Frontend & Interactive Learning Interface

> **Transformando documentación técnica en experiencias de microaprendizaje adaptativo mediante IA.**  
> Interfaz web interactiva tipo SPA desarrollada con **Streamlit**, diseñada bajo principios de **Frontend Engineering & UI/UX Design** por el equipo de desarrollo frontend.

[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![UI/UX System](https://img.shields.io/badge/UI%2FUX-Design_System-0094F0?style=for-the-badge&logo=figma&logoColor=white)](#fundamentos-diseno)
[![WCAG Compliant](https://img.shields.io/badge/WCAG_2.1-AA%20%2F%20AAA-10B77F?style=for-the-badge)](#tokens-color)
[![No Country](https://img.shields.io/badge/No_Country-Simulation_G10-00E599?style=for-the-badge)](https://www.nocountry.tech/)

---

<a id="vision-general"></a>
## 📌 Visión del Producto

**NuevaMente** es una plataforma orientada a estudiantes y profesionales del sector tecnológico que necesitan asimilar documentación técnica densa sin caer en la fatiga cognitiva del estudio tradicional.

El equipo frontend asumió de forma integral la **arquitectura técnica** y el **diseño de producto UI/UX**, planteando una experiencia de usuario inspirada en herramientas utilitarias de alta adopción (*como iLovePDF*): un flujo lineal de 3 pasos (*Carga ➔ Configuración ➔ Resultado*), reactivo, directo y en una sola pantalla.

---

<a id="evidencia-visual"></a>
## 📸 Evidencia Visual & Prototipado de Interfaz

> ℹ️ **Nota sobre el entorno de ejecución:** Las capturas a continuación documentan el prototipado y validación de diseño de la interfaz. En el entorno real de Streamlit, la plataforma se ejecuta en **Modo Oscuro (Dark Mode)** debido a que el framework maneja el tema de forma estática en `config.toml` y no ofrece soporte nativo para alternar dinámicamente entre temas claro y oscuro en tiempo de ejecución.

### 1. Flujo Completo de Usuario (Carga, Parámetros y Resultados)
Comparativa del flujo interactivo en sus tres fases de interacción:
* **Paso 1 (Carga):** Dropzone con arrastre y validación de archivos (`PDF`, `DOCX`, `TXT`).
* **Paso 2 (Parámetros):** Selectores adaptativos para perfil destinatario, nicho y nivel pedagógico.
* **Paso 3 (Resultado):** Panel interactivo de estudio activo con Flashcards y Quiz con feedback dinámico.

![Comparativa visual del flujo de 3 pasos de NuevaMente: Carga de documentos en Paso 1, Personalización pedagógica en Paso 2 y Resultados interactivos con Flashcards y Quiz en Paso 3, contrastados en modo claro y modo oscuro](assets/nuevamente_3_pantallas_preview.png)

### 2. Sistema de Diseño & Validación de Contraste WCAG 2.1
Tokens aplicados a componentes clave (chips, badges, títulos y opciones interactivas) verificados bajo normas de accesibilidad:
* **Texto principal sobre fondo oscuro:** Ratio **17.06:1** (*Supera WCAG AAA*).
* **Acento Ámbar (`#F59F0A`):** Ratio **9.12:1** (*Supera WCAG AAA*).
* **Acento Verde (`#10B77F`):** Ratio **6.52:1** (*Supera WCAG AA/AAA*).

![Evaluación de accesibilidad y contraste WCAG 2.1 del sistema de diseño de NuevaMente en modo claro y modo oscuro, detallando ratios de legibilidad aprobados para botones primarios, badges de estado y textos de lectura](assets/nuevamente_theme_preview.png)

### 3. Componente Gráfico: Gráfico Donut de Puntaje (`render_donut`)
Evaluación aislada de la función `render_donut()` desarrollada en CSS/SVG nativo con gradiente cónico (`conic-gradient`), aplicando cambio dinámico de color semántico según desempeño (Ámbar `<60%` para refuerzo vs. Verde `≥60%` para logro):

![Validación aislada del componente gráfico render_donut en modo claro y modo oscuro mostrando porcentajes de 0%, 25%, 59% en color ámbar de acento y 60%, 85%, 100% en verde secundario](assets/donut_validation_preview.png)

---

<a id="fundamentos-diseno"></a>
## 🎨 Fundamentos de Diseño UI/UX & Ergonomía Cognitiva

### 1. Flujo Mental Inspirado en iLovePDF
Se priorizó un modelo mental ampliamente reconocido por los usuarios: una secuencia directa sin barras laterales que desvíen la atención del objetivo pedagógico.

```mermaid
flowchart LR
    A["Paso 1 · Carga<br/>Dropzone tipo iLovePDF<br/>(PDF, DOCX, TXT)"] -->|Validación inmediata| B["Paso 2 · Ajustes<br/>Audiencia, nicho y nivel<br/>Selectores adaptativos"]
    B -->|Generación con IA| C["Paso 3 · Estudio Activo<br/>Flashcards interactivas &<br/>Quiz con donut radial"]
```

<a id="tokens-color"></a>
### 2. Psicología del Color: Concentración con Energía

La paleta cromática se seleccionó para proporcionar serenidad visual durante sesiones de lectura prolongada, incorporando puntos focales de alta energía:

| Token | Hex | Muestra | Justificación Cognitiva & Rol Semántico |
| :--- | :---: | :---: | :--- |
| **Deep Background** | `#070B22` | ![#070B22](https://img.shields.io/badge/-%20-070B22?style=flat-square) | **Concentración:** Azul marino profundo de baja luminancia. Reduce el deslumbramiento ocular en entornos oscuros. |
| **Surface Card** | `#0F1430` | ![#0F1430](https://img.shields.io/badge/-%20-0F1430?style=flat-square) | **Jerarquía:** Superficie de elevación suave que estructura visualmente cada sección. |
| **Text Primary** | `#F0F0F0` | ![#F0F0F0](https://img.shields.io/badge/-%20-F0F0F0?style=flat-square) | **Legibilidad:** Blanco templado optimizado para lectura técnica extensa sin causar encandilamiento. |
| **Brand Primary** | `#0094F0` | ![#0094F0](https://img.shields.io/badge/-%20-0094F0?style=flat-square) | **Foco Tecnológico:** Azul cian eléctrico para acciones primarias (CTAs) y títulos de paso. |
| **Success / Valid** | `#10B77F` | ![#10B77F](https://img.shields.io/badge/-%20-10B77F?style=flat-square) | **Refuerzo Positivo:** Verde esmeralda para validaciones correctas y aprobaciones de quiz (≥60%). |
| **Accent Energy** | `#F59F0A` | ![#F59F0A](https://img.shields.io/badge/-%20-F59F0A?style=flat-square) | **Dinamismo Mental:** Ámbar cálido que resalta badges, pasos activos y conceptos clave a memorizar. |

### 3. Tipografía Anatómica para Estudio

* **Nunito (Google Fonts):** Fuente sans-serif principal. Sus terminaciones suavemente redondeadas reducen la rigidez geométrica típica de las tipografías corporativas, aportando calidez, cercanía y una lectura más descansada durante períodos de estudio continuos.
* **IBM Plex Mono:** Tipografía monoespaciada reservada para identificadores técnicos, bucket de OCI y depuración de payloads.
* **Material Symbols:** Íconos vectoriales de Streamlit (`:material/nombre:`) integrados nativamente para un renderizado liviano.

---

<a id="arquitectura"></a>
## 🏛️ Arquitectura Frontend & Integración con Backend

La interfaz opera como una aplicación de una sola página coordinada mediante el estado de sesión (`st.session_state`):

```mermaid
flowchart TD
    subgraph UI ["Capa de Presentación (Streamlit SPA)"]
        U["Usuario"] --> APP["app.py<br/>Layout & Routing SPA"]
        APP --> S1["pages/seccion1_carga.py<br/>Dropzone de archivos<br/>Extracción de texto y validación"]
        APP --> S2["pages/seccion2_parametros.py<br/>Configuración pedagógica<br/>Despacho HTTP vía client_config"]
        APP --> S3["pages/seccion3_resultados.py<br/>Render interactivo de Flashcards<br/>Quiz con feedback y render_donut"]
    end

    subgraph Core ["Tokens & Configuración"]
        TH["theme.py<br/>CSS inyectado & Gráficos"]
        CFG["config.toml<br/>Tema base Streamlit"]
        CS["constants.py<br/>Perfiles, Formatos y Niveles"]
    end

    subgraph Service ["Capa de Cliente & Red"]
        CC["client_config.py<br/>URL endpoint & Timeout (300s)<br/>Fallback mock resiliente"]
    end

    subgraph Backend ["Servicios de Backend & Nube"]
        API["Backend FastAPI<br/>/api/v1/adapt"]
        RAG["Pipeline Ingesta RAG"]
        OCI["Oracle Cloud Infrastructure<br/>Object Storage"]
    end

    S1 --> S2 --> S3
    S1 -.-> TH & CFG
    S2 -.-> CS & CC
    S3 -.-> TH
    CC -->|POST HTTP / Fallback| API
    API --> RAG
    API --> OCI
```

---

<a id="estructura-archivos"></a>
## 📂 Estructura Real del Módulo Frontend

```
interfaz/
├── .gitignore               # Exclusiones de Git locales del módulo
├── config.toml              # Definición de paleta y base del tema oscuro nativo
├── assets/
│   ├── logo.png             # Isotipo oficial de NuevaMente
│   ├── nuevamente_3_pantallas_preview.png # Prototipo visual del flujo de 3 pasos
│   ├── nuevamente_theme_preview.png       # Matriz de accesibilidad y contraste WCAG
│   └── donut_validation_preview.png       # Validación del componente donut de puntaje
├── pages/
│   ├── __init__.py
│   ├── seccion1_carga.py    # Paso 1: Dropzone, lectura de archivo y extracción
│   ├── seccion2_parametros.py # Paso 2: Selección de parámetros y consumo de API
│   └── seccion3_resultados.py # Paso 3: Renderizado interactivo (Flashcards y Quiz)
├── app.py                   # Orquestador del flujo, control de paso_actual y layout
├── client_config.py         # Configuración del endpoint backend (ADAPT_URL) y timeout
├── constants.py             # Enums de PERFILES, FORMATOS y NIVELES
├── theme.py                 # Inyección de estilos CSS, fuentes y función render_donut()
├── requirements.txt         # Dependencias directas del frontend
└── README.md                # Documentación técnica del módulo
```

---

<a id="integracion-backend"></a>
## 🔌 Integración y Comunicación con Backend

La comunicación entre el frontend y el backend está orquestada en `seccion2_parametros.py` a través de los parámetros definidos en `client_config.py`:

* **Endpoint de Adaptación:** `POST {BACKEND_URL}/api/v1/adapt` (por defecto `http://localhost:8000/api/v1/adapt`).
* **Timeout configurado:** `300 segundos` (adaptado a los tiempos de inferencia de modelos LLM con RAG).
* **Payload Despachado:**
  * `documento_titulo`: Nombre del recurso subido.
  * `documento_contenido`: Texto extraído del documento.
  * `perfil_destinatario`: Audiencia pedagógica elegida.
  * `formato_salida`: Formato mapeado (`Flashcards` o `Quiz`).
  * `nicho_sector`: Nicho industrial de contextualización.
  * `nivel_detalle`: Grado de profundidad técnica.
* **Tolerancia a fallos:** Si el servicio backend no está disponible o la conexión falla, el frontend incluye un generador mock de contingencia que previene la ruptura de la aplicación y permite evaluar la experiencia de usuario.

---

<a id="formatos-aprendizaje"></a>
## 🚀 Formatos de Aprendizaje Soportados

1. **🃏 Flashcards de Memorización:**
   * Navegación interactiva tarjeta por tarjeta (*Anterior / Siguiente*).
   * Interacción para alternar entre el frente (concepto/pregunta) y el dorso (explicación detallada).
   * Contador dinámico de progreso.

2. **📝 Quiz Interactivo con Justificaciones:**
   * Presentación de preguntas estructuradas con opciones identificadas por letras (A, B, C, D).
   * Registro reactivo de respuestas seleccionadas por el usuario.
   * Feedback explicativo inmediato con justificación pedagógica por pregunta.
   * Gráfico donut radial SVG (`render_donut`) que calcula visualmente el porcentaje final de aciertos.

3. **Formatos Estructurados Adicionales:**
   * Soporte base extensible para *Guía Práctica Paso a Paso (Tutorial)*, *Resumen Ejecutivo* y *Guion Audiovisual*.

---

<a id="instalacion"></a>
## 🛠️ Instalación y Ejecución Local

### Prerrequisitos
* Python 3.10 o superior instalado.
* Entorno virtual (`venv` o `conda`).

```bash
# 1. Clonar el repositorio
git clone https://github.com/No-Country-simulation/NuevaMente-G10-LATAM-equipo-33.git

# 2. Situarse en la carpeta de la interfaz
cd NuevaMente-G10-LATAM-equipo-33/interfaz

# 3. Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate       # En Windows: venv\Scripts\activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Iniciar la aplicación
streamlit run app.py
```

> 💡 **Nota de ejecución:** Se recomienda iniciar el servidor desde el directorio `interfaz/` para asegurar la correcta resolución de rutas de assets y estilos locales. La app iniciará en `http://localhost:8501`.

---

<a id="estado-proyecto"></a>
## 📊 Estado de Implementación & Checklist del Proyecto

| Hito / Requisito | Módulo / Ubicación | Estado |
| :--- | :--- | :---: |
| **SPA Interactiva en una sola página** | `interfaz/app.py` | ✅ Completado |
| **Dropzone Multiformato (PDF, DOCX, TXT)** | `interfaz/pages/seccion1_carga.py` | ✅ Completado |
| **Parametrización pedagógica adaptativa** | `interfaz/pages/seccion2_parametros.py` | ✅ Completado |
| **Componentes de Flashcards y Quiz con Donut SVG** | `interfaz/pages/seccion3_resultados.py` | ✅ Completado |
| **Sistema de Diseño e inyección CSS personalizada** | `interfaz/theme.py` | ✅ Completado |
| **Consumo HTTP resiliente de API backend** | `interfaz/client_config.py` | ✅ Completado |
| **Integración con Pipeline RAG e Ingesta** | `ingesta_rag/` & `backend/` | ✅ Completado |
| **Orquestación con Agentes LLM** | `orquestacion_agentes/` & `backend/` | ✅ Completado |
| **Persistencia en OCI Object Storage** | `oci_storage/` & `backend/` | ✅ Completado |
| **Flujo de ramas Git Flow & Conventional Commits** | Repositorio GitHub | ✅ Completado |

---

<a id="retos-tecnicos"></a>
## ⚠️ Retos Técnicos & Limitaciones Detectadas

Durante el ciclo de desarrollo se identificaron limitaciones técnicas ligadas a las características intrínsecas de Streamlit:

1. **Limitación de Tema Dinámico (Light Mode vs. Dark Mode en Runtime):**
   * Aunque los tokens de diseño para modo claro y modo oscuro fueron conceptualizados, prototipados y verificados con ratios WCAG AA/AAA, Streamlit gestiona la configuración de temas mediante su archivo estático `config.toml`.
   * Debido a esto, la aplicación se ejecuta con **Modo Oscuro forzado**. No existe soporte nativo en Streamlit para ofrecer un switch de cambio de tema al usuario final en tiempo de ejecución sin recargar la aplicación o mutar configuraciones del servidor.
   * *Decisión:* La definición de tokens en `theme.py` permanece preparada para reutilizarse directamente en una futura migración a React.

2. **Resolución de Rutas Estáticas para el Logo:**
   * En `app.py`, la comprobación de existencia del logo (`os.path.exists("assets/logo.png")`) depende del directorio de trabajo actual (*CWD*). Si el usuario ejecuta `streamlit run interfaz/app.py` desde la raíz del repositorio en lugar de entrar a `interfaz/`, la ruta relativa no encuentra el archivo y oculta el logo temporalmente.

3. **Ciclo de Re-renderizado y Gestión de Estado:**
   * Ante cada interacción del usuario, Streamlit vuelve a ejecutar el script completo de Python. Para evitar pérdida de datos entre pasos, fue necesario encapsular estrictamente el control de flujo en variables de `st.session_state` (`paso_actual`, `solicitud`, `resultado`).

---

<a id="roadmap"></a>
## 🚀 Roadmap Técnico & Oportunidades de Evolución

Para una siguiente versión orientada a producción masiva, se plantean las siguientes mejoras arquitectónicas:

```mermaid
flowchart LR
    R1["Fase 1 · Feedback UX<br/>Pantallas de espera dedicadas<br/>(Loading / Skeletons)"] --> R2["Fase 2 · Exportación<br/>Botón de descarga<br/>(PDF, MD y Anki)"]
    R2 --> R3["Fase 3 · Migración Web<br/>Transición a React / Next.js<br/>+ Tailwind CSS"]
```

1. **Pantallas Intermedias de Espera (*Loading States*):**
   * **Pantalla de Espera 1 (post-Carga):** Estado visual de procesamiento y skeleton loader mientras se realiza la extracción de texto y chunking de archivos voluminosos.
   * **Pantalla de Espera 2 (post-Parámetros):** Pantalla interactiva con microanimaciones y consejos de estudio mientras los agentes LLM sintetizan el contenido a través de la API.

2. **Funcionalidad de Exportación y Descarga:**
   * Incorporar un botón de descarga multiformato en la sección de resultados para exportar las flashcards y cuestionarios en **PDF imprimible**, **Markdown** para aplicaciones de notas (*Obsidian, Notion*) y archivos compatibles con **Anki**.

3. **Migración Arquitectónica a React / Next.js + Tailwind CSS:**
   * Reescribir la capa de presentación sobre un stack moderno de frontend que permita alternar dinámicamente entre Light y Dark Mode mediante variables CSS nativas, brindar animaciones fluidas con Framer Motion y eliminar la sobrecarga de re-runs de Streamlit.

---

<a id="git-flow"></a>
## 🌿 Convención Git & Colaboración

El equipo de frontend mantuvo una separación limpia de ramas de trabajo:

```
interfaz (rama integradora del frontend)
├── interfaz-seccion1-carga       → Feature branch: Carga & Dropzone
├── interfaz-seccion2-parametros  → Feature branch: Parámetros & Selectores
└── interfaz-seccion3-resultados  → Feature branch: Render de Resultados
```

* Se aplicaron estándares de **Conventional Commits** (`feat:`, `fix:`, `style:`, `docs:`) y revisiones mediante Pull Request hacia la rama `interfaz` antes de la integración con `main`.

---

<a id="equipo"></a>
## 👥 Equipo Frontend & UI/UX

* **Beatriz Delgadillo**
* **Alessandra**
* **Gisell**

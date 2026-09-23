# orquestacion-agentes

Este módulo recibe información de otro módulo y usa Gemini (IA de Google) para generar contenido educativo adaptado (flashcards, quiz, etc).

## Cómo instalarlo y correrlo

1. Conseguí tu API Key de Gemini gratis en: https://aistudio.google.com/apikey

2. Entrá a la carpeta orquestacion-agentes y creá el entorno:

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

3. Copiá el archivo .env.example y renombralo a .env. Adentro pegá tu API Key así:

GOOGLE_API_KEY=tu_api_key_aca

4. Corré el programa:

python main.py

Te va a mostrar en pantalla un ejemplo de contenido generado.

## Formatos que genera por ahora

- Flashcards
- Quiz

## Si algo falla

- Si dice que no encuentra "shared": asegurate de estar parado dentro de la carpeta orquestacion-agentes y hacé git pull origin main.
- Si dice que el modelo no existe: puede que Google haya cambiado el nombre del modelo, hay que actualizarlo en el código.

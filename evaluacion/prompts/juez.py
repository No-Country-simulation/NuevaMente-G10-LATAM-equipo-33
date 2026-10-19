"""Prompt del evaluador (LLM como juez)."""

PROMPT_JUEZ = """Sos un revisor riguroso de contenido educativo técnico. Tu tarea es
verificar si el CONTENIDO GENERADO es fiel al CONTEXTO de la fuente original y si es
adecuado para el destinatario.

CONTEXTO DE LA FUENTE ORIGINAL:
{contexto_texto}

PARÁMETROS DEL CONTENIDO:
- Título: {titulo}
- Perfil del destinatario: {perfil_destinatario}
- Formato: {formato_salida}

ÍTEMS A EVALUAR (cada uno con su índice):
{items_texto}

INSTRUCCIONES:
1. Para CADA ítem, emití un veredicto usando únicamente el CONTEXTO. No uses
   conocimiento externo, aunque sea correcto en la realidad:
   - "respaldado": el contexto sustenta completamente el ítem.
   - "parcial": el contexto sustenta solo una parte, o el ítem agrega datos que
     no están en el contexto.
   - "no_respaldado": el contexto no lo sustenta o lo contradice.
2. En un quiz, evaluá la pregunta, la respuesta correcta y la justificación. Las
   opciones incorrectas son distractores a propósito: no las penalices por ser falsas.
3. Evaluá la claridad pedagógica general para el perfil "{perfil_destinatario}": lenguaje
   adecuado, ejemplos o analogías, y nivel de profundidad. Respondé Alta, Media o Baja.
4. En las observaciones resumí brevemente qué está bien y qué ítems fallan y por qué.

Devolvé un veredicto por cada índice, sin omitir ninguno.
"""
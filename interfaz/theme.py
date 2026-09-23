"""
Tema visual de NuevaMente: paleta de colores + tipografía.

Los colores "base" (fondo, texto, primario) ya están en
.streamlit/config.toml, que es lo que Streamlit usa nativamente para
pintar botones, inputs, etc. Este archivo agrega lo que Streamlit no
soporta de forma nativa: la fuente personalizada y los colores
"secondary" y "accent", vía CSS inyectado.

Si cambian algún color, actualícenlo en los dos lugares: aquí (para los
usos manuales, como badges) y en .streamlit/config.toml (para los
componentes nativos de Streamlit).
"""

import streamlit as st

PALETTE = {
    "text": "#F0F0F0",
    "background": "#070B22",
    "primary": "#0094F0",
    "secondary": "#10B77F",
    "accent": "#F59F0A",
}

FONT_FAMILY = "Nunito"
FONT_FAMILY_MONO = "IBM Plex Mono"
GOOGLE_FONT_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Nunito:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&"
    "family=IBM+Plex+Mono:wght@400;500;600&display=swap"
)


def inject_custom_css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('{GOOGLE_FONT_URL}');

        html, body, [class*="css"] {{
            font-family: '{FONT_FAMILY}', sans-serif;
        }}

        h1, h2, h3, h4 {{
            font-family: '{FONT_FAMILY}', sans-serif;
            font-weight: 600;
        }}

        /* Tarjeta/sección genérica para separar los 3 bloques en una sola página */
        .nm-section {{
            background-color: rgba(240, 240, 240, 0.03);
            border: 1px solid rgba(240, 240, 240, 0.08);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        /* Pastilla (chip) tipo "STEP 1 · ADD MATERIAL" del mockup de referencia */
        .nm-pill {{
            display: inline-block;
            background-color: rgba(240, 240, 240, 0.08);
            color: {PALETTE["text"]};
            padding: 4px 14px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.02em;
        }}

        .nm-pill-accent {{
            display: inline-block;
            background-color: {PALETTE["accent"]};
            color: #241704;
            padding: 4px 14px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
        }}

        .nm-badge-secondary {{
            background-color: {PALETTE["secondary"]};
            color: #08211a;
            padding: 4px 12px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            display: inline-block;
        }}

        .nm-badge-accent {{
            background-color: {PALETTE["accent"]};
            color: #241704;
            padding: 4px 12px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            display: inline-block;
        }}

        .nm-step-title {{
            color: {PALETTE["primary"]};
            font-weight: 600;
            font-size: 0.95rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.25rem;
        }}

        /* Letra A/B/C/D de las opciones del quiz */
        .nm-option-letter {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background-color: rgba(240, 240, 240, 0.1);
            color: {PALETTE["text"]};
            font-size: 0.75rem;
            font-weight: 700;
            margin-right: 8px;
        }}

        /* Círculo de puntaje final, tipo donut, con % en el centro */
        .nm-donut-wrap {{
            display: flex;
            justify-content: center;
            margin: 0.5rem 0 1rem;
        }}
        .nm-donut {{
            width: 120px;
            height: 120px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            font-weight: 700;
            color: {PALETTE["text"]};
        }}

        /* Para datos técnicos: bucket de OCI, objeto_id, JSON, etc. */
        .nm-mono {{
            font-family: '{FONT_FAMILY_MONO}', monospace;
            font-size: 0.85rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_donut(pct: int, label: str = "") -> None:
    """Círculo de puntaje (0-100), estilo mockup de referencia."""
    color = PALETTE["secondary"] if pct >= 60 else PALETTE["accent"]
    st.markdown(
        f"""
        <div class="nm-donut-wrap">
            <div class="nm-donut" style="background: conic-gradient({color} {pct}%, rgba(240,240,240,0.08) 0);">
                <div style="background:{PALETTE['background']};width:88px;height:88px;border-radius:50%;
                            display:flex;align-items:center;justify-content:center;flex-direction:column;">
                    <span>{pct}%</span>
                    {f'<span style="font-size:0.65rem;font-weight:400;opacity:0.7">{label}</span>' if label else ""}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
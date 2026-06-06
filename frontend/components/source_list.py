"""
Source list component: Display configured portal sources.
"""

import streamlit as st


def render_source_list(sources):
    """Render each source as a card with name and link."""
    if not sources:
        st.warning("No hay fuentes configuradas.")
        return

    columnas = st.columns(2)
    for idx, fuente in enumerate(sources):
        with columnas[idx % 2]:
            st.markdown(
                f"""
                <div style='border:1px solid #ddd; border-radius:14px; padding:18px; margin-bottom:16px; background-color:#fbfbfb;'>
                    <div style='font-size:16px; font-weight:700; margin-bottom:8px;'>{fuente['name']}</div>
                    <div style='font-size:14px; color:#333; line-height:1.4;'>
                        <a href='{fuente['url']}' target='_blank'>{fuente['url']}</a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

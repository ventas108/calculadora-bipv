"""Utilidades de UI compartidas entre páginas."""
import streamlit.components.v1 as components


def bloquear_traduccion():
    """Impide que Google Translate (Chrome) traduzca la app.

    El traductor automático modifica el DOM por fuera de React y provoca
    errores 'NotFoundError: removeChild' al re-renderizar Streamlit.
    La app ya está en español, así que se marca como no traducible.
    Debe llamarse DESPUÉS de st.set_page_config().
    """
    components.html(
        """
        <script>
        try {
            const doc = window.parent.document;
            doc.documentElement.setAttribute('translate', 'no');
            doc.documentElement.classList.add('notranslate');
            if (!doc.querySelector('meta[name="google"][content="notranslate"]')) {
                const meta = doc.createElement('meta');
                meta.name = 'google';
                meta.content = 'notranslate';
                doc.head.appendChild(meta);
            }
        } catch (e) { /* sin permisos: no romper la app */ }
        </script>
        """,
        height=0,
    )

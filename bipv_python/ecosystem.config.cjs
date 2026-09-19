// PM2 ecosystem — Calculadora BIPV Python (Streamlit)
// Fuente de verdad única (corregida 19-sep-2026 tras confirmar por SSH el
// proceso real en producción: `pm2 describe streamlit-bipv` mostraba
// exec cwd=/var/www/bipv/calculadora-bipv y script args con rutas relativas
// bipv_python/venv/... — ni este archivo ni ecosystem.config.js coincidían
// exactamente antes de esta corrección).
// Guardar en: /var/www/bipv/calculadora-bipv/bipv_python/ecosystem.config.cjs
// Uso: cd /var/www/bipv/calculadora-bipv && pm2 start bipv_python/ecosystem.config.cjs

module.exports = {
  apps: [
    {
      name: "streamlit-bipv",
      script: "bipv_python/venv/bin/streamlit",
      args: "run bipv_python/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true --server.maxUploadSize 200 --server.maxMessageSize 200",
      cwd: "/var/www/bipv/calculadora-bipv",
      interpreter: "none",
      env: {
        PYTHONPATH: "/var/www/bipv/calculadora-bipv/bipv_python",
        PYTHONUNBUFFERED: "1",
      },
      watch: false,
      max_memory_restart: "1G",
      restart_delay: 5000,
      log_date_format: "YYYY-MM-DD HH:mm:ss",
    },
  ],
};


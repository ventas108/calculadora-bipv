// PM2 ecosystem — Calculadora BIPV Python (Streamlit)
// Guardar en: /var/www/bipv/calculadora_bipv/ecosystem.config.js
// Uso: pm2 start ecosystem.config.js

module.exports = {
  apps: [
    {
      name: "calculadora-bipv-python",
      script: "/usr/local/bin/streamlit",
      args: "run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true",
      cwd: "/var/www/bipv/calculadora_bipv",
      interpreter: "none",
      env: {
        PYTHONPATH: "/var/www/bipv/calculadora_bipv",
        PYTHONUNBUFFERED: "1",
      },
      watch: false,
      max_memory_restart: "1G",
      restart_delay: 5000,
      log_date_format: "YYYY-MM-DD HH:mm:ss",
    },
  ],
};

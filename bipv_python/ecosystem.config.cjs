// PM2 ecosystem — Calculadora BIPV Python (Streamlit)
// Uso: pm2 start ecosystem.config.cjs

module.exports = {
  apps: [
    {
      name: "bipv-streamlit",
      script: "/var/www/bipv/calculadora-bipv/bipv_python/venv/bin/streamlit",
      args: "run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true",
      cwd: "/var/www/bipv/calculadora-bipv/bipv_python",
      interpreter: "none",
      env: {
        PYTHONPATH: "/var/www/bipv/calculadora-bipv/bipv_python",
        PYTHONUNBUFFERED: "1",
        PATH: "/var/www/bipv/calculadora-bipv/bipv_python/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
      },
      watch: false,
      max_memory_restart: "1G",
      restart_delay: 5000,
      log_date_format: "YYYY-MM-DD HH:mm:ss",
    },
  ],
};

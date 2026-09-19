// DEPRECADO — usar bipv_python/ecosystem.config.cjs (única fuente de verdad,
// corregida 19-sep-2026 para coincidir con el proceso real en producción:
// nombre `streamlit-bipv`, ruta `/var/www/bipv/calculadora-bipv`). Este
// archivo quedaba con ruta (`calculadora_bipv`, guion bajo) y nombre de
// proceso (`calculadora-bipv-python`) que NUNCA coincidieron con la
// realidad del servidor — no usar para `pm2 start`.
module.exports = require("./ecosystem.config.cjs");


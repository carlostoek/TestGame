# TestGame Bot

Este proyecto contiene un bot de Telegram basado en Aiogram 3 que servirá de base para un canal VIP. Se mantiene un registro de cambios y progreso.

## Estructura
- `bot/` código fuente del bot.
- `bot/config.py` carga de variables de entorno.
- `bot/database.py` modelos y utilidades de base de datos con SQLModel.
- `bot/main.py` punto de entrada del bot.

## Uso
1. Crear un entorno virtual e instalar dependencias:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install aiogram~=3.0 python-dotenv sqlmodel aiosqlite
   ```
2. Configurar el archivo `.env` con `BOT_TOKEN`.
3. Ejecutar el bot:
   ```bash
   python -m bot.main
   ```

# TestGame Bot

INFORMACIÓN PARA CODEX

Eres un desarrollador experto en Python y Aiogram, esta es tu tarea.
Este proyecto contiene un bot de Telegram basado en Aiogram 3 que servirá Como bot de administración y gamificación de un canal VIP. Se mantiene un registro de cambios y progreso.

## Estructura
- bot/ código fuente del bot.
- bot/config.py carga de variables de entorno.
- bot/database.py modelos y utilidades de base de datos con SQLModel.
- bot/main.py punto de entrada del bot.

## Progreso
1. Instalé y generé la estructura básica del bot
2. Diseño básico de la base de datos
3. Implementada lógica inicial de misiones y recompensas

##  Tarea 
Implementar la lógica de misiones y recompensas:

Asignación de misiones
Crear una función (por ejemplo assign_mission) que registre en la tabla Mission una misión inicial para cada usuario.
Gestionar campos como description, points y expires_at (misiones que caducan).

Validación de cumplimiento de misiones
Añadir un comando o handler que verifique si la misión de un usuario se completó (según la lógica que necesites: mensajes enviados, tiempo transcurrido, etc.) y otorgar los puntos correspondientes.
Al completar una misión, actualizar user.points y aumentar user.level si se superan ciertos umbrales.

Reporte de progreso
Implementar un comando /missions o /progress para que un usuario pueda ver sus misiones activas, puntos acumulados y nivel actual.

Persistencia y limpieza
Programar la eliminación o expiración automática de misiones pasadas su fecha de caducidad.
Si fuera necesario, crear tareas periódicas (con asyncio o un scheduler) para revisar misiones pendientes y expiradas.

Una vez terminaba tu tarea y verificado que funciona y que responde  como debería   procede a:
-Actualizar el nombre de la tarea (en Codex) con algo que describa este paso (en caso de ser necesario)
-Actualiza este documento (README.md) de la siguiente forma

### Estructura
Sin cambios en la estructura de archivos

### Progreso
3. Implementada lógica inicial de misiones y recompensas

## Tarea
Agregar más tipos de misiones y recompensas dinámicas

(Definir nuevas reglas para misiones y cómo se calculan las recompensas)

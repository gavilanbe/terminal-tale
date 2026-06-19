# 💛 Terminal Tale
Un RPG de terminal inspirado en Undertale, con combate bullet-hell esquivando ataques con tu corazón.

## ✨ Características
- RPG por turnos con combate estilo bullet-hell: mueve tu corazón para esquivar los ataques
- Jefe con sprite expresivo que cambia de cara según el momento del combate
- Sistema de menús ACT / FIGHT al estilo Undertale, barras de HP y de ataque
- Caja de esquive con frames de invulnerabilidad tras recibir daño
- Audio generado en tiempo real (síntesis WAV) con reproducción multiplataforma
- Arte ASCII a todo color con muchos pares de color de `curses`
- Solo librería estándar de Python

## 🚀 Cómo jugar / ejecutar
```bash
python3 terminal_tale.py
```
Requiere Python 3.8+ y una terminal de al menos 80x30 con soporte Unicode.

## 🎮 Controles
- Flechas: mover el corazón en la caja de esquive / navegar menús
- `Enter` / `Espacio`: confirmar (ACT, FIGHT, opciones)
- En la fase FIGHT, sincroniza tu golpe con la barra de ataque
- `Q` / `Esc`: salir

## 🛠️ Tecnología
- Python 3.8+
- Librería `curses` (terminal)
- Síntesis de audio con `wave` + `struct` y reproducción multiplataforma (`afplay`/`aplay`/etc.)

## 📦 Parte de mi colección de juegos
Uno más de mis juegos de terminal hechos por hobby. 🎮

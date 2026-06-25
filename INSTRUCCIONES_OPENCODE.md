# Instrucciones OpenCode - Click2Folders

## Cambiar de modelo (dentro del TUI)
- Escribe `/model` y presiona Enter
- Selecciona el modelo (ej: MiMo V2.5 Free para visión + código)
- No pierdes el contexto de la conversación al cambiar

## Reconectar tras hibernación / pérdida de conexión

### Opción 1 - Dentro del TUI (sin cerrar)
1. Escribe `/compact` y Enter (a veces reestablece)
2. Si no funciona, escribe `/model`, cambia a otro modelo y vuelve al anterior

### Opción 2 - Desde otro cmd/terminal
1. Abre un nuevo cmd (Windows + R, escribe "cmd", Enter)
2. Escribe: `opencode --continue`
3. Se abrirá otra ventana TUI con el historial intacto
4. Cierra la sesión vieja

## Ver sesiones guardadas
En un cmd/terminal nuevo:
```
opencode session list
```

## Dónde se guardan las conversaciones
```
%USERPROFILE%\.local\share\opencode\project\global\storage\
```

## Exportar conversación
Dentro del TUI: escribe `/export` y se guarda como archivo Markdown.

---

# Git - Control de versiones local

## ¿Para qué sirve?
Tomar "fotos" del código cuando funciona. Si luego algo se daña, puedes volver a esa foto.

## Comandos básicos (desde cmd en la carpeta Click2folders)

### Ver el estado actual
```
git status
```

### Ver el historial de versiones (commits)
```
git log --oneline
```

### Ver qué cambió en el último commit
```
git diff
```

### Volver a la versión anterior (si algo se dañó)
Opción A - Ver archivos como estaban (sin borrar los cambios actuales):
```
git restore .
```

Opción B - Volver al último commit (descarta cambios actuales):
```
git checkout .
```

### Guardar una nueva versión después de cambios
```
git add .
git commit -m "descripción de lo que cambiaste"
```

## Nota
- Todo queda en tu PC, no necesita internet
- Git no guarda las conversaciones de opencode, solo el código
- Las conversaciones siguen en `%USERPROFILE%\.local\share\opencode\`

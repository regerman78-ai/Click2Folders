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

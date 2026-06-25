# Click2Folders - Notas de sesión opencode

---

## Sesión: 22 Jun 2026 (22:00 approx)
- **Modelo**: MiMo V2.5 Free (opencode/mimo-v2-5-free)
- **Versión código**: v1.8.49

### Último cambio registrado
- **Problema**: Texto de columna "Estado" oculto por el borde de la ventana
- **Solución**: Se redujeron los anchos de columna en `_build_queue_area()`:
  - `folder`: 680 → 480 (stretch=True)
  - `status`: 250 → 180 (stretch=False)
- **Archivo**: `click2folders.py` línea ~1207

### Cambios en esta sesión
- Se configuró sistema de backup conversacional en NOTAS_SESION.md
- El usuario solicitó mantener historial completo de cambios para retomar conversaciones tras reconexión
- Se explicaron elementos de la interfaz TUI de OpenCode

### Elementos de la interfaz TUI
- **Build** (esquina inferior izquierda): Modo de ejecución
  - Build mode: Edita archivos y ejecuta comandos
  - Plan mode: Solo sugiere cambios sin ejecutarlos
  - Se cambia con tecla Tab
- **Predeterminado/Low/Medium/High** (esquina inferior derecha): Variante del modelo
  - Controla nivel de razonamiento/esfuerzo
  - Predeterminado: Configuración normal
  - Low: Menos esfuerzo, más rápido
  - Medium: Balance velocidad/calidad
  - High: Máximo esfuerzo, más detallado
- **Engranaje (⚙️)**: Configuración del TUI
  - theme: Tema visual
  - keybinds: Atajos de teclado
  - scroll_speed: Velocidad de scroll
  - mouse: Habilitar mouse
  - attention: Notificaciones y sonidos

### Próximos pasos pendientes
- (Agregar aquí cuando se definan)

---

## Seguimiento de uso de tokens (MiMo V2.5 Free)
- **Fecha inicial**: 22 Jun 2026
- **Tokens iniciales**: 39.175 (20% de uso)
- **Costo**: $0.00 (modelo gratuito)
- **Proveedor**: OpenCode Zen

### Modelos gratuitos disponibles
- MiMo-V2.5 Free (actual)
- DeepSeek V4 Flash Free
- North Mini Code Free
- Nemotron 3 Ultra Free
- Big Pickle

### Notas importantes
- Los modelos gratuitos son "por tiempo limitado"
- No hay información oficial sobre frecuencia de reseteo de cuota
- Datos pueden ser usados para mejorar el modelo
- Si un modelo se agota, se puede cambiar a otro disponible con `/model`

### Acciones a realizar
- Monitorear reseteo de cuota (¿diario? ¿mensual?)
- Verificar en opencode.ai/auth para detalles de uso
- Investigar desinstalación de Ollama (está integrado en OpenCode Desktop)
- Cerrar OpenCode Desktop antes de desinstalar Ollama (PID 16704)

### Información importante descubierta
- El usuario tiene **OpenCode Desktop** instalado (no la versión terminal)
- Ruta: `C:\Users\Usuario\AppData\Local\Programs\@opencode-ai-desktop\`
- OpenCode Desktop incluye Ollama integrado/preconfigurado
- Para desinstalar Ollama: cerrar OpenCode Desktop primero
- Los modelos gratuitos de OpenCode Zen (MiMo, Big Pickle, etc.) NO necesitan Ollama

### Sesión anterior con Big Pickle
- **Fecha**: 19 Jun 2026 (02:10 - 02:17 UTC)
- **Modelo**: Big Pickle (opencode)
- **Sesión ID**: ses_1225b5dd6ffepI55rU45hpfVuW
- **Acciones**: Lectura y edición múltiples de click2folders.py
- **Contenido**: No disponible (solo metadatos en logs)

### Notas para usuario
- OpenCode Desktop ≠ OpenCode Terminal (son versiones diferentes)
- Si cierras OpenCode Desktop, pierdes el hilo de la conversación actual
- Al reiniciar, abre OpenCode y continua desde NOTAS_SESION.md

---

## Info del proyecto
- **Versión**: v1.8.49
- **Ruta**: `C:\Users\Usuario\Desktop\Click2folders\`
- **Ejecutable**: `dist\click2folders.exe`
- **Compilador**: Inno Setup
- **Estado**: Ceros falsos positivos en Virus Total

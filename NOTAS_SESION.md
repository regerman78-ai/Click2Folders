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

## Sesión: 27 Jun 2026
- **Modelo**: MiMo V2.5 Free
- **Versión**: v1.8.49
- **Backup código**: BAUL\click2folders_backup_27062026_v2.py

### Contexto de sesión
- Usuario: Germán Vargas
- Objetivo: Rediseñar ventana de donaciones con logos por categoría

### Cambios realizados

#### 1. Ventana de Donaciones rediseñada
- **Logos locales** en cada categoría (izquierda):
  - PayPal: `BAUL/paypal-logo.jpg`
  - Nequi: `BAUL/nequi.jpg`
  - Tether: `BAUL/Tether.png`
- **Botón PayPal**: Imagen local `BAUL/paypal_donate.gif` (clicable)
- **Enlace Nequi**: Cambiado a `https://checkout.nequi.wompi.co/method`
- **Subtítulo Nequi**: "Donaciones por Nequi:" / "Donate with Nequi:"
- **Eliminado**: Sección WhatsApp completa
- **Eliminado**: Texto "Haz click en los links para copiarlos"
- **Eliminado**: Llave Nequi (email + nombre)
- **Todo centrado** con `anchor="center"`
- **Espaciado** mejorado entre secciones

#### 2. Cambio de idioma con ventanas emergentes
- Al cambiar idioma, se cierran ventanas abiertas
- Se reabren en el nuevo idioma automáticamente
- Ventanas soportadas: Donaciones, Soporte, Tutorial

#### 3. Corrección de textos en inglés/español
- "Donaciones por Nequi:" → "Donate with Nequi:" (en inglés)
- "Developed by:" → "Desarrollado por:" (en español)

#### 4. Fix de base_path
- Cambiado de `os.getcwd()` a `os.path.dirname(os.path.abspath(__file__))`
- Soluciona problemas al ejecutar desde otra ubicación

### Logos utilizados en BAUL/
- `paypal-logo.jpg` - Logo PayPal
- `paypal_donate.gif` - Botón donar PayPal (descargado con User-Agent)
- `nequi.png` → `nequi.jpg` - Logo Nequi (renombrado por usuario)
- `Tether.png` - Logo Tether
- `logo whatsapp.png` - Logo WhatsApp (ya no se usa)

### Estado actual de la ventana Donaciones
```
┌─────────────────────────────────────────┐
│        ¡Gracias por usar...!            │
│    ¡Si te gusta el programa...!         │
│                                         │
│  [PayPal Logo]  [Botón Donar]           │
│─────────────────────────────────────────│
│  [Nequi Logo]  Donaciones por Nequi:    │
│                checkout.nequi...        │
│─────────────────────────────────────────│
│  [Tether Logo] Tether USDT (TRC20):     │
│                [QR] TFKbp...           │
│─────────────────────────────────────────│
│        ¡Gracias por tu apoyo!           │
│    Desarrollado por: Germán Vargas      │
└─────────────────────────────────────────┘
```

### Archivos de respaldo
- `BAUL\click2folders_backup_27062026.py` - Primer backup
- `BAUL\click2folders_backup_27062026_v2.py` - Segundo backup (actual)

### Git
- **Commit**: `fe7679f` - "Rediseño ventana donaciones con logos locales y cambio de idioma en ventanas"
- **Fecha**: 27 Jun 2026
- **Archivos modificados**: click2folders.py, NOTAS_SESION.md
- **Para revertir**: `git checkout fe7679f click2folders.py`

---

## Sesión: 25 Jun 2026
- **Modelo**: MiMo V2.5 Free
- **Versión**: v1.8.49
- **Commit seguridad**: f7ee1f6 (estado antes de cambios)

### Contexto de sesión
- Usuario: Germán Vargas, desarrollador de Click2Folders
- Sistema: Windows, OpenCode Desktop
- Objetivo: Rediseñar ventana de donaciones y mejorar UX

### Cambios realizados en ventana de Donaciones

#### 1. PayPal: Botón imagen clicable (COMPLETADO)
- **Antes**: Label con correo `regerman78@gmail.com` que copiaba al portapapeles
- **Ahora**: Botón imagen clicable que abre página de donaciones
- **URL destino**: https://www.paypal.com/donate?hosted_button_id=JMPWGD5VA32UW
- **Imagen**: https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif
- **Implementación**: 
  - Función `_display_paypal_btn()` muestra la imagen
  - Función `_load_paypal_thread()` carga la imagen desde URL
  - Hilo secundario para no bloquear la UI
  - Click abre `webbrowser.open()` con URL de donación

#### 2. Nequi: Enlace de pago agregado (COMPLETADO)
- **Sección mantuvo**: Correo `regerman78@gmail.com` + "Red*** Var***"
- **Nuevo**: Enlace de pago Nequi
- **URL**: https://checkout.nequi.wompi.co/l/EYGaPV
- **Subtítulo**: "Donar con Nequi:"
- **Implementación**:
  - Label clickeable azul con el enlace
  - Click abre `webbrowser.open()` con URL de Nequi

#### 3. Texto eliminado (COMPLETADO)
- **Eliminado**: "Haz click en los links para copiarlos"
- Razón: Ya no es necesario因为 ahora hay botones clickeables

#### 4. Botón "Quitar Carpetas" (COMPLETADO)
- **Cambiado a**: "Quitar Carpetas Seleccionadas"
- **Líneas modificadas**: 1057, 1283, 1565
- **Versión inglés**: "Remove selected folders"

### Método de carga asíncrona de imágenes
- Se usa `threading.Thread` para cargar imágenes desde URL
- `_load_paypal_thread()` carga el botón de PayPal
- `_display_paypal_btn()` muestra la imagen en el contenedor
- `self.after(0, ...)` ejecuta la actualización en el hilo principal
- Patrón similar al ya existente para QR de USDT

### Solución a problema de PyInstaller
- **Problema**: PyInstaller no incluía carpetas adicionales en la compilación
- **Solución temporal**: Usar URLs en lugar de archivos locales
- **Para futuras imágenes**: Agregar al `.spec` en `datas` o usar URLs

### Git y respaldo
- **Commit de seguridad**: f7ee1f6 (estado antes de cambios)
- **Para revertir**: "Revierte al commit f7ee1f6"
- **Historial**: Se mantiene en NOTAS_SESION.md

### Notas importantes para futuras sesiones
- El usuario prefiere soluciones locales sobre dependencias de internet
- Siempre preguntar antes de modificar código (modo plan)
- Compilar después de cada cambio significativo
- El `.exe` no se actualiza automáticamente al modificar `.py`
- PyInstaller requiere configuración especial para incluir archivos

### Estado actual de la ventana Donaciones
```
┌─────────────────────────────────────────┐
│        ¡Gracias por usar...!            │
│    ¡Si te gusta el programa...!         │
│                                         │
│           Paypal:                       │
│    [ BOTÓN DONAR PAYPAL IMG ]           │
│─────────────────────────────────────────│
│    Llave Nequi Colombia:                │
│       regerman78@gmail.com              │
│         Red*** Var***                   │
│        Donar con Nequi:                 │
│   https://checkout.nequi.wompi.co/...   │
│─────────────────────────────────────────│
│       Tether USDT (TRC20):              │
│       TFKbp...                          │
│─────────────────────────────────────────│
│    Whatsapp Desarrollador Germán        │
│       https://bit.ly/...                │
└─────────────────────────────────────────┘
```

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

### Cómo retomar después de reiniciar
Dime algo como:
> "Abre NOTAS_SESION.md y retoma la sesión del 25 Jun 2026. Estábamos trabajando en la ventana de donaciones de Click2Folders."

### Comandos útiles para revertir
- "Revierte todos los cambios al último commit"
- "Revierte el archivo click2folders.py al último commit"
- "Revierte al commit f7ee1f6"

---

## Info del proyecto
- **Versión**: v1.8.49
- **Ruta**: `C:\Users\Usuario\Desktop\Click2folders\`
- **Ejecutable**: `dist\click2folders.exe`
- **Compilador**: Inno Setup
- **Estado**: Ceros falsos positivos en Virus Total

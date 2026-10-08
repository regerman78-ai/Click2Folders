# NOTAS DE SESIÓN - Click2Folders (Sesión con OpenCode)

## Fecha: 15-16-17-19-21-23-24/09/2026

---

## Cambios 24-25/09/2026 (v1.10.14 → v1.10.18)

### 1. Botón "Actualización" (Update)
- Botón rojo al final del toolbar (Tutorial → Soporte → Traducir → Donaciones → Actualización)
- Abre la página de releases de GitHub: `https://github.com/regerman78-ai/Click2Folders/releases`

### 2. Auto-check de actualizaciones
- Al iniciar, verifica GitHub API si hay nueva versión (una vez por sesión)
- Si hay actualización disponible, muestra popup con opciones "Descargar" / "Después"
- Si toca donaciones (conteo par): donaciones primero → después actualizaciones
- Si no toca donaciones: actualización directa

### 3. Constantes GitHub
- `GITHUB_REPO = "regerman78-ai/Click2Folders"`
- `GITHUB_URL`, `GITHUB_RELEASES_URL`, `GITHUB_API_URL`

### 4. Tutorial actualizado
- Nueva sección "Actualización / Update" en ambos idiomas
- Explica el botón y el auto-check automático

### 5. Emoji en ventana de donaciones
- Emoji (smiling face double thumbs up) a la derecha de "¡Gracias por tu apoyo!"
- Tamaño: 80x80px
- "Desarrollado por: Germán Vargas" centrado debajo
- Copyright centrado al final

### 6. Orden de botones del toolbar
- Tutorial → Soporte → Traducir → Donaciones → Actualización

### 7. Bug fix: popup de finalización bloquea ventana principal
- Eliminado `popup.grab_set()` de `_show_completion_dialog` y `_show_restored_popup`
- Antes: si no se hacía click en OK, la ventana principal quedaba inaccesible
- Ahora: el popup no bloquea la interacción con la ventana principal

### 11. Versión v1.10.18
- Fix: traducción columna contenido "Archivos en total" ↔ "Total files" en inglés
- Fix: columna estado texto visible (ancho aumentado a 130px)
- Fix: timer no se reinicia al cambiar idioma (preserva tiempo transcurrido)

---

## Pendiente
- **InnoSetup**: Convertir exe portátil a instalador
- **Screenshots**: Subir capturas de la interfaz al repo
- **Release v1.10.7**: Crear release con el instalador

---

## Cambios 22/09/2026 (v1.10.2 → v1.10.3)

### 1. Icono actualizado
- Reemplazado `favicon.ico` con `Logo-Final.ico` de `BAUL/Logo Click2Folders/`
- Afecta ventana principal y barra de tareas

### 2. Log resumen final
- Después de organizar todas las carpetas, se muestra un RESUMEN FINAL en el log
- Incluye: archivos sin fecha por carpeta, carpetas creadas por carpeta
- Totales generales y fecha/hora final

### 3. Columna Contenido después de organizar: archivos sin fecha
- Después de organizar, la columna muestra "X carpetas / Y archivos sin fecha" en vez de "Archivos en total"
- `_organize_dirs_created` rastrea carpetas creadas reales por carpeta

### 4. Log: scroll al RESUMEN FINAL
- `_log_summary()` busca el marker "RESUMEN FINAL" y hace scroll ahí

### 5. Tooltip ruta completa en columna Carpeta
- Hover sobre columna Carpeta muestra ruta completa en tooltip oscuro
- `_tree_folder_tooltip` destruido al salir del área o cambiar de columna
- Binding `<Motion>` y `<Leave>` en el tree

### 6. Columna Contenido reducida
- 320px → 280px → 250px (minwidth 200px), texto completo visible

### 7. Conteo de carpetas incluye año
- `year_dir` ahora se cuenta como carpeta creada (antes solo se contaba `month_dir`)

### 8. Tutorial actualizado
- Columna Contenido: explica behavior antes/después de organizar (ES/EN)

### 9. Icono .ico regenerado con Pillow
- Todos los tamaños: 16, 32, 48, 64, 128, 256 px
- Desde Logo Final.png (1038x1024, RGBA)

### 10. Popup "sin carpetas" con estilo neoformism
- Cambiado de `messagebox.showinfo` a `_show_modern_popup`

### 11. Botones "Agregar varias carpetas" corregidos
- Orden: "Seleccionar todo" primero, "Deseleccionar todo" segundo (como ventana principal)
- Texto: "todo/todas" en vez de "todas"

### 12. RESUMEN FINAL siempre visible
- Ahora posiciona la línea "RESUMEN FINAL" en la primera línea visible del log

---

## Cambios 19/09/2026 (v1.9.1 → v1.9.2)

### 1. Columna Cantidad: se actualiza después de organizar
- Después de organizar, se recalculan carpetas/archivos y se actualiza la columna
- Ya no queda con la información del comienzo

### 2. Redimensionamiento de columnas: fix completo
- Causa raíz: carpeta tenía `stretch=True`, causaba movimiento invertido al arrastrar
- Solución: todas las columnas ahora tienen `stretch=False`
- `on_tree_click` protegido para no interferir con resize en borde Sel/Carpeta
- `_ColumnResizer` reescrito con lógica simple: cada borde ajusta su columna

### 3. Ancho columna Cantidad ampliado
- 250px → 280px para mostrar texto completo

### 4. Espacio en blanco eliminado
- Todas las columnas `stretch=False`
- `_fit_folder()` calcula ancho de Carpeta = `treeview_width - sel - cantidad - status` (offset 0)
- Se ejecuta en `<Configure>` (resize ventana) + `after(50, ...)` tras `deiconify`
- Retry si `winfo_width() <= 10` (reintenta a los 50ms)
- **Durante drag, NO ejecuta `_fit_folder`** (verifica `_drag_col`)

### 5. Borde derecho de Estado fijo al treeview
- `_on_drag()` ajusta `status = start_status - dx` en CUALQUIER borde
- Esto mantiene el borde derecho de Estado siempre fijo al treeview
- Left edge de Sel también fijo (por diseño)

### 6. Layout Treeview optimizado
- `("Treeview.treearea", {"sticky": "nswe"})` elimina padding interno
- Esto permite que `winfo_width()` = ancho exacto del área de columnas

---

## Pendiente
- **Incrementar versión con cada cambio significativo** — v1.9.1 debió subir a v1.9.2, v1.9.3, etc. con cada fix

---

## Cambios 17/09/2026 (v1.9.0 → v1.9.1)

### 1. Tutorial: limpieza de texto
- Eliminado punto 4 "La columna 'Cantidad'..." de "¿Cómo usar el programa?"
- Eliminado bloque de texto sobre "Las subcarpetas de cada mes..." de "¿Qué hace el programa?"

### 2. Log: línea separadora en timestamp final
- Línea `====` superior agregada al timestamp de fin

### 3. Columnas: redimensionables y persistentes
- `_ColumnResizer` restaurado sin Canvas (solo eventos en treeview)
- Ancho de columna persiste al ajustar manualmente

### 4. Columna Cantidad: más ancha
- Ampliada a 250px para mostrar texto completo

### 5. Backup v1.9.1 creado

---

## Cambios 17/09/2026 (v1.8.49 → v1.9.0)

### 1. Columna "Cantidad" agregada
- Nueva columna entre Carpeta y Estado mostrando carpetas/archivos por carpeta
- Formato: "5 carpetas / 1969 archivos"
- Se actualiza después de organizar y deshacer

### 2. Columna Estado simplificada
- Solo muestra: "Organizado", "Sin organizar" (y estados intermedios)
- Eliminado texto "para organizar" después de deshacer

### 3. Tutorial actualizado
- Sección "¿Qué hace el programa?" reescrita con los 4 modos en negrilla
- Texto subrayado con `__...__` soportado en rendering del tutorial
- Checkbox text: "No poner número de mes" (antes "No anteponer...")
- Sección "Cómo usar": 4 pasos con explicación de columna Cantidad
- Sección "Información adicional": descripción de Columna Cantidad y Estado

### 4. Popup de restaurar
- Ahora usa `tk.Label` con `font=("Segoe UI", 12, "bold")` igual que popup "finalizado"

### 5. Persistencia contador de donaciones
- Archivo en `os.path.expanduser("~")` en vez de `tempfile.gettempdir()`

### 6. Bug fix combo dropdown
- `configure(values=...)` + `set(...)` para evitar duplicados

---

## Cambios 16/09/2026

### 1. Título de ventana
- Cambiado a "Organizador Cronológico de Fotos y Video"
- Constante `WINDOW_TITLE` + `_toggle_lang` + encabezado del tutorial

### 2. Título del tutorial
- "¿Qué fechas detecta?" → "¿Qué fechas detecta el programa?"

### 3. Log y contadores se resetean al agregar carpetas
- `_clear_log()` + `_reset_counters()` en `_add_single_folder` y `do_add`

### 4. Seleccionar todo / Deseleccionar todo
- Validación `tree.exists(iid)`, limpieza de IDs obsoletos en `_clear_placeholder_rows`

### 5. Posición de ventana tutorial
- `toolbar_offset` aumentado de 100 a 130

### 6. Bug del combo dropdown
- `self.mode_combo.configure(values=new_values)` + `self.mode_combo.set(new_text)`

### 7. Persistencia del contador de donaciones
- Archivo cambiado de `tempfile.gettempdir()` a `os.path.expanduser("~")`
- Donaciones solo en launches pares: `count > 1 and count % 2 == 0`

### 8. Ventana de donaciones
- Altura reducida: `minsize(440, 420)`, padding reducido

### 9. Botón de idioma
- "Modo Ingles" → "Translate to English" (ES)
- "Spanish Style" → "Traducir al Español" (EN)

### 10. Label de estado eliminado del btn_frame
- Widget dummy oculto mantenido para referencias internas

### 11. Popup de restaurar con estilo neoformism
- `_show_restored_popup` ahora usa `ctk.CTkFrame` + `ctk.CTkLabel` + `ctk.CTkButton`
- Sin icono de círculo azul

---

## Resumen de Cambios Realizados

### 1. Rediseño UI Neoformism (CustomTkinter)
- Cambio de `ttk` a `customtkinter` (CTk) para botones, frames, labels, scrollbars
- Ventana principal cambió de `ctk.CTk` a `tk.Tk` con widgets CTk
- Colores: toolbar `#e8eef5`, botones azul/verde/naranja/púrpura
- Treeview con estilo neoformismo (clam theme, headers azules)
- Progress bar CTk con `set(X/100)` en vez de `configure(value=X)`
- Barra de contadores movida antes del log area con `side="bottom"`

### 2. Ventana de Donaciones
- Sección WhatsApp eliminada definitivamente
- Logo Nequi clickeable (abre enlace de donación)
- Dirección USDT clickeable para copiar al portapapeles
- Texto "Haz click en la dirección para copiarla" debajo de Tether
- Donaciones solo en lanzamientos pares (`count >= 2 and count % 2 == 0`)
- Texto cambiado: "Click2Folders es libre y no tiene molestos anuncios"
- Texto final: "¡Considera donar para que siga siendo así!" (bold)
- Ventana de donaciones se abre directamente (sin `withdraw/deiconify`)
- Outer frames: `fg_color="#e8eef5"` (mismo color del fondo)
- Inner content: `bg="white"` con padding `pady=8, padx=8`
- Contenido centrado con frame intermedio `pack(anchor="center")`
- Separadores con `fg_color="#e8eef5"` para ser invisibles
- Botón "Modo Idioma": fix bug que reabría ventanas cerradas (usar `.exists()` en vez de `.win`)

### 3. Botón "Deshacer organización"
- Siempre habilitado excepto durante procesamiento
- Si no hay carpetas cargadas, muestra popup: "No hay carpetas cargadas para deshacer. Agrega una carpeta primero."

### 4. Mensaje "Por favor espere..."
- Movido al header del log area (junto a "Organizando Carpeta:")
- Label `lbl_wait` centrado con frame contenedor `fill="x", expand=True`
- Parpadeo continuo de 3 puntos suspensivos con `animate_wait()`
- Se limpia cuando termina el procesamiento

### 5. Treeview con líneas divisorias
- Agregadas 6 filas placeholder vacías al iniciar (`_add_placeholder_rows()`)
- Estilo: `borderwidth=1, relief="solid"`
- Se limpian al agregar carpetas reales (`_clear_placeholder_rows()`)
- Se vuelven a crear cuando se quitan todas las carpetas

### 6. Popup "Agregar varias carpetas"
- Texto ejemplo eliminado: "Ej: carpeta 'Fotos' con subcarpetas..."
- Solo queda el texto principal de instrucciones

### 7. Texto de aviso de modos
- Cambiado: "Si no encuentra fecha..." → "Si el programa no encuentra fecha en ninguna de las 3 opciones..."

### 8. Cursor manito en Tutorial
- Agregado `cursor="hand2"` al frame header, flecha y título de cada sección

### 9. Ajustes de geometría
- Ventana principal: `900x620`, `minsize(900, 620)`
- Altura aumentada desde arriba sin mover la barra inferior
- Padding reducido: toolbar (5,3), opciones (3), cola (3), progreso (5,3), log (3)

---

## Archivos Modificados
- `click2folders.py` - Archivo principal (todos los cambios)
- `click2folders.spec` - Actualizado con `('Baul', 'Baul')` en datas
- `compilar.bat` - Auto-instala customtkinter si falta

## Backup
- `Backcup OpenCode/click2folders_backup_pre_neoformism.py` - Backup antes del rediseño neoformism
- `Backcup OpenCode/click2folders_backup_v1.9.0.py` - Backup v1.9.0
- `Backcup OpenCode/click2folders_backup_v1.9.1.py` - Backup v1.9.1
- `Backcup OpenCode/click2folders_backup_v1.9.1_complete.py` - Backup v1.9.1 completo (19/09/2026, con todos los fixes de columnas)

## Dependencias
- `customtkinter==5.2.2`
- `psutil`
- `Pillow` (para imágenes)
- `darkdetect`

## Compilación
- PyInstaller con `.spec`
- VirusTotal: 4/70 falsos positivos (PyInstaller)
- v1.1 logró 0/71 con Inno Setup installer

---

## Cambios 25/09/2026 (v1.10.18 → v1.10.19)

### 1. Columna "Contenido" más ancha
- Ancho de columna aumentado: 350px → 450px (minwidth 300 → 400)
- Texto ahora se muestra completo: "19 carpetas / 1925 archivos organizados / 44 sin fecha"
- Ya no se corta el texto de la columna

### Archivos
- `click2folders.py` - Línea 1673: ancho de columna "cantidad"
- `Backup Claude/v1.10.19/` - .py + .exe compilado

---

## Cambios 25/09/2026 (v1.10.19 → v1.10.20)

### 1. Ventana de Soporte simplificada
- Título ajustado a 2 líneas con salto de línea (\n) para que no sea tan ancho
- "Contáctanos" → "¡Escríbenos!" con fuente bold 14
- Correo aumentado a fuente 15 (antes 13), mantiene click para copiar
- Eliminado "Desarrollado por: Germán Vargas" y copyright

### 2. Fix: imágenes donaciones (BAUL)
- El spec file tenía `datas=[]` (se perdió en compilación anterior)
- Restaurado `datas=[('BAUL', 'BAUL')]` para incluir imágenes en el exe
- PayPal, Nequi, Tether y Emoji ahora se ven correctamente en el exe compilado

### 3. Columna "Contenido" (de v1.10.19)
- Ancho 350px → 450px

### Archivos
- `click2folders.py` - Línea 1673 (columna), on_support(), versión
- `click2folders.spec` - datas=[('BAUL', 'BAUL')]
- `installer.iss` - v1.10.20
- `Backup Claude/v1.10.20/` - .py + .exe + installer

---

## Cambios 25/09/2026 (v1.10.21 → v1.10.22)

**Base limpia: v1.10.21 + 5 fixes + recompilación.**

### 1. Bumping versión a v1.10.22
- Recompilación con PyInstaller tras matar proceso previo
- Actualizados installer.iss, click2folders.spec, click2folders.py

### 2. Diagnóstico traducción
- `_toggle_lang` envuelta en `try/except` que escribe errores en `lang_error.txt`
- Permite identificar excepciones silenciosas que impiden la traducción

### 3. Fix icono principal/taskbar
- `safe_icon()` usa `iconbitmap(default=...)` + `tk.PhotoImage()` como fallback
- `favicon.ico` incluido en `datas` del spec file para que esté disponible en `_MEIPASS`

### 4. Fix `_fit_folder` robusto
- Se cambió `tkfont.Font(font=self.tree["font"])` por `tkfont.Font(family="Segoe UI", size=11)` fijo
- Se agrega verificación `fnt is not None` antes de medir texto

### 5. Se removió `self.after(200, self._fit_folder)` de `_toggle_lang`
- Para evitar interferencia con el renderizado del árbol al cambiar idioma
- `_fit_folder` se llama solo tras agregar, organizar, deshacer y al redimensionar

### Archivos
- `click2folders.py` - v1.10.22
- `click2folders.spec` - datas con favicon.ico incluido
- `installer.iss` - v1.10.22
- `Backup Claude/v1.10.22/` - .py + spec + iss

---

## Cambios 25/09/2026 (v1.10.18 → v1.10.21)

**Base limpia: v1.10.18. Solo 4 cambios puntuales.**

### 1. Fix: icono ventanas auxiliares (Soporte)
- `safe_icon()` se llamaba DESPUÉS de `deiconify()` en la ventana de Soporte — el icono no se mostraba
- Ahora `safe_icon(w)` se llama ANTES de `deiconify()`, como en todas las demás ventanas

### 2. Columna "Contenido" auto-adaptable al contenido
- `_fit_folder` ahora mide el texto más largo de la columna con `tkinter.font.Font.measure()`
- Ancho mínimo: 300px. Máximo: 500px. Se expande automáticamente según contenido
- Se recalcula al agregar carpetas, organizar, deshacer, cambiar idioma y redimensionar ventana

### 3. Traducción de columna Contenido + Log al cambiar idioma
- Se removió la condición `if new_cant != current_cant` y `if new_log != current_log` — ahora siempre ejecuta `tree.set()` y reemplaza el texto del log para forzar actualización
- Se agrega `str()` para asegurar que los values se lean como string
- Se removió `self.after(200, self._fit_folder)` de `_toggle_lang` para evitar interferencia con el renderizado del árbol
- `_fit_folder` se llama solo tras agregar, organizar, deshacer y al redimensionar

### 4. Ventana de Soporte simplificada
- Título en 2 líneas con `\n` (fuente 15 bold) para reducir ancho
- Emoji 👇 amarillo (punto de mano señalando hacia abajo)
- "¡Escríbenos!" (bold 14)
- Correo: fuente **15** (antes 13), mantiene click-to-copy
- Eliminado "Desarrollado por: Germán Vargas" y copyright

### 5. Fix: icono principal y barra de tareas
- `safe_icon()` ahora usa `iconbitmap(default=...)` + `iconphoto()` como fallback
- `favicon.ico` agregado a `datas` del spec file para que esté disponible en `_MEIPASS` al ejecutar

### Fix: `_fit_folder` robusto
- Se cambió `tkfont.Font(font=self.tree["font"])` por `tkfont.Font(family="Segoe UI", size=11)` para evitar fallos con ttk.Treeview
- Se agrega verificación `fnt is not None` antes de medir texto

### Archivos
- `click2folders.py` - v1.10.21 (base v1.10.18 + 5 fixes)
- `click2folders.spec` - datas con favicon.ico incluido
- `installer.iss` - v1.10.21
- `Backup Claude/v1.10.21/` - .py + spec + iss

---

## v1.10.23 � 26/09/2026 � Debug traducci�n + fix iconos PIL

### 1. Debug de _toggle_lang a archivo
- Se elimin� messagebox.showinfo("DEBUG",...) que bloqueaba la ejecuci�n
- Se agreg� logging detallado a lang_debug.txt con: english_mode antes/despu�s, cantidad de children del tree, values de cada item, valores antes/despu�s de traducci�n, longitud del log, si cambi�, y errores
- Se elimina lang_error.txt (ya no se usa), ahora todo va a lang_debug.txt

### 2. Fix iconos con PIL
- safe_icon() ahora usa PIL.Image.open() + ImageTk.PhotoImage() en lugar de 	k.PhotoImage() que no puede leer .ico
- Se agrega win._icon_ref = photo para evitar garbage collection
- Fallback a 	k.PhotoImage si PIL no est� disponible

### Archivos
- click2folders.py - v1.10.23
- installer.iss - v1.10.23
- Backup Claude/v1.10.23/ - .py + spec + iss + exe

---

## v1.10.24 � 27/09/2026 � Fix traducci�n (TypeError ra�z) + centrado + parpadeo ventanas

### 1. Fix CR�TICO: traducci�n columna Contenido y log
- **Causa ra�z encontrada**: _toggle_lang l�nea ~1448 hac�a datetime.now() - self.start_time pero start_time es un loat (de 	ime.time()) ? **TypeError** ? saltaba al except ? la traducci�n del �rbol y log (que est�n DESPU�S en el flujo) **nunca se ejecutaba**
- Por eso botones/encabezados S� cambiaban (est�n ANTES del error) pero columna Contenido, Estado y log NO
- Fix: elapsed = time.time() - self.start_time
- Fix adicional: _translate_log_text ten�a las frases gen�ricas (rchivos organizados, sin fecha, carpetas creadas) ANTES que las espec�ficas (Total de archivos organizados:) ? texto quedaba mezclado. Reordenadas las frases espec�ficas primero
- Debug lang_debug.txt ahora se escribe junto al exe (sys.executable) cuando est� congelado (antes iba a la carpeta temp de PyInstaller)

### 2. Fix: ventanas emergentes siempre centradas en pantalla
- center_window() reescrito: siempre centra en pantalla (ignora parent), y usa winfo_reqwidth()/winfo_reqheight() cuando winfo_width() retorna 1 (ventanas withdrawn)
- Ventana Donaciones: c�digo inline de centrado reemplazado por center_window(w) (antes usaba winfo_width()=1 ? sal�a desplazada a la derecha/abajo)

### 3. Fix: parpadeo de ventana peque�a al lado izquierdo al hacer click
- **Causa**: varios popups creaban 	k.Toplevel SIN withdraw() ? aparec�an en posici�n default (esquina superior izquierda) antes de centrarse
- Agregado popup.withdraw() inmediatamente tras crear + popup.deiconify() tras centrar en: _show_update_popup, _show_modern_popup, intro m�ltiples carpetas, selecci�n requerida (organizar/deshacer), _show_tip_with_action, _show_completion_dialog, _show_restored_popup, _show_confirm_dialog, _open_overlay
- Verificados los 16 pares withdraw/deiconify

### Archivos
- click2folders.py - v1.10.24
- installer.iss - v1.10.24
- Backup Claude/v1.10.24/ - .py + spec + iss + exe

---

## v1.10.25 - 27/09/2026 - Fix parpadeo persistente + centrado residual (Donaciones/Soporte)

### 1. Fix parpadeo: causa real = safe_icon ANTES de withdraw
- En v1.10.24 se agregó withdraw() a muchas ventanas, pero en Donaciones, Tutorial y Selección de carpetas el withdraw quedaba DESPUÉS de safe_icon() (lectura PIL de icono = ~10-50ms con ventana ya visible) → parpadeo persistente
- Evidencia: Soporte NO parpadea porque hace withdraw() antes de safe_icon; Donaciones/Tutorial SÍ parpadeaban
- Fix: withdraw() ahora es la PRIMERA instrucción tras tk.Toplevel() en: on_tutorial, _do_on_donate, on_support, selección de carpetas (win), _show_image_window
- Verificado con grep: las 16 ventanas con safe_icon ahora tienen withdraw() antes de safe_icon; solo quedan 4 tooltips overrideredirect sin withdraw (correctos, pequeños junto al cursor)

### 2. Fix centrado residual: re-centrado diferido tras mapear
- Causa: winfo_reqwidth() de una ventana withdrawn puede sobreestimar el tamaño real (CTk renderiza al mapear) → x calculado con ancho mayor → ventana aparece a la IZQUIEDA del centro
- center_window() ahora agenda _recenter_window(win) con win.after(100, ...) que recalcula con el tamaño REAL (winfo_width) una vez la ventana está mapeada, corrigiendo la posición
- _recenter_window valida winfo_exists() para ventanas destruidas en los 100ms
- Afecta a: Donaciones, Soporte, imagen, overlay, popups — todos pasan por center_window()

### Archivos
- click2folders.py - v1.10.25
- installer.iss - v1.10.25
- Backup Claude/v1.10.25/ - .py + spec + iss + exe

---

## v1.10.26 - 28/09/2026 - Fix salto de ventanas al centrarse + nombres descriptivos de salida

### 1. Fix CRÍTICO: ventanas abrían "en otra parte" y luego saltaban al centro
- **Causa raíz (descubierta con instrumentación)**: una ventana oculta (withdrawn) reporta `winfo_width() = 200x200` (tamaño por defecto de Tk), **no 1** — por eso el fallback a `reqwidth` nunca se activaba y el PRIMER centrado usaba 200x200
- A los 100ms el re-centrado calculaba con el tamaño real → **salto visible**:
  - Soporte: (583,284) → (533,275)
  - Donaciones: (583,284) → (463,115) — 169px hacia arriba ("abría abajo y luego centraba")
  - Confirmar deshacer: (583,284) → (516,328)
- **Fix**: `center_window()` ahora detecta `state() == 'withdrawn'` y mide `winfo_reqwidth()/reqheight()` + **minsize** (parse con regex porque `wm minsize` devuelve `(440, 420)`) → la primera posición ya es la correcta
- El re-centrado a 100ms se mantiene como seguridad, pero con la medida correcta calcula la misma posición ⇒ **cero salto**
- **Verificado con arnés de instrumentación** (muestreo 0-900ms): Soporte, Donaciones y Confirmar deshacer mantienen posición idéntica en todas las muestras

### 2. Nombres descriptivos de los archivos de salida (portable + instalador)
- Portable: `dist\Click2Folders-Portable-v1.10.26.exe`
- Instalador: `installer\Click2Folders-Instalador-v1.10.26.exe`
- installer.iss: `Source` apunta al portable versionado (con `DestName: click2folders.exe` para que el instalado conserve su nombre interno) y `OutputBaseFilename=Click2Folders-Instalador-v1.10.26`
- **Orden de compilación**: pyinstaller → renombrar portable → ISCC

### Archivos
- click2folders.py - v1.10.26
- installer.iss - v1.10.26
- dist\Click2Folders-Portable-v1.10.26.exe
- installer\Click2Folders-Instalador-v1.10.26.exe
- Backup Claude/v1.10.26/ - .py + spec + iss + portable + instalador

---

## v1.10.27 - 28/09/2026 - Traducciones pendientes + columnas sin texto oculto + single-instance robusto

### 1. Mensaje naranja "Por favor espere..." ahora se traduce en caliente
- **Causa**: el texto se guardaba en un closure al iniciar la organización; si el usuario cambiaba de idioma mientras trabajaba, el mensaje seguía en el idioma inicial
- Fix: `status_text(msg, english)` con pares ES/EN (`_STATUS_PAIRS`) se resuelve **en cada tick** de la animación (cada 300ms) y al fijar el estado ⇒ siempre coincide con el idioma actual
- Aplica a: "Por favor espere/Please wait" y "Deshaciendo organización.../Undoing organization..."

### 2. Columnas del árbol: el texto nunca queda oculto
- **Causa**: `_fit_folder` tenía un tope de 500px para la columna Contenido (`min(max_cant_w, 500)`) y forzaba que las 4 columnas sumaran exactamente el ancho visible ⇒ texto largo se cortaba
- Fix: medición **sin tope** de Contenido y Estado (y de los encabezados, que cambian con el idioma); Carpeta ocupa el resto (mín. 200)
- **Nueva barra horizontal**: si la suma de columnas excede el ancho visible, aparece una scrollbar horizontal (oculta cuando no hace falta) para alcanzar cualquier resto
- Se re-ajusta al terminar de traducir los valores en `_toggle_lang`

### 3. Soporte: "¡Escríbenos!" traducido
- Ambas ramas del ternario eran idénticas ⇒ ahora "Write to us!" en inglés

### 4. Popup "Quitar Carpetas Seleccionadas" traducido
- `_show_modern_popup("Marca con ☑ ...")` no tenía traducción ⇒ ahora "Check ☑ the folders you want to remove from the list."

### 5. Single-instance robusto (mutex de Windows)
- **Antes**: archivo PID temporal + `tasklist` — propenso a fallos (permisos, PID reutilizados, títulos que cambian con el idioma) y con fallback que creaba una segunda instancia en cualquier error
- **Ahora**: mutex nombrado de Windows (`CreateMutexW`) — se libera solo al cerrar el proceso, sin archivos obsoletos; si ya existe instancia ⇒ `EnumWindows` busca la ventana principal **por prefijo "Click2Folders"** (funciona en español e inglés) y la trae al frente (`SW_RESTORE` + `SetForegroundWindow` con truco de tecla Alt si Windows bloquea el foreground) ⇒ la 2ª instancia sale sin abrir nada
- **Probado**: 2º lanzamiento termina solo (`HasExited=True`), queda 1 sola instancia activa

### Archivos
- click2folders.py - v1.10.27
- installer.iss - v1.10.27
- dist\Click2Folders-Portable-v1.10.27.exe
- installer\Click2Folders-Instalador-v1.10.27.exe
- Backup Claude/v1.10.27/ - .py + spec + iss + portable + instalador

---

## v1.10.28 - 28/09/2026 - Popups modales se traducen en caliente + "¡Write to us!"

### 1. Popups abiertos ahora se actualizan al pulsar Traducir
- **Antes**: solo Soporte/Donaciones/Tutorial se reabrían al cambiar de idioma; los popups modales (Aviso, Selección requerida, fin de organización, restaurado, confirmar deshacer, actualización disponible) conservaban el texto con el que se crearon
- **Ahora**: registro `self._live_popups` — cada popup modal registra sus widgets con pares (ES/EN) al crearse y se des-registra solo al cerrarse (`<Destroy>`); en `_toggle_lang` se recorren los vivos y se re-escriben título + textos al nuevo idioma (sin cerrar/reabrir, sin perder estado)
- `_show_modern_popup` ahora acepta **tupla (es, en)** además de texto plano

### 2. "Deshacer organización" sin carpetas: texto en inglés real
- **Causa**: ambas ramas del ternario eran idénticas (español) — el popup "No hay carpetas cargadas para deshacer..." salía en español aunque la UI estuviera en inglés
- Ahora: "There are no folders loaded to undo. Add a folder first."

### 3. Soporte: signo de admiración inicial
- "Write to us!" → "¡Write to us!" (consistente con "¡Escríbenos!")

### 4. Confirmación de deshacer con mensaje bilingüe
- El `msg` que construía `on_undo` era un f-string elegido al momento; ahora pasa tupla (es, en) y se traduce en caliente igual que el resto

### Verificación
- py_compile OK
- Test runtime (14 checks): texto/título/botón del popup Aviso, fin de organización, deshacer sin carpetas, confirmación con toggle durante wait_window, registro limpio al cerrar — TODO PASS
- Portable compilado; title bar en runtime: "Click2Folders - Organizador Cronológico de Fotos y Videos v1.10.28"; 2do lanzamiento sale solo (mutex OK)

### Archivos
- click2folders.py - v1.10.28
- installer.iss - v1.10.28
- dist\Click2Folders-Portable-v1.10.28.exe
- installer\Click2Folders-Instalador-v1.10.28.exe
- Backup Claude/v1.10.28/ - .py + spec + iss + NOTAS_SESION + portable + instalador

---

## v1.10.29 - 29/09/2026 - Footer con total de organizados + log sin RESUMEN por carpeta

### 1. Footer: nuevos contadores (barra inferior)
- "Archivos analizados: x" → **"Total de archivos organizados: x"**
- "Carpetas creadas: x" → **"Total de carpetas creadas: x"**
- "Tiempo transcurrido" queda igual
- **Valor real de organizados**: nuevo contador acumulado `self.total_organized` (se incrementa al mover cada archivo en `_organize_folder`, se inicializa en `__init__` y se resetea en `_reset_counters`); NO incluye los archivos sin fecha (que se omiten), por lo que el footer ahora es coherente con el total del log (ej. 6952 organizados ≠ 7064 analizados)
- Las 3 zonas que muestran el footer quedan sincronizadas: construcción inicial (`_build_counters_bar`), actualización en vivo (`_refresh_counters`) y cambio de idioma (`_toggle_lang`); etiquetas en EN igual a las del log: "Total files organized:" / "Total folders created:"

### 2. Log: eliminado el RESUMEN FINAL por carpeta
- **Eliminado** (duplicaba la columna Contenido): encabezado "RESUMEN FINAL"/"FINAL SUMMARY" con sus separadores y las líneas por carpeta "Nombre: X archivos organizados, Y sin fecha, Z carpetas creadas"
- **Se conserva** el bloque final igual que en las capturas:
  ```
  ============================================================
    Total de archivos organizados: 6952
    Total de archivos sin fecha detectable: 112
    Total de carpetas creadas: 71
  ============================================================
    Fecha/hora final: 29/09/2026 10:37:39
  ============================================================
  ```
- `_log_summary`: el marker de scroll ahora busca "Total de archivos organizados:" (antes "RESUMEN FINAL", que ya no existe) para mantener el desplazamiento automático al resumen
- Pares de traducción del log se mantienen (ayudan a traducir logs históricos)

### 3. Tutorial actualizado (coherencia)
- Descripción del footer: "total de archivos organizados, total de carpetas creadas" (ES/EN)
- Descripción de la columna Contenido: "'X carpetas / Y archivos organizados / Z sin fecha'" (ES/EN) — antes decía solo "X carpetas / Y archivos sin fecha"

### Verificación
- py_compile OK
- **Test end-to-end** (12 checks, TODO PASS): organización real de 6 archivos en carpeta temporal con mainloop — footer con total real (6), log sin RESUMEN FINAL ni líneas por carpeta, totales + fecha/hora final presentes, traducción ES↔EN del footer y del log, registro de popups limpio
- Title bar en runtime: "Click2Folders - Organizador Cronológico de Fotos y Videos v1.10.29"

### Archivos
- click2folders.py - v1.10.29
- installer.iss - v1.10.29
- dist\Click2Folders-Portable-v1.10.29.exe
- installer\Click2Folders-Instalador-v1.10.29.exe
- Backup Claude/v1.10.29/ - .py + spec + iss + NOTAS_SESION + portable + instalador

---

## v1.10.30 - 29/09/2026 - Confirmación al cerrar el programa (X)

### 1. Diálogo "Confirmar cierre" al pulsar la X
- **Nuevo** `on_close` pregunta antes de cerrar: al pulsar la X de la ventana principal (o Alt+F4) aparece el diálogo modal **"¿Deseas cerrar el programa?"** con botones **"Sí, cerrar"** (rojo) y **"Cancelar"** (gris)
- Si el usuario cancela (botón Cancelar o la X del propio diálogo) el programa queda abierto; solo cierra al confirmar
- Protege contra cierres accidentales; `on_close` solo lo invoca el protocolo `WM_DELETE_WINDOW` (nadie más lo llama)
- Mismo estilo visual que los demás popups (frame #e8eef5, esquinas redondeadas, `center_window`, `grab_set`, `transient`)
- **Traducido y en vivo**: registrado en `_live_popups` — si el usuario pulsa Traducir con el diálogo abierto, título/label/botones cambian de idioma al instante ("Do you want to close the program?" / "Yes, close" / "Cancel", título "Confirm close")

### Verificación
- py_compile OK
- **Test unitario (6 checks, TODO PASS)**: cancelar→False + traducción en caliente del diálogo, confirmar→True, `on_close` cancelado deja la app viva, `on_close` confirmado destruye la app
- **Test en el exe real (ALL PASS)**: WM_CLOSE a la ventana principal → aparece el diálogo; X al diálogo (cancelar) → diálogo se cierra y la app **sigue viva**
- Title bar en runtime: "Click2Folders - Organizador Cronológico de Fotos y Videos v1.10.30"

### Archivos
- click2folders.py - v1.10.30
- installer.iss - v1.10.30
- dist\Click2Folders-Portable-v1.10.30.exe
- installer\Click2Folders-Instalador-v1.10.30.exe
- Backup Claude/v1.10.30/ - .py + spec + iss + NOTAS_SESION + portable + instalador

---

## v1.10.31 - 29/09/2026 - Contenido sin carpetas creadas + log sin espacio desperdiciado + sin lang_debug

### 1. Columna Contenido: se elimina el dato de carpetas creadas
- **Antes**: `26 carpetas / 1925 archivos organizados / 44 sin fecha` → **Ahora**: `1925 archivos organizados / 44 sin fecha` (ES) / `1925 files organized / 44 without date` (EN)
- Se quitó el segmento `{dc} carpetas / ` del formato post-organizar en `_update_cantidad_after_organize`; el total de carpetas creadas sigue visible en el pie de pantalla (`Total de carpetas creadas:`)
- El formato previo a organizar (`X carpetas / Y Archivos en total`) **se mantiene**: son subcarpetas existentes de la carpeta, no carpetas creadas por el programa
- Tutorial actualizado (EN y ES): ejemplo de Contenido tras organizar ya sin carpetas

### 2. Anchos de columna: nada queda oculto (verificado)
- Contenido/Estado: sin tope de ancho en `_fit_folder`, `minwidth=300` → el texto nunca queda cortado
- **Carpeta**: `folder_w = max(_col_needed(1, 200), espacio_restante)` — si el texto de la ruta no cabe en el espacio restante, la columna se ensancha y aparece la barra horizontal (antes una ruta larga podía quedar cortada **sin** scroll)

### 3. Log: sin línea en blanco final
- Se eliminó el `\n` final del bloque de resumen y el `\n` extra que añadía `_log_summary` → el log termina limpio en la última línea de `============================================================`
- El espacio en blanco que se veía al pie del log era material desaprovechado (decisión: eliminarlo)

### 4. Se elimina lang_debug.txt (artefacto de depuración)
- **Qué era**: archivo de texto de debug que `_toggle_lang` escribía en la carpeta del programa registrando el estado de la traducción; no aportaba nada al usuario final y no debe existir en la distribución
- Se eliminó todo el aparato `_dbg` de `_toggle_lang` (lista de debug + escritura del archivo): ya no se genera ni en modo fuente ni en modo congelado
- Se borró `dist\lang_debug.txt` existente

### Verificación
- py_compile OK
- **Test e2e (15 checks, ALL PASS)**: proceso real de organización (6 archivos), formato de Contenido sin "carpetas", anchos sin texto oculto (Contenido, Carpeta, y tras traducir), log termina en `====` sin blanco final, totales presentes y sin RESUMEN, `_toggle_lang` no crea `lang_debug.txt`, traducción completa (Contenido + log + footer)
- Title bar en runtime: "Click2Folders - Organizador Cronológico de Fotos y Videos v1.10.31" (EnumWindows PASS)

### Archivos
- click2folders.py - v1.10.31
- installer.iss - v1.10.31
- dist\Click2Folders-Portable-v1.10.31.exe
- installer\Click2Folders-Instalador-v1.10.31.exe
- Backup Claude/v1.10.31/ - .py + spec + iss + NOTAS_SESION + portable + instalador

---

## v1.10.32 - 29/09/2026 - Regresiones de v1.10.31: barra horizontal y log cortado

### 1. Ventana de carpetas restaurada (como en v1.10.30)
- **Problema**: en v1.10.31 cambié `folder_w = max(_col_needed(1, 200), espacio_restante)` — con rutas largas la columna Carpeta se ensanchaba, el total superaba el ancho de la vista y aparecía una **barra horizontal de desplazamiento que no existía antes**; al arrastrar los separadores de columna con esa barra activa, las líneas divisorias se descolocaban y "todo se desordenaba"
- **Solución**: revertido a la fórmula original de v1.10.30: `folder_w = max(200, tw - sel_w - cant_w - status_w)` — la columna Carpeta llena el espacio restante, sin barra horizontal, idéntico a como estaba
- Test H2: suma de anchos = ancho exacto del árbol (838 = 838), sin desbordar

### 2. Mensaje final del log ya no sale cortado
- **Problema**: `_log_summary` hacía `yview_moveto((line_id-2)/total_lines)` (fracción de líneas, no de scroll real) — al quitar el espacio en blanco final en v1.10.31, la última línea real ("Fecha/hora final" + cierre `====`) quedaba a media vista
- **Solución**: `_log_summary` ahora hace `yview_moveto(1.0)` tras insertar el resumen → el log queda fijado al final, la última línea siempre visible
- Test L2/L5: `yview()` retorna `(..., 1.0)` tras organizar y tras traducir

### Verificación
- py_compile OK
- **Test e2e (14 checks, ALL PASS)**: organización real (6 archivos), **sin barra horizontal** (H1/H3), anchos sin desbordar (H2), formato Contenido sin carpetas, log termina en `====` y **scroll al final** (L2), totales presentes, sin RESUMEN, sin `lang_debug.txt`, traducción completa
- Title bar en runtime: "Click2Folders - Organizador Cronológico de Fotos y Videos v1.10.32" (EnumWindows PASS)

### Archivos
- click2folders.py - v1.10.32
- installer.iss - v1.10.32
- dist\Click2Folders-Portable-v1.10.32.exe
- installer\Click2Folders-Instalador-v1.10.32.exe
- Backup Claude/v1.10.32/ - .py + spec + iss + NOTAS_SESION + portable + instalador

---

## v1.10.33 - 30/09/2026 - Agregar carpetas acumula (no reemplaza) + organización con selección preservada

### 1. "Agregar carpeta" ya no reemplaza la anterior
- **Bug**: `_clear_placeholder_rows()` borraba **TODAS** las filas del árbol (no solo los placeholders vacíos) y `_add_single_folder()` lo llamaba antes de insertar → cada carpeta nueva **borraba las anteriores** (fila y ☑ perdidos); el `queue` sí acumulaba, quedando inconsistente (carpetas invisibles en la lista)
- **Solución**: las filas placeholder ahora llevan tag `"ph"` (`_add_placeholder_rows`) y `_clear_placeholder_rows()` solo borra las que tengan ese tag → las carpetas reales **se conservan y acumulan**
- Afectaba también a "Agregar varias carpetas" (`do_add` llamaba a la misma función)

### 2. "No organiza nada" - consecuencia del mismo bug
- Al agregar una 2ª carpeta se borraba la fila de la 1ª **con su ☑** → al pulsar Organizar no había nada marcado y salía el aviso "Selección requerida" (o se procesaba otra cosa): sensación de que "no organiza nada"
- Con la acumulación corregida, la marca ☑ **sobrevive** a agregar más carpetas (test B3) y Organizar procesa lo marcado (test O2-O4)
- Defensa extra en `on_start`/`on_undo`: ignorar valores de carpeta vacíos (filas placeholder no pueden colarse en la selección)

### 3. Quitar todo → placeholders restaurados
- `remove_checked` sigue funcionando: al vaciar la lista reaparecen las 6 filas placeholder (tag `ph`) y se puede volver a agregar desde cero (test Q3-Q5)

### Verificación
- py_compile OK
- **Test e2e (19 checks, ALL PASS)**: placeholders iniciales; agregar A y B **acumula 2 filas** con A conservada **y sigue marcada ☑**; duplicado no duplica ni borra; organizar con A marcada → A "Organizado"/"6 archivos organizados / 0 sin fecha", B intacta, footer 6; regresiones v1.10.32 (log con cierre, scroll al final, sin barra horizontal); quitar todo → 6 placeholders + queue vacía; re-agregar tras vaciar; sin `lang_debug.txt`
- Title bar en runtime: "Click2Folders - Organizador Cronológico de Fotos y Videos v1.10.33" (EnumWindows PASS)

### Archivos
- click2folders.py - v1.10.33
- installer.iss - v1.10.33
- dist\Click2Folders-Portable-v1.10.33.exe
- installer\Click2Folders-Instalador-v1.10.33.exe
- Backup Claude/v1.10.33/ - .py + spec + iss + NOTAS_SESION + portable + instalador

---

## v1.10.34 - 30/09/2026 - "Carpeta Vacía" en Contenido + soporte EN con "¿" + tutorial coherente

### 1. Carpetas vacías muestran "Carpeta Vacía / Empty Folder"
- **Antes**: al agregar una carpeta sin archivos ni subcarpetas, la columna Contenido quedaba **vacía** (sin información)
- **Ahora**: `else ""` → `("Carpeta Vacía" if not eng else "Empty Folder")` en los 3 puntos del formato pre-organización:
  - `_add_single_folder` (agregar carpeta)
  - `do_add` (agregar varias carpetas)
  - `_update_status_after_undo` (tras deshacer)
- `_translate_cantidad_text` conoce el par `Carpeta Vacía ↔ Empty Folder` → al pulsar Traducir, las filas ya existentes se traducen en caliente (ambas direcciones)
- Post-organización conserva el formato "N archivos organizados / M sin fecha"

### 2. Soporte en inglés: encabezado con "¿" de apertura
- EN: `"¿Do you have any questions,\nsuggestions or want to report a problem?"` — faltaba el signo de apertura (el ES ya lo tenía)

### 3. Tutorial revisado por coherencia (EN + ES)
- **"Quantity column" → "Content column"**: el encabezado real del árbol es Contenido/Content (el nombre viejo venía de versiones anteriores)
- Formatos de ejemplo exactos: 'X folders / **Total files**' y 'X carpetas / Y **Archivos en total**' (antes decía 'Y files'/'Y archivos')
- Nueva línea en Columna Contenido: carpeta vacía muestra **'Empty Folder' / 'Carpeta Vacía'**
- **Extensiones**: decía "solo imagen o video... siempre que tenga metadatos o fecha en el nombre" → ahora "cualquier tipo de archivo (jpeg, png, mp4, Word, Excel, PDF, etc.)" + recomendación de modos 3/4 para documentos
- Botón: "Remove Folders" → "Remove selected folders" (etiqueta real del botón EN)
- "NEVER deletes your photos or videos" → "NEVER deletes your files" / "NUNCA borra tus archivos" (también organiza documentos)

### 4. Comportamiento: ¿organiza archivos que no son foto/video (Word/Excel)?
- **Sí** — `_organize_folder` no filtra por extensión: procesa cualquier archivo; solo decide si tiene fecha en el modo elegido
- Modo 1 (Captura/Medio/Nombre): fotos EXIF → video fecha de medio → fecha en nombre → Shell "Medio creado"; si nada → "sin fecha" y **se queda en la raíz**
- Modo 2: fecha en el nombre; **Modo 3 (Creación) y 4 (Modificación) sirven para cualquier archivo** (Word/Excel/PDF) porque usan fechas del sistema — recomendados para documentos

### Verificación
- py_compile OK
- **Test e2e (38 checks, ALL PASS)**: Carpeta Vacía al agregar (ES y EN + traducción en caliente ida y vuelta); soporte EN con "¿"; tutorial EN/ES (Content column sin Quantity, Remove selected folders, extensiones, mención Empty Folder/Carpeta Vacía, sin textos obsoletos); organizar modo 3 con carpeta normal y vacía → contenidos post-organizar correctos ("2/0" y "0/0"); log termina en `====` sin línea en blanco + scroll 1.0; deshacer → "Carpeta Vacía" restaurada + archivos de vuelta en raíz; placeholders v1.10.33; sin `lang_debug.txt`
- Title bar en runtime: "Click2Folders - Organizador Cronológico de Fotos y Videos v1.10.34" (EnumWindows PASS)
- **Arnés de test (lecciones)**: los hilos de trabajo llaman `self.after()` y eso solo despacha si el main thread está dentro de `mainloop` → `on_start`/`on_undo` se ejecutan desde un callback programado (`run_op`); `_check_launch_donation` se neutraliza en el test porque `on_donate()` cierra ventanas auxiliares (`_close_aux_windows`) y borraba el Soporte/Tutorial a mitad de prueba
- **⚠ Nunca usar PowerShell `-replace`+`Set-Content` sobre click2folders.py**: el archivo es UTF-8 sin BOM y PS 5.1 lo lee como ANSI (mojibake `Ã³`/`Â¿`); se restauró desde `Backup Claude/v1.10.33/` y los cambios se reaplicaron con la herramienta Edit

### VirusTotal (02/10/2026)
- **Portable v1.10.34**: 5/69 falsos positivos — Arctic Wolf (Unsafe), Bkav Pro (W32.Malware.3E776734), CrowdStrike (malicious_confidence_60%), Microsoft (Trojan:Win32/Wacatac.C!ml), SecureAge (Malicious); etiqueta de amenaza "trojan", categorías peexe/overlay/64bits (típico de PyInstaller de un solo archivo)
- **Compilación sin cambios respecto a las versiones con 0-2 FP**: mismo `.spec` (UPX **no está instalado** ⇒ `upx=True` es no-op, igual que en los builds anteriores), mismo PyInstaller 6.16.0, misma fuente — la variación 2→5 es actualización de heurísticas de los motores (Wacatac/Cloud), no del programa
- **Instalador v1.10.34 regenerado (02/10)** con ISCC desde el mismo portable → archivo distinto (Inno Setup, no PyInstaller) ⇒ escaneo propio en VirusTotal
- **✅ Instalador v1.10.34 en VirusTotal: 0/69 — sin falsos positivos** (SHA256 `fd4a08b40fc460560fe9d74ecfff908c27dc5341e81de2b7427c8bc259e158f5`, analizado 02/10/2026) — el empaquetado Inno Setup no dispara las heurísticas PyInstaller/Wacatac que marcan el portable; recomendado distribuir el instalador como binario oficial

### Archivos
- click2folders.py - v1.10.34
- installer.iss - v1.10.34
- dist\Click2Folders-Portable-v1.10.34.exe
- installer\Click2Folders-Instalador-v1.10.34.exe
- Backup Claude/v1.10.34/ - .py + spec + iss + NOTAS_SESION + portable + instalador

---

## Documentación del repositorio - 02/10/2026 - PRIVACY.md + README (sin cambio de versión)

### Contexto
- Inspirado en un video de TikTok sobre 5 normativas para apps hechas con IA (política de privacidad, declarar no-recopilación, declarar uso de IA, nombrar terceros, borrado de datos)
- Decisión del usuario: **el video NO se integra** ni en la app ni en el README; solo se aplicó el contenido como checklist del proyecto

### Cambios
- **Nuevo `PRIVACY.md`** (raíz del repo, ES+EN): declara no-recopilación, sin cuentas/servidores, única comunicación = API de GitHub para verificar updates, terceros (PayPal / Nequi-Wompi / USDT), desarrollo con asistencia de IA, archivos nunca salen de la PC, borrado = desinstalar
- **README.md**:
  - Nueva sección "Privacidad / Privacy" después de "Seguridad", enlazando `PRIVACY.md`
  - Datos desactualizados corregidos: badge versión **v1.10.14 → v1.10.34**; VirusTotal **0/68 → 0/69** (badge, features y sección Seguridad ES/EN)
- No se tocó `click2folders.py` → sin compilar, sin bump de versión; solo se actualiza esta NOTAS en `Backup Claude/v1.10.34/`

### Archivos afectados
- PRIVACY.md (nuevo)
- README.md
- NOTAS_SESION.md

---

## v1.10.35 - 05/10/2026 - Dominio legacy, recurso de versión y reducción de FP

### Contexto
- **Análisis de vulnerabilidades** del código antes de open source: sin hallazgos críticos (sin eval/exec/subprocess/shell, TLS con verificación por defecto activa, sin secretos, sin servidor ni puertos de escucha, links hardcodeados) - el riesgo real es la 2FA de GitHub, no el código
- Usuario reportó dominio `click2folders.com` (página creada por IA en su momento, nunca publicada) → corregir referencias
- Portable v1.10.34 marcaba 5 FP en VirusTotal (vs 2 en versiones previas) → intentar reducción

### Cambios
1. **Dominio**: `click2folders_installer.iss` (legacy v1.1) `MyAppURL` → `https://github.com/regerman78-ai/Click2Folders`; el `installer.iss` activo ya apuntaba a GitHub
2. **Bump v1.10.35**: `click2folders.py` (línea 4 + `APP_VERSION`), `installer.iss` ×3 (AppVersion, OutputBaseFilename, Source portable), README badge
3. **FP - recurso de versión**: nuevo `version_info.txt` (VSVersionInfo: Company "German Vargas", FileDescription "Click2Folders - Chronological Photo and Video Organizer", FileVersion 1.10.35.0, Copyright (c) 2026) embebido en el PE vía spec `version=` - los exe PyInstaller "sin metadatos de versión" son más penalizados por heurísticas
4. **FP - `upx=False` explícito** en spec (UPX no está instalado; con `upx=True` era no-op, pero explícito documenta intención de no comprimir)

### Verificación
- py_compile OK
- Build PyInstaller 6.16.0 OK - log confirma "Copying version information to EXE"
- EnumWindows runtime: "Click2Folders - Organizador Cronológico de Fotos y Videos **v1.10.35**" PASS
- ISCC OK → Click2Folders-Instalador-v1.10.35.exe (16.09 sec)

### Nota FP honesta
- 2 vs 5 FP entre versiones = **deriva de heurísticas en la nube** de los motores (mismo código, mismo .spec), no un defecto nuevo
- Reducción real: (a) escanear este build nuevo en VirusTotal, (b) portal gratis de Microsoft para falso positivo `https://www.microsoft.com/wdsi/filesubmission`, (c) firma de código OV/EV (de pago) = solución definitiva; **la licencia MIT no influye en los FP**

### Archivos
- click2folders.py - v1.10.35
- click2folders.spec - `version=` + `upx=False`
- version_info.txt (nuevo)
- installer.iss - v1.10.35
- click2folders_installer.iss - URL legacy corregida
- README.md - badge v1.10.35
- dist\Click2Folders-Portable-v1.10.35.exe - SHA256 59B71B2C113357951149327D55A2E564631CBB83CEA7ABD671DA4549AA78CE40
- installer\Click2Folders-Instalador-v1.10.35.exe - SHA256 0E40A70DABE6331F258C3E492960C57670CE331DC3A1F77C58C9B856C2A2C330
- Backup Claude/v1.10.35/ - .py + spec + iss + NOTAS_SESION + portable + instalador + README + PRIVACY + version_info + iss legacy

---

## v1.10.36 - 05/10/2026 - Iconos de acción (abrir ↗ / copiar ⧉) en Soporte y Donaciones

### Contexto
- Usuario vio una web (Soporte SpotiFLAC) con iconos a la derecha de cada valor: ↗ = abre ventana/navegador, ⧉ = copiar al portapapeles → aplicar el mismo patrón a Click2Folders

### Cambios
1. **Nuevo helper** `_action_icon(parent, glyph, cmd)`: CTkButton 34x28, corner_radius=8, fondo blanco, borde #cbd5e1, hover #f1f5f9, glifo font ("Segoe UI", 15) - estética de caja con icono como la referencia
2. **Soporte**: eliminado el texto "Haz click en el correo para copiarlo" / "Click the email to copy it" (ES/EN) → **⧉ a la derecha del correo** en `mail_row`; `copy_mail` acepta `widget=` para tooltip vía `_show_tooltip_temporal` cuando se pulsa el icono
3. **Donaciones**:
   - PayPal: **↗** al final de la fila (abre `paypal.com/donate`...)
   - Nequi: **↗** al final de la fila (abre checkout wompi)
   - USDT: dirección movida a `addr_row` + **⧉ a la derecha** (copia dirección, tooltip igual que antes); texto de instrucción de USDT se mantiene
4. **Glifos verificados por render**: `⧉` (U+29C9) y `↗` (U+2197) dibujan bien en Segoe UI/Segoe UI Symbol (prueba con captura previa a implementar)
5. **Bump v1.10.36**: py ×2, installer.iss ×3, README badge, version_info.txt → 1.10.36.0

### Verificación
- py_compile OK
- **Test e2e source (9/9 + 5/5 PASS)**: soporte ES/EN sin texto de instrucción + 1 icono ⧉ + invoke copia email al clipboard; donaciones ES/EN 2↗ + 1⧉ + invoke copia dirección USDT; capturas tomadas
- Verificación geométrica soporte: icono abs x=762 vs correo termina en 752 (gap 10px, derecha ✓), borde #cbd5e1 en caja, glyph ⧉ ✓
- EnumWindows runtime: "Click2Folders - ... v1.10.36" PASS
- ISCC OK (7.50 sec)
- Nota sesión: la capa de lectura de imágenes de la herramienta sirvió caché vieja (siempre la misma captura de Donaciones); verificación final de Soporte se hizo vía geometría+píxeles

### Archivos
- click2folders.py - v1.10.36 (`_action_icon`, `on_support`, `_do_on_donate`)
- installer.iss - v1.10.36 / version_info.txt - 1.10.36.0 / README badge v1.10.36
- dist\Click2Folders-Portable-v1.10.36.exe - SHA256 86B3ABABA6AAB2137A93B7444ED9C6A47778221BEA8D038F1F35FF794EE9B00A
- installer\Click2Folders-Instalador-v1.10.36.exe - SHA256 1E9BC100D841C910BA2F43CE78F13F2CBD74CB3195A01DDEE43FB9E5B0F9DE1A
- Backup Claude/v1.10.36/ - .py + spec + iss + NOTAS_SESION + portable + instalador + README + PRIVACY + version_info

---

## v1.10.37 - 05/10/2026 - Eliminada la instrucción de USDT en Donaciones

### Contexto
- Con los iconos ↗/⧉ presentes (v1.10.36), el texto "Haz click en la dirección para copiarla" / "Click the address to copy it" quedó redundante → usuario pidió eliminarlo (lo marcó en rojo en su captura)

### Cambios
1. **Donaciones/USDT**: eliminada la etiqueta de instrucción (ES/EN) sobre la dirección; queda título + (`addr_row`: dirección + icono ⧉)
2. **Bump v1.10.37**: py ×2 (línea 4 + APP_VERSION), installer.iss ×3, README badge, version_info.txt → 1.10.37.0

### Verificación
- py_compile OK
- Test source 6/6 PASS: ES y EN - texto eliminado, 2 iconos ↗ + 1 ⧉ presentes, invoke del ⧉ copia dirección USDT al clipboard
- EnumWindows runtime: "Click2Folders - ... v1.10.37" PASS
- ISCC OK (8.078 sec)

### Archivos
- click2folders.py - v1.10.37
- installer.iss - v1.10.37 / version_info.txt - 1.10.37.0 / README badge v1.10.37
- dist\Click2Folders-Portable-v1.10.37.exe - SHA256 8CD4CAEAB8FCE38CF5559B7B479C6ACD799DEE4887197ED6BA5D1CDFB128DF57
- installer\Click2Folders-Instalador-v1.10.37.exe - SHA256 39C7F40DF36AFFDE3F4B138E526A545B9BCB888836F5BB8B0EB80252F3253FF3
- Backup Claude/v1.10.37/ - .py + spec + iss + NOTAS_SESION + portable + instalador + README + PRIVACY + version_info

---

## v1.10.38 - 06/10/2026 - Capturas nuevas reordenadas, bloqueo de Traducir durante proceso y separador único en el log

### Contexto
- Usuario subió 2 capturas nuevas (`Organized for Years.jpg`, `Organize into subfolders by month in English.jpg`) y pidió reordenarlas en el README: Antes → Organized for Years → Después → month in English → resto igual; `donations.jpg` se actualizó en el mismo nombre (sin cambio en README)
- Requisito: mientras se organiza/deshace, el botón Traducir debe quedar deshabilitado para que carpetas y log terminen en el idioma inicial
- Requisito: el log tenía 2 líneas `====`×60 seguidas (cierre del bloque FILES + apertura del bloque final) → debe verse 1 sola

### Cambios
1. **README**: badge → v1.10.38 + 2 secciones nuevas insertadas en el orden pedido (URLs con %20 por los espacios)
2. **Botón Traducir**: `_set_buttons_state` ahora también configura `btn_lang` (se llama en 3306 organizar / 3766 deshacer → disabled; 3479/3835/3899 → normal) + guard en `_toggle_lang`: `if is_processing: return`
3. **Log**: eliminado el `\n{'='*60}` de cierre del bloque FILES (~3450) → separador simple antes del bloque `Fin:`/`End:`
4. **Bump v1.10.38**: py ×2 (línea 4 + APP_VERSION), installer.iss ×3, README badge, version_info.txt → 1.10.38.0

### Verificación
- py_compile OK
- E2E 17/17 PASS (ES y EN): btn_lang disabled al iniciar / normal al final, `_toggle_lang` bloqueado en proceso y funcional en reposo, idioma sin cambios en cada corrida, log sin `====` consecutivos, separador único alrededor del bloque FILES seguido de Fin/End
- Lección reconfirmada: el test debe usar `mainloop()` + callbacks `after` (patrón run_op); con `update()` el hilo muere en `self.after(0, constant_time_update)` línea 3417 (`RuntimeError: main thread is not in main loop`) y `is_processing` queda colgado
- EnumWindows runtime: "Click2Folders - ... v1.10.38" PASS
- ISCC OK (7.422 sec)

### Archivos
- click2folders.py - v1.10.38
- installer.iss - v1.10.38 / version_info.txt - 1.10.38.0 / README badge v1.10.38
- dist\Click2Folders-Portable-v1.10.38.exe - SHA256 292FF25E6182576C571C6C078280E19DF116723EF2FB0DA32EFFC2FB1DBC38E4
- installer\Click2Folders-Instalador-v1.10.38.exe - SHA256 5306513C1E5A3D702C3FCB71E4489C3798EAB1D00EC3F0308EE663A5BCF622B1
- Backup Claude/v1.10.38/ - .py + spec + iss + NOTAS_SESION + portable + instalador + README + PRIVACY + version_info

---

## v1.10.39 - 06/10/2026 - Log sin recortes al maximizar + nota sobre capturas del README

### Contexto
- Al maximizar la ventana, el cuadro de log crece y la línea superior visible quedaba cortada por la mitad (el usuario marcó con rojo "ARCHIVOS SIN FECHA DETECTADA: 44" recortada, con espacio libre señalado con flecha); pidió "bajarlo un poco" para verla completa
- El usuario reportó que GitHub no muestra el orden de capturas pedido: el README local SÍ tiene el orden pedido desde v1.10.38 (Antes → Organized for Years → Después → month in English → resto); GitHub muestra el viejo porque **no se ha hecho push** (pendiente de revisión del usuario)

### Cambios
1. **Realign del log en resize**: `_build_log_area` enlaza `<Configure>` de `self.txt` → `_on_log_configure` (debounce 120 ms con `after_cancel`) → `_realign_log_view`: si la línea en `@0,0` está cortada (bbox de su inicio vacío) → `see(line_start)` la baja completa
2. **`_log_summary`**: inserta `text + "\n"` → queda una línea vacía real al final; cualquier recorte posterior al realinear cae en esa línea vacía y el `====` final se ve completo
3. **Bump v1.10.39**: py ×2 (línea 4 + APP_VERSION), installer.iss ×3, README badge, version_info.txt → 1.10.39.0

### Verificación
- py_compile OK
- Test 15/15 PASS: resize con vista al final (línea superior completa + última línea no vacía completa), cierre con `====` tras `_log_summary` (separador final completo en el pie), corte forzado en medio corregido, guardia del debounce sin excepción, run E2E de organización ES (btn_lang bloqueado/liberado, guardia, separador único, bloque FILES n=2)
- Lección Tk: `get 1.0 end` incluye un `\n` implícito → la última línea no vacía real está en `end - 2 lines` cuando el contenido ya termina en `\n` (helper `last_nonempty()` camina hacia atrás sobre líneas vacías)
- EnumWindows runtime: "Click2Folders - ... v1.10.39" PASS
- ISCC OK (8.828 sec)

### Archivos
- click2folders.py - v1.10.39
- installer.iss - v1.10.39 / version_info.txt - 1.10.39.0 / README badge v1.10.39
- dist\Click2Folders-Portable-v1.10.39.exe - SHA256 F9F1DC213AFC5C13068550CBAED54C7CB3045E76D8E9C4B32458AAFC1B3F3EFE
- installer\Click2Folders-Instalador-v1.10.39.exe - SHA256 6F6B7852FA26C54784818DD9AB5EF62FA5806A0665CB33A6F7279D56EFA39DDE
- Backup Claude/v1.10.39/ - .py + spec + iss + NOTAS_SESION + portable + instalador + README + PRIVACY + version_info

---

## v1.10.40 - 06/10/2026 - Log completo al maximizar (sin espacio final ni líneas ocultas) + push a GitHub

### Contexto
- v1.10.39 falló en el objetivo real: (a) quedó una línea vacía al final del log que el usuario marcó con rojo ("Elimina ese espacio del final"), (b) la línea "ARCHIVOS SIN FECHA DETECTADA" ni siquiera se veía al maximizar (top = 7px cortado, `bbox` no-None → el guard del realign no disparaba)
- Diagnóstico con 2 carpetas (patrón del usuario): maximizado H=189px, span(ARCHIVOS→final) = 13 líneas = 195px > H → el anclaje al final no alcanzaba a mostrar la línea; la línea vacía final (+15px) y el doble blanco del resumen (+15px) empeoraban el span

### Cambios
1. **Sin espacio final**: `_log_summary` vuelve a `insert(text)` (sin `+"\n"`)
2. **Un solo blanco**: eliminado el `\n` inicial de `lines` del resumen → un único blanco entre bloque Fin y Totales (span −15px)
3. **Realign = anclar al final**: `_realign_log_view` ahora solo `yview_moveto(1.0)` si la vista ya estaba al final (`yview()[1] >= 0.999`); el corte δ de píxeles cae sobre la línea en blanco (invisible), la línea ARCHIVOS y el `====` final quedan completos; posiciones de lectura intermedia se preservan
4. **Bump v1.10.40**: py ×2, installer.iss ×3, README badge, version_info.txt → 1.10.40.0

### Verificación
- py_compile OK
- Test 12/12 PASS (escenario usuario: 2 carpetas): ARCHIVOS SIN FECHA **visible COMPLETA** tras `state("zoomed")`, pie `====` completo (normal y maximizado), sin `"\n\n"` final, un solo blanco Fin→Totales, sin `====` consecutivos, btn_lang bloqueado/liberado + guardia
- Lección: `bbox` de Tk devuelve caja con `y<0` para caracteres parcialmente recortados → condición correcta de "línea cortada" es `bb is None or bb[1] < 0`; pero anclar al final es más robusto que `see(top)` porque garantiza el span completo hasta el cierre
- EnumWindows runtime: "Click2Folders - ... v1.10.40" PASS
- ISCC OK (8.562 sec)

### Archivos
- click2folders.py - v1.10.40
- installer.iss - v1.10.40 / version_info.txt - 1.10.40.0 / README badge v1.10.40
- dist\Click2Folders-Portable-v1.10.40.exe - SHA256 6A2575D9893149DF09095348E0E901B5AB4D4EF5DB867128800DD988C49A7EDD
- installer\Click2Folders-Instalador-v1.10.40.exe - SHA256 CA618943910886A14151A9A84F5A9910945D240523C1DAE1C5452FF2B73C1B93
- Backup Claude/v1.10.40/ - .py + spec + iss + NOTAS_SESION + portable + instalador + README + PRIVACY + version_info

---

## v1.10.41 - 06/10/2026 - El log vuelve bien al reducir la ventana (bandera at_end) + aclaración de screenshots en GitHub

### Contexto
- El usuario confirmó: inicio ✓ y maximizar ✓, pero **al volver a tamaño original el log se veía mal**. Causa: el realign solo corrige si `yview()[1] >= 0.999` DESPUÉS del resize; al reducir Tk dejaba la vista sin anclar al final (fracción <0.999) → el guard no disparaba y la vista quedaba a mitad del log
- Screenshots: verificado con fetch de `raw.githubusercontent.com/.../README.md` que GitHub **ya sirve** badge v1.10.41→ v1.10.40, orden nuevo (Antes → Organized for Years → Después → month in English) y todas las imágenes (carpeta == HEAD == push `b2b9e38`, `git status screenshots` limpio) → el usuario ve **caché del navegador** (Ctrl+F5)

### Cambios
1. **Bandera `_log_at_end`**: `yscrollcommand` ahora va por `_on_log_scroll` (guarda la barra + registra `last >= 0.999` como "estaba al final"), pero **ignora los eventos durante el resize** (`_log_resizing`), para no perder el estado pre-resize
2. **`_on_log_configure`** marca `_log_resizing = True` al inicio y lo limpia `_realign_log_view` en `finally`
3. **`_realign_log_view`**: si la bandera dice que estaba al final → `yview_moveto(1.0)` (garantiza ancla al final tras cualquier resize); si el usuario había scrolleado para leer → no toca la posición
4. **Bump v1.10.41**: py ×2, installer.iss ×3, README badge, version_info.txt → 1.10.41.0

### Verificación
- py_compile OK
- Test 17/17 PASS: ciclo NORMAL → ZOOMED → RESTAURAR (vista al final + pie `====` completo + tope en tramo final en los 3 estados, ARCHIVOS completo en MAX, sin `====` consecutivos, sin línea vacía final) + posición de lectura al 50% NO se fuerza al final en resize + btn_lang bloqueado/liberado
- EnumWindows runtime: "Click2Folders - ... v1.10.41" PASS
- ISCC OK (7.281 sec)

### Archivos
- click2folders.py - v1.10.41
- installer.iss - v1.10.41 / version_info.txt - 1.10.41.0 / README badge v1.10.41
- dist\Click2Folders-Portable-v1.10.41.exe - SHA256 FA44DD66BF930B8BDB771D12FC35A195373FE9048B8DB64C41CFD79E8D7FF9C3
- installer\Click2Folders-Instalador-v1.10.41.exe - SHA256 614E78403BA50BE56FE3F1412324E888577E86D85F67D5CA41535A841E799859
- Backup Claude/v1.10.41/ - .py + spec + iss + NOTAS_SESION + portable + instalador + README + PRIVACY + version_info

---

## v1.10.42 - 06/10/2026 - Glifos con borde 2px + GitHub: unificación de ramas main/master (causa raíz de "imágenes desactualizadas")

### Contexto
- Usuario: "pon el borde de los glifos igual que el ancho del borde de cada item (PayPal/Nequi/USDT)" → glifos ↗/⧉ tenían `border_width=1` y los items `border_width=2`
- Usuario: "actualicé la página de GitHub y siguen sin actualizarse las imágenes" — el README crudo en `raw.githubusercontent.com` ya servía el contenido nuevo → **causa raíz distinta**: el repo tenía DOS ramas divergentes; el sitio servía **`main`** (rama por defecto, OID `a887202`, solo 4 archivos: .gitignore, Logo Final.png, README.md, screenshots — README VIEJO sin "Organizado por Años"), mientras todos los pushes iban a **`master`** (comits paralelos con los mismos mensajes pero SHAs distintos, línea reescrita en algún momento)

### Cambios
1. **`_action_icon`**: `border_width=1` → `border_width=2` (mismo ancho que los items `paypal_outer`/`nequi_outer`/`tether_outer` en líneas 2632/2655/2688)
2. **Unificación de ramas** (sin force, sin pérdida): `git merge origin/main --allow-unrelated-histories -X ours` → gana nuestro README (orden nuevo + badge), suma a `master` los archivos que solo vivían en `main`: **`Logo Final.png`** (el logo del README estaba roto en master) y `screenshots/main-window.jpg`
3. **Push**: `master` → `8bf409a`; luego `git push origin master:main` (fast-forward `a887202..8bf409a`) → ambas ramas en `8bf409a`
4. **Bump v1.10.42**: py ×2, installer.iss ×3, README badge, version_info.txt → 1.10.42.0

### Verificación
- py_compile OK
- Test 7/7 PASS (mainloop+after): título v1.10.42, 3 glifos en diálogo de donaciones con `border_width=2`, 3 items con `border_width=2`, glifo == item, 1 glifo en Support con `border_width=2`
- EnumWindows runtime: "Click2Folders - ... v1.10.42" PASS
- ISCC OK (8.891 sec)
- Web de GitHub verificada por fetch: OID servido `8bf409a`, contiene "Organizado por Años", badge v1.10.40, Logo Final presente

### Archivos
- click2folders.py - v1.10.42 (glifos border_width=2)
- installer.iss - v1.10.42 / version_info.txt - 1.10.42.0 / README badge v1.10.42
- dist\Click2Folders-Portable-v1.10.42.exe - SHA256 4FF5973BE74112A10A2AA463D848D2432CD7BA47C8F4550CDF669C8BCD16C820
- installer\Click2Folders-Instalador-v1.10.42.exe - SHA256 186625D73B494873870337DA1796D1D8A30BF7CDD5C2F58AA0BCCBA681113424
- Backup Claude/v1.10.42/ - .py + spec + iss + NOTAS_SESION + portable + instalador + README + PRIVACY + version_info

---

## v1.10.43 - 06/10/2026 - README: títulos bilingües ES/EN reordenados + modos con números normales + tutorial interno explica carpetas en inglés

### Contexto
- Usuario revisó el README en GitHub (ya servía el contenido nuevo tras unificar ramas) y pidió 5 ajustes de texto/estructura, más aclarar en el tutorial cómo crear carpetas en inglés

### Cambios README
1. **Título de la imagen de años**: `### Organizado por Años / Organized by Years` → `### Después / Organizado por Años / Organized by Years` (texto exacto elegido por el usuario)
2. **Siguiente captura (mes ES)**: `### Después / After` → `### Organizado en Subcarpetas por mes / Organized in Subfolders by Month`
3. **Captura en inglés**: `### Organización por Mes (Inglés) / Organization by Month (English)` → `### Organizado en Subcarpetas por mes (Inglés) / Organized in Subfolders by Month (English)` + párrafo nuevo: "También puedes crear las subcarpetas en inglés: pon el programa en inglés y haz clic en "Organizar"." + traducción EN
4. **Modos con números normales**: la lista `1.`–`4.` estaba ANIDADA dentro de la viñeta `- **4 modos de organización:**` → GitHub renderiza `<ol>` anidado con números **romanos** (i., ii., iii., iv.). Desanidada al margen → `<ol>` de primer nivel → 1, 2, 3, 4 normales (verificado: nunca hubo romanos en el historial de git; el HTML en vivo sí tiene `<ol>` anidado = CSS de GitHub)
5. **Paso 1 de "¿Cómo usarlo?"**: "Descarga el instalador desde Releases" → "Descarga el instalador o la versión portable desde Releases"

### Cambios app (tutorial interno `on_tutorial`)
6. **ES** (sección "🔘 Botones principales" → "Traducir al Español"): línea nueva "Para crear las carpetas en inglés solo pon el programa en inglés y da click en Organizar."
7. **EN** (misma sección): "To create the folders in English, just set the program to English and click Organize."
8. **Bump v1.10.43**: py ×2, installer.iss ×3, README badge, version_info.txt → 1.10.43.0

### Verificación
- py_compile OK
- Test 8/8 PASS (mainloop+after): título v1.10.43 + README (4 títulos/pasos/estructura desanidada) + tutorial ES con nota + tutorial EN con nota
- EnumWindows runtime: "Click2Folders - ... v1.10.43" PASS
- ISCC OK (8.078 sec)

### Nota
- La captura `screenshots/tutorial.jpg` del README quedó desactualizada (el tutorial interno cambió); el usuario puede regenerarla cuando quiera

### Archivos
- click2folders.py - v1.10.43 (tutorial ES/EN)
- installer.iss - v1.10.43 / version_info.txt - 1.10.43.0 / README badge v1.10.43
- dist\Click2Folders-Portable-v1.10.43.exe - SHA256 19CC9D3E3CB0B800E77052AFB8D98220964892AB8403EF490AAD37921FBC25AC
- installer\Click2Folders-Instalador-v1.10.43.exe - SHA256 8A65621293EB5E21C1250171108FD86B86554EA462171651BAA79E5B9772EA5D
- Backup Claude/v1.10.43/ - .py + spec + iss + NOTAS_SESION + portable + instalador + README + PRIVACY + version_info

---

## v1.10.44 - 06/10/2026 - README: 4 títulos de capturas con textos nuevos (877 archivos, "Ahora queda", "¡Y subcarpetas!", "Incluso puedes")

### Contexto
- Usuario pidió 4 cambios de texto en los títulos de las capturas del README (citaba los que ve en GitHub, que corresponden a la versión aún sin subir de v1.10.43 → los nuevos textos reemplazan a los de v1.10.43 pendientes)

### Cambios README (títulos)
1. `Antes / Before` → **`877 archivos desordenados`** (texto exacto pedido, sin traducción)
2. `Organizado por Años / Organized by Years` → **`Ahora queda organizado por Años / Organized by Years`**
3. `Después / After` → **`¡Y subcarpetas por mes! / And month subfolders!`** (EN según regla ES/EN; "month subfolders" = término ya usado en el README)
4. `Organización por Mes (Inglés) / Organization by Month (English)` → **`Incluso puedes poner las subcarpetas en inglés / You can even have the subfolders in English`** — se conserva el párrafo "También puedes crear las subcarpetas en inglés: pon el programa en inglés y haz clic en Organizar." (+EN) que explica el CÓMO
5. **Bump v1.10.44**: py ×2, installer.iss ×3, README badge, version_info.txt → 1.10.44.0

### Verificación
- py_compile OK
- Test 12/12 PASS (mainloop+after): los 4 títulos nuevos + "Antes / Before" ausente + nota cómo-crear conservada + paso1 portable + modos 1-4 desanidados + badge v1.10.44 + título v1.10.44 + tutorial ES/EN notas
- EnumWindows runtime: "Click2Folders - ... v1.10.44" PASS
- ISCC OK (11.328 sec)

### Archivos
- click2folders.py - v1.10.44
- installer.iss - v1.10.44 / version_info.txt - 1.10.44.0 / README badge v1.10.44
- dist\Click2Folders-Portable-v1.10.44.exe - SHA256 55E0F77EE50E77D372A716D86777E0651652C851AC7A3F988E7FA6BD2E033EB3
- installer\Click2Folders-Instalador-v1.10.44.exe - SHA256 D7673203671535310173F9046B10B7CC7AA721953A78C496DD66F1569B62FF1B
- Backup Claude/v1.10.44/ - .py + spec + iss + NOTAS_SESION + portable + instalador + README + PRIVACY + version_info

---

## v1.10.45 - 07/10/2026 - README: título nuevo de la imagen en inglés + eliminado el párrafo redundante

### Contexto
- Usuario (tras ver v1.10.44 ya publicado) pidió: título nuevo para la captura en inglés y eliminar el texto enmarcado en rojo (título viejo). Confirmó por pregunta: el nuevo texto pasa a ser el TÍTULO y el párrafo "También puedes crear..." (con su traducción) se ELIMINA para no repetir el mismo mensaje

### Cambios README
1. `### Incluso puedes poner las subcarpetas en inglés / You can even have the subfolders in English` → **`### Incluso nombra las subcarpetas en inglés, solo pon el programa en inglés y da click en organize / It even names the subfolders in English, just put the program in English and click organize`**
2. **Eliminado** el párrafo bilingual debajo de la imagen: "También puedes crear las subcarpetas en inglés: pon el programa en inglés y haz clic en 'Organizar'." + "You can also create the subfolders in English: put the program in English and click "Organize"."
3. **Bump v1.10.45**: py ×2, installer.iss ×3, README badge, version_info.txt → 1.10.45.0

### Verificación
- py_compile OK
- Test 12/12 PASS (mainloop+after): título nuevo ES+EN presente, título viejo ausente, párrafo antiguo ausente, 3 títulos anteriores conservados, paso portable, modos 1-4, badge, título app, tutorial ES/EN
- EnumWindows runtime: "Click2Folders - ... v1.10.45" PASS
- ISCC OK (21.281 sec)

### Archivos
- click2folders.py - v1.10.45
- installer.iss - v1.10.45 / version_info.txt - 1.10.45.0 / README badge v1.10.45
- dist\Click2Folders-Portable-v1.10.45.exe - SHA256 DF919334B4EB0DC3D0E71839A5159545622DA78C3B9E4A0053590E56BC7AB76B
- installer\Click2Folders-Instalador-v1.10.45.exe - SHA256 4B7288A770F4FC61C9E49493AECDA923AC569571E963CC0B7FCA83AA9873FD72
- Backup Claude/v1.10.45/ - .py + spec + iss + NOTAS_SESION + portable + instalador + README + PRIVACY + version_info

---

## v1.10.46 - 07/10/2026 - Ko-fi: nueva tarjeta de donación PRIMERA (app + README + PRIVACY)

### Contexto
- Usuario creó su página de Ko-fi **https://ko-fi.com/click2folders** y conectó su cuenta de PayPal (Ko-fi paga instantáneo al PayPal; 0% de comisión en donaciones únicas con Contributor Mode desactivada) → integrar Ko-fi como método de donación **primero** en el orden: **Ko-fi → PayPal → Nequi → USDT**
- Icono colocado por el usuario: `BAUL/Ko-fi_Logo.png` (220x220) - el spec empaqueta BAUL completo, se incluye solo

### Cambios
1. **Ventana Donaciones (`_do_on_donate`)**: nueva tarjeta **KO-FI PRIMERA** (antes de PayPal), mismo patrón de las demás: logo `BAUL/Ko-fi_Logo.png` (60x60, clicable), título **"Apóyame en Ko-fi:"** / **"Support me on Ko-fi:"**, enlace `https://ko-fi.com/click2folders` (clicable) y botón **↗** al final vía `_action_icon`; `open_kofi()` abre el navegador con fallback a portapapeles (mismo patrón `open_nequi_checkout`) + separador → orden final: **Ko-fi → PayPal → Nequi → USDT**
2. **README**: sección `### Ko-fi` **primera** en Donaciones, antes de `### PayPal`: "Apóyame en Ko-fi / Support me on Ko-fi: **https://ko-fi.com/click2folders**"
3. **PRIVACY.md**: terceros ES+EN → "(Ko-fi, PayPal, Nequi/Wompi, USDT)"
4. **Bump v1.10.46**: py ×2, installer.iss ×3, README badge, version_info.txt → 1.10.46.0

### Verificación
- py_compile OK
- Test **30/30 PASS** (mainloop+after): archivos (README link + Ko-fi antes de PayPal + badge, PRIVACY ×2, iss ×2, version_info ×4, APP_VERSION) + ES y EN: 4 tarjetas, Ko-fi PRIMERA, PayPal 2da, Nequi 3ra, USDT 4ta, título ES/EN, enlace, glifo al final, logo cargado, botón ↗ único
- EnumWindows runtime: "Click2Folders - ... v1.10.46" PASS
- ISCC OK (9.078 sec)

### Nota
- `screenshots/donations.jpg` del README quedó desactualizado (ahora muestra la tarjeta Ko-fi primero); el usuario regenerará la captura antes de publicar

### Archivos
- click2folders.py - v1.10.46 (tarjeta Ko-fi)
- BAUL/Ko-fi_Logo.png - icono nuevo (colocado por el usuario)
- installer.iss - v1.10.46 / version_info.txt - 1.10.46.0 / README badge v1.10.46
- dist\Click2Folders-Portable-v1.10.46.exe - SHA256 6BBD343F5AB594E506C4912401D7E1A76AFE8C257FE2C480F6435BAA84EB3D8A
- installer\Click2Folders-Instalador-v1.10.46.exe - SHA256 1DDF7E064FA65DAC406334CA65CC39A622FDF46990EB386A2661DCD556ACCD51
- Backup Claude/v1.10.46/ - .py + spec + iss + NOTAS_SESION + portable + instalador + README + PRIVACY + version_info

---

## v1.10.47 - 08/10/2026 - Ko-fi: título nuevo "Invítame un café" (ES+EN) en app y README

### Contexto
- Usuario vio la ventana de Donaciones de v1.10.46 y prefirió **"Invítame un café en Ko-fi:"** en vez de "Apóyame en Ko-fi:" → corregir; EN elegido por pregunta: **"Buy me a coffee on Ko-fi:"** (frase oficial de Ko-fi)
- README: mismo texto bilingüe nuevo en la sección Ko-fi

### Cambios
1. **Ventana Donaciones**: título Ko-fi ES "Apóyame en Ko-fi:" → **"Invítame un café en Ko-fi:"**; EN "Support me on Ko-fi:" → **"Buy me a coffee on Ko-fi:"**
2. **README**: línea de la sección Ko-fi → **"Invítame un café en Ko-fi / Buy me a coffee on Ko-fi: https://ko-fi.com/click2folders"**
3. **Bump v1.10.47**: py ×2, installer.iss ×3, README badge, version_info.txt → 1.10.47.0

### Verificación
- py_compile OK
- Test **34/34 PASS** (mainloop+after): textos nuevos ES+EN presentes + viejos ausentes (app y README), README Ko-fi antes de PayPal, badge/iss ×2/version_info ×4/APP_VERSION, 4 tarjetas en orden ES+EN, logo/glyph al final/botón ↗ único
- EnumWindows runtime: "Click2Folders - ... v1.10.47" PASS
- ISCC OK (10.515 sec)

### Nota (hallazgo operativo)
- El **mutex de instancia única** (`Click2Folders_SingleInstance_v1`, línea 178) + `sys.exit(0)` en `__init__` (línea 1371) hace que el test salga **0 sin ningún output** si queda un exe corriendo → **matar procesos *click2folders* ANTES de correr tests** (2 instancias v1.10.46 de la verificación previa causaron el silencio)

### Archivos
- click2folders.py - v1.10.47 (título Ko-fi ES/EN)
- installer.iss - v1.10.47 / version_info.txt - 1.10.47.0 / README badge v1.10.47
- dist\Click2Folders-Portable-v1.10.47.exe - SHA256 5972450D44B73CD4D9175294EA04E5707A1AFE641E6331C2AF03033FA4A3E191
- installer\Click2Folders-Instalador-v1.10.47.exe - SHA256 2A76F0FE758B8E25D008323BB61DEB95DB918CCDE2E91B9D0CDF66E910CEEB61
- Backup Claude/v1.10.47/ - .py + spec + iss + NOTAS_SESION + portable + instalador + README + PRIVACY + version_info

---

## v1.10.48 - 08/10/2026 - Ko-fi: título simplificado "Invítame un café" (sin "en Ko-fi")

### Contexto
- Usuario vio v1.10.47 en pantalla y pidió **quitar "en Ko-fi:"** del título (recuadro rojo en su captura): solo dejar **"Invítame un café"**

### Cambios
1. **Ventana Donaciones**: título Ko-fi ES "Invítame un café en Ko-fi:" → **"Invítame un café"**; EN "Buy me a coffee on Ko-fi:" → **"Buy me a coffee"**
2. **README**: línea Ko-fi → **"Invítame un café / Buy me a coffee: https://ko-fi.com/click2folders"** (misma simplificación bilingüe)
3. **Bump v1.10.48**: py ×2, installer.iss ×3, README badge, version_info.txt → 1.10.48.0

### Verificación
- py_compile OK
- Test **34/34 PASS** (mainloop+after): textos nuevos ES+EN presentes, "en Ko-fi"/"on Ko-fi" ausentes (app y README), README Ko-fi antes de PayPal, badge/iss ×2/version_info ×4/APP_VERSION, 4 tarjetas en orden ES+EN, logo/glyph/botón ↗ único
- EnumWindows runtime: "Click2Folders - ... v1.10.48" PASS
- ISCC OK (9.031 sec) - PyInstaller: retry benigno de timestamp (PermissionError 1/20, luego OK)

### Nota
- Pendiente: captura `screenshots/donations.jpg` del usuario con este título final → push a master y main

### Archivos
- click2folders.py - v1.10.48 (título Ko-fi simplificado)
- installer.iss - v1.10.48 / version_info.txt - 1.10.48.0 / README badge v1.10.48
- dist\Click2Folders-Portable-v1.10.48.exe - SHA256 9542EC93EA62BC03525A1367486F8EF1C73168982F14474E47B0722E11D4CAB3
- installer\Click2Folders-Instalador-v1.10.48.exe - SHA256 AAB67D4E31D9F9B658400F07B4B93BEB0E1F71DFA53F1D7CC08E97D424C273C8
- Backup Claude/v1.10.48/ - .py + spec + iss + NOTAS_SESION + portable + instalador + README + PRIVACY + version_info

---

## v1.10.49 - 08/10/2026 - README: "¿Cómo usarlo?" reducido a 3 pasos + nota de deshacer

### Contexto
- Usuario: la lista de 6 pasos de "¿Cómo usarlo? / How to use?" estaba muy larga → reemplazar por 3 pasos + nota de deshacer (textos exactos dados por el usuario)

### Cambios README
1. **Lista nueva** (antes 6 pasos):
   1. Descarga el instalador o usa la versión portable y abre el programa
   2. Elige el modo de organización y agrega las carpetas que quieras
   3. Click en Organizar
2. **Nota nueva** (párrafo aparte tras línea en blanco): "¡También puedes deshacer la organización y elegir otro modo de organización las veces que quieras!"
3. **Eliminados**: link Releases del paso 1 (la sección "Descarga / Download" arriba ya lo tiene), "Instala Click2Folders", "Agrega la carpeta...", "Marca las carpetas...", "¡Listo! Tus fotos..."
4. **Bump v1.10.49**: py ×2, installer.iss ×3, README badge, version_info.txt → 1.10.49.0

### Verificación
- py_compile OK
- Test **32/32 PASS** (mainloop+after): 3 pasos nuevos + nota de deshacer presentes, 5 textos viejos ausentes, línea Ko-fi intacta, badge/iss ×2/version_info ×4/APP_VERSION, ventanas Donaciones ES+EN sin regresión (4 tarjetas, Ko-fi primero, título/enlace/glifo/logo)
- EnumWindows runtime: "Click2Folders - ... v1.10.49" PASS
- ISCC OK (11.157 sec)

### Archivos
- click2folders.py - v1.10.49 (solo bump)
- installer.iss - v1.10.49 / version_info.txt - 1.10.49.0 / README badge v1.10.49
- README.md - lista ¿Cómo usarlo? reducida
- dist\Click2Folders-Portable-v1.10.49.exe - SHA256 36A56960A4763CF567B55354C3DDEAC8C754FE63E53FAB4C4AB90DB3A8062E78
- installer\Click2Folders-Instalador-v1.10.49.exe - SHA256 C7388128993B70306F356605CC4CFA59332D3F51FC1469D50277C7EF8270F138
- Backup Claude/v1.10.49/ - .py + spec + iss + NOTAS_SESION + portable + instalador + README + PRIVACY + version_info

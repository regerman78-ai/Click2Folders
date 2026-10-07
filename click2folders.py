# -- coding: utf-8 --
"""
Click2Folders - Organizador automático de fotos y videos
Versión: v1.10.44
"""
import os
import re
import sys
import time
import struct
import shutil
import hashlib
import tempfile
import threading
import webbrowser
from datetime import datetime, timedelta
from collections import defaultdict
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor
import customtkinter as ctk

# === ESTILO NEOFORMISMO ===
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Variables de la aplicación
APP_NAME = "Click2Folders"
APP_VERSION = "v1.10.44"
GITHUB_REPO = "regerman78-ai/Click2Folders"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"
GITHUB_RELEASES_URL = f"{GITHUB_URL}/releases"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
WINDOW_TITLE = f"Click2Folders - Organizador Cronológico de Fotos y Videos {APP_VERSION}"
ICON_FILE = "favicon.ico"
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# Carga condicional de librerías
try:
    from PIL import Image, ImageTk, ImageFilter, ImageStat, ImageOps
    from PIL import Image as PILImage
    PIL_OK = True
except Exception:
    PIL_OK = False
try:
    import win32com.client
    import pythoncom
    WIN32_OK = True
except Exception:
    WIN32_OK = False
try:
    from win32com.propsys import propsys, pscon
    PROPSYS_OK = True
except Exception:
    try:
        import win32com.propsys as propsys
        PROPSYS_OK = True
    except Exception:
        PROPSYS_OK = False
# --- CACHE GLOBAL ---

# --- Funciones utilitarias (sin cambios) ---
def center_window(win, parent=None):
    try:
        win.update_idletasks()
        withdrawn = False
        try:
            withdrawn = str(win.state()) == 'withdrawn'
        except Exception:
            withdrawn = False
        if withdrawn:
            # Una ventana oculta reporta winfo_width()=200x200 (default de Tk),
            # no su tamaño real: medir por req + minsize para NO tener que
            # re-centrar (y saltar) después de mostrarse.
            ww = win.winfo_reqwidth()
            wh = win.winfo_reqheight()
            try:
                nums = re.findall(r'-?\d+', str(win.tk.call('wm', 'minsize', win)))
                if len(nums) >= 2:
                    ww = max(ww, int(nums[0]))
                    wh = max(wh, int(nums[1]))
            except Exception:
                pass
        else:
            ww = win.winfo_width()
            wh = win.winfo_height()
            if ww <= 1:
                ww = win.winfo_reqwidth()
            if wh <= 1:
                wh = win.winfo_reqheight()
        if ww <= 1:
            ww = 480
        if wh <= 1:
            wh = 480
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw - ww) // 2
        y = (sh - wh) // 2
        win.geometry(f"+{x}+{y}")
        # Seguridad: re-centra con el tamaño real si algo cambió al mapear.
        # Con la medida correcta calcula la misma posición => no hay salto.
        win.after(100, lambda: _recenter_window(win))
    except Exception:
        pass

def _recenter_window(win):
    try:
        if not win.winfo_exists():
            return
        ww = win.winfo_width()
        wh = win.winfo_height()
        if ww <= 1 or wh <= 1:
            return
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw - ww) // 2
        y = (sh - wh) // 2
        win.geometry(f"+{x}+{y}")
    except Exception:
        pass

# Pares de texto de estado ES/EN para que el mensaje naranja
# siempre se muestre en el idioma actual aunque se cambie en caliente
_STATUS_PAIRS = [
    ("Por favor espere", "Please wait"),
    ("Deshaciendo organización...", "Undoing organization..."),
]

def status_text(msg, english):
    for es, en in _STATUS_PAIRS:
        if msg in (es, en):
            return en if english else es
    return msg

def safe_icon(win, icon_path=ICON_FILE):
    icon_full_path = os.path.join(base_path, icon_path)
    try:
        win.iconbitmap(default=icon_full_path)
    except Exception:
        pass
    try:
        if PIL_OK:
            img = Image.open(icon_full_path)
            img = img.resize((32, 32), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            win.iconphoto(False, photo)
            win._icon_ref = photo
        else:
            photo = tk.PhotoImage(file=icon_full_path)
            win.iconphoto(False, photo)
            win._icon_ref = photo
    except Exception:
        pass

def load_image(path, max_width=None, max_height=None):
    img_full_path = os.path.join(base_path, path)
    if not os.path.exists(img_full_path) or not PIL_OK:
        return None
    try:
        img = Image.open(img_full_path)
        if max_width or max_height:
            img.thumbnail((max_width or img.width, max_height or img.height), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None

def ensure_single_instance():
    """Mutex de Windows: si ya hay una instancia, enfoca su ventana y sale.
    El mutex se libera solo al cerrar el proceso (sin archivos PID obsoletos)."""
    global _MUTEX_HANDLE
    try:
        import ctypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p)
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        ERROR_ALREADY_EXISTS = 183
        handle = kernel32.CreateMutexW(None, False, "Click2Folders_SingleInstance_v1")
        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            _focus_existing_window()
            try:
                kernel32.CloseHandle(handle)
            except Exception:
                pass
            return False
        _MUTEX_HANDLE = handle  # mantenerlo vivo durante la vida del proceso
        return True
    except Exception:
        return True

def _focus_existing_window():
    """Busca la ventana principal (en español o inglés) y la trae al frente."""
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        found = []
        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def _cb(hwnd, _lparam):
            try:
                if user32.IsWindowVisible(hwnd):
                    buf = ctypes.create_unicode_buffer(1024)
                    user32.GetWindowTextW(hwnd, buf, 1024)
                    if buf.value.startswith("Click2Folders"):
                        found.append(hwnd)
            except Exception:
                pass
            return True
        user32.EnumWindows(_cb, 0)
        for hwnd in found:
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.BringWindowToTop(hwnd)
            if not user32.SetForegroundWindow(hwnd):
                # Windows bloquea el foreground: simular tecla Alt lo permite
                user32.keybd_event(0x12, 0, 0, 0)
                user32.SetForegroundWindow(hwnd)
                user32.keybd_event(0x12, 0, 0x0002, 0)
        return bool(found)
    except Exception:
        return False

def _get_launch_count():
    """Lee y actualiza el contador de lanzamientos para mostrar donaciones cada 2 aperturas."""
    count_file = os.path.join(os.path.expanduser("~"), ".click2folders_launch_count.dat")
    try:
        if os.path.exists(count_file):
            with open(count_file, "r") as f:
                count = int(f.read().strip())
        else:
            count = 0
        count += 1
        with open(count_file, "w") as f:
            f.write(str(count))
        return count
    except Exception:
        return 0

def readable_month(m, english=False):
    if english:
        return ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"][m - 1]
    return ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"][m - 1]

DATE_PATTERN = re.compile(r'(\d{4})[-\s]?(\d{1,2})[-\s]?(\d{1,2})|(\d{4})\s*(\d{1,2})')
SCREENSHOT_PATTERN = re.compile(r'screenshot.*(\d{4})-(\d{2})-(\d{2})')
DAY_MONTH_YEAR_PATTERN = re.compile(r'(\d{1,2})[\s\-]?([a-zA-Z]+)[\s\-]?(\d{4})')
YEAR_MONTH_COMPACT_PATTERN = re.compile(r'(\d{4})(\d{2})(\d{2})')
DATE_TIME_PATTERN = re.compile(r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2})-(\d{1,2})-(\d{1,2})')
YEAR_TEXT_MONTH_DAY_PATTERN = re.compile(r'(\d{4})[\s\-]?([a-zA-Z]+)[\s\-]?(\d{1,2})')
COMPACT_DDMMYYYY_PATTERN = re.compile(r'(\d{2})(\d{2})(\d{4})')
SPANISH_LONG_DATE_PATTERN = re.compile(
    r'(\d{1,2})\s*de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\s*de\s+(\d{4})',
    re.IGNORECASE
)
# Mes(texto) Día [de] Año [consecutivo]  ej: "Oct 7 de 2012 2" / "Octubre 7 2012"
MONTH_DAY_YEAR_TEXT_PATTERN = re.compile(r'([a-zA-Z]+)[\s\-_]+(\d{1,2})\s*(?:de\s*)?(\d{4})(?:[\s\-_]+\d{1,3})?')
# Día Mes(texto) [de] Año [consecutivo]  ej: "7 Oct de 2012 2" / "7 de Octubre 2012"
DAY_MONTH_YEAR_TEXT_CONSEC_PATTERN = re.compile(r'(\d{1,2})\s*(?:de\s*)?([a-zA-Z]+)[\s\-_]+(?:de\s*)?(\d{4})(?:[\s\-_]+\d{1,3})?')

MONTH_DICT = {
    'enero': 1, 'ene': 1, 'jan': 1,
    'febrero': 2, 'feb': 2,
    'marzo': 3, 'mar': 3,
    'abril': 4, 'abr': 4, 'apr': 4,
    'mayo': 5, 'may': 5,
    'junio': 6, 'jun': 6,
    'julio': 7, 'jul': 7,
    'agosto': 8, 'ago': 8, 'aug': 8,
    'septiembre': 9, 'sep': 9, 'sept': 9, 'setiembre': 9, 'set': 9,
    'octubre': 10, 'oct': 10,
    'noviembre': 11, 'nov': 11,
    'diciembre': 12, 'dic': 12, 'dec': 12,
}

def _valid_date(year, month, day=1):
    try:
        if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
            return datetime(year, month, day)
    except ValueError:
        pass
    return None

def _parse_spanish_long_date(text):
    """Parsea fechas en español: '15 de enero de 2024' o '15 de Ene de 2024'"""
    if not text:
        return None
    m = SPANISH_LONG_DATE_PATTERN.search(text)
    if m:
        month_str = m.group(2).lower()
        if month_str in MONTH_DICT:
            return _valid_date(int(m.group(3)), MONTH_DICT[month_str], int(m.group(1)))
    return None

def extract_date_from_filename(filename: str):
    """Extrae la primera fecha válida encontrada en el nombre del archivo."""
    low = filename.lower()
    # Normalizar separadores para facilitar detección
    low_norm = re.sub(r'[_\-]', ' ', low)

    # 1. YYYYMMDD compacto (ej: 20130518)
    m = YEAR_MONTH_COMPACT_PATTERN.search(low)
    if m:
        dt = _valid_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if dt: return dt

    # 1b. Mes(texto) Día [de] Año [consecutivo]  ej: "Oct 7 de 2012 2" (consecutivo se ignora)
    m = MONTH_DAY_YEAR_TEXT_PATTERN.search(low)
    if m:
        month_str = m.group(1).lower()
        if month_str in MONTH_DICT:
            dt = _valid_date(int(m.group(3)), MONTH_DICT[month_str], int(m.group(2)))
            if dt: return dt

    # 1c. Día Mes(texto) [de] Año [consecutivo]  ej: "7 Oct de 2012 2" / "7 de Octubre 2012 3"
    m = DAY_MONTH_YEAR_TEXT_CONSEC_PATTERN.search(low)
    if m:
        month_str = m.group(2).lower()
        if month_str in MONTH_DICT:
            dt = _valid_date(int(m.group(3)), MONTH_DICT[month_str], int(m.group(1)))
            if dt: return dt

    # 2. DD[sep]MesTexto[sep]YYYY  ej: 18 Mayo 2013 / 18-Ene-2013 / 18_Enero_2013 / 18Mayo2013
    for text in [low_norm, low]:
        m = DAY_MONTH_YEAR_PATTERN.search(text)
        if m:
            month_str = re.sub(r'[ _\-]', '', m.group(2).lower())
            if month_str in MONTH_DICT:
                dt = _valid_date(int(m.group(3)), MONTH_DICT[month_str], int(m.group(1)))
                if dt: return dt

    # 3. YYYY[sep]MesTexto[sep]DD  ej: 2013 Mayo 18 / 2013_Mayo_18
    for text in [low_norm, low]:
        m = YEAR_TEXT_MONTH_DAY_PATTERN.search(text)
        if m:
            month_str = re.sub(r'[ _\-]', '', m.group(2).lower())
            if month_str in MONTH_DICT:
                dt = _valid_date(int(m.group(1)), MONTH_DICT[month_str], int(m.group(3)))
                if dt: return dt

    # 4. DDMMYYYY compacto ej: 18052013
    m = COMPACT_DDMMYYYY_PATTERN.search(low)
    if m:
        dt = _valid_date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        if dt: return dt

    # 5. DATE_TIME_PATTERN  ej: 2013-05-18 11-05-00
    m = DATE_TIME_PATTERN.search(low)
    if m:
        dt = _valid_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if dt: return dt

    # 6. DATE_PATTERN general  ej: 2013-05-18 / 2013_05
    m = DATE_PATTERN.search(low)
    if m:
        year = int(m.group(1) or m.group(4))
        month = int(m.group(2) or m.group(5))
        dt = _valid_date(year, month)
        if dt: return dt

    # 7. SCREENSHOT_PATTERN
    m = SCREENSHOT_PATTERN.search(low)
    if m:
        dt = _valid_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if dt: return dt

    return None

def iter_all_files(folder):
    try:
        for entry in os.scandir(folder):
            if entry.is_file() and not entry.name.startswith('.'):
                yield os.path.join(folder, entry.name)
    except Exception:
        pass

def count_all_files(folder):
    return sum(1 for _ in iter_all_files(folder))

def count_subfolders(folder_path):
    """Cuenta las subcarpetas de primer nivel."""
    try:
        return sum(1 for e in os.scandir(folder_path) if e.is_dir())
    except Exception:
        return 0

PROPERTY_CACHE = {}
PROPERTY_INDEX_CACHE = {}  # cache separado para get_property_index (evita conflicto de tipos con PROPERTY_CACHE)
FILE_PROPS_CACHE = {}  # path -> {"Fecha de captura": str, "Medio creado": str}
SHELL = None  # Shell.Application del hilo principal (compatibilidad)
_thread_local = threading.local()

def _get_thread_ns_cache():
    """Devuelve el cache de namespaces del hilo actual (cada hilo tiene el suyo)."""
    cache = getattr(_thread_local, 'ns_cache', None)
    if cache is None:
        cache = {}
        _thread_local.ns_cache = cache
    return cache

def _get_thread_shell():
    """Devuelve una instancia de Shell.Application creada en el hilo ACTUAL.
    Los objetos COM están vinculados al apartment del hilo donde se crean;
    reutilizar una instancia creada en otro hilo causa que ciertas propiedades
    (como 'Medio creado' en videos) devuelvan valores vacíos de forma
    inconsistente. Cada hilo de trabajo debe tener su propia instancia."""
    if not WIN32_OK:
        return None
    inst = getattr(_thread_local, 'shell', None)
    if inst is None:
        try:
            inst = win32com.client.Dispatch("Shell.Application")
            _thread_local.shell = inst
        except Exception:
            return None
    return inst

def get_property_indices(folder, prop_name):
    """Devuelve TODOS los índices de columna candidatos que coincidan con prop_name
    (exactos primero, luego parciales). Prueba también alias en otros idiomas.
    Necesario porque el índice de una propiedad puede no tener valor para cierto tipo
    de archivo aunque el nombre de columna coincida."""
    cache_key = (os.path.normcase(os.path.abspath(folder)), prop_name.lower())
    if cache_key in PROPERTY_CACHE:
        return PROPERTY_CACHE[cache_key]
    if not WIN32_OK:
        return []
    try:
        sh = _get_thread_shell()
        if sh is None:
            return []
        ns = sh.NameSpace(folder)
        names_to_try = [prop_name] + COLUMN_NAME_ALIASES.get(prop_name, [])
        exact_matches = []
        partial_matches = []
        for name in names_to_try:
            target = name.strip().lower()
            for i in range(0, 500):
                detail_name = ns.GetDetailsOf(None, i)
                if not detail_name:
                    continue
                name_norm = detail_name.strip().lower()
                if name_norm == target:
                    if i not in exact_matches:
                        exact_matches.append(i)
                elif target in name_norm or name_norm in target:
                    if i not in partial_matches:
                        partial_matches.append(i)
        indices = exact_matches + partial_matches
        PROPERTY_CACHE[cache_key] = indices
        return indices
    except Exception:
        PROPERTY_CACHE[cache_key] = []
        return []

# Column name aliases para compatibilidad con Windows en otros idiomas
COLUMN_NAME_ALIASES = {
    "Fecha de captura": ["Date taken", "Date created", "Date acquired"],
    "Medio creado": ["Date encoded", "Media created", "Creation date"],
}

def _try_column_names(ns, names):
    """Busca el índice de columna para cualquiera de los nombres dados (exact match)."""
    for name in names:
        target = name.strip().lower()
        for i in range(0, 500):
            detail_name = ns.GetDetailsOf(None, i)
            if detail_name and detail_name.strip().lower() == target:
                return i
    return None

def get_property_index(folder, prop_name):
    """Busca el índice exacto de una columna en el Shell namespace.
    Prueba también alias en otros idiomas si no encuentra el nombre principal.
    Usa PROPERTY_INDEX_CACHE separado para no confundir tipos con get_property_indices."""
    cache_key = (os.path.normcase(os.path.abspath(folder)), prop_name.lower())
    if cache_key in PROPERTY_INDEX_CACHE:
        return PROPERTY_INDEX_CACHE[cache_key]
    if not WIN32_OK:
        return None
    try:
        sh = _get_thread_shell()
        if sh is None:
            return None
        ns = sh.NameSpace(folder)
        names_to_try = [prop_name] + COLUMN_NAME_ALIASES.get(prop_name, [])
        idx = _try_column_names(ns, names_to_try)
        PROPERTY_INDEX_CACHE[cache_key] = idx
        return idx
    except Exception:
        PROPERTY_INDEX_CACHE[cache_key] = None
        return None

def _get_cached_namespace(dir_path, force_refresh=False):
    """Namespace cacheado por hilo. Usa el Shell.Application del hilo actual
    (via _get_thread_shell) para evitar problemas de apartment COM."""
    cache = _get_thread_ns_cache()
    if not force_refresh and dir_path in cache:
        return cache[dir_path]
    sh = _get_thread_shell()
    if sh is None:
        return None
    ns = sh.NameSpace(dir_path)
    cache[dir_path] = ns
    return ns

def _clean_date_str(date_str):
    if not date_str:
        return None
    date_str = date_str.replace('\u200e', '').replace('\u200f', '').replace('\xa0', ' ').replace('a. m.', 'AM').replace('p. m.', 'PM').replace('a.m.', 'AM').replace('p.m.', 'PM')
    return date_str.strip() or None

def _get_item_by_name(folder, file_name):
    """Obtiene un item del folder usando Filter (más confiable que ParseName)."""
    try:
        items = folder.Items()
        items.Filter(0x80, file_name)
        if items.Count > 0:
            return items.Item(0)
    except Exception:
        pass
    try:
        return folder.ParseName(file_name)
    except Exception:
        pass
    return None

def _read_props_with_namespace(folder, file_name, dir_path, prop_names):
    """Intenta leer las propiedades dado un namespace. Prueba TODOS los índices
    candidatos por propiedad hasta encontrar un valor no vacío (algunos archivos
    no tienen valor en la primera columna candidata aunque el nombre coincida)."""
    item = _get_item_by_name(folder, file_name)
    if item is None:
        return None
    result = {}
    for prop_name in prop_names:
        indices = get_property_indices(dir_path, prop_name)
        value = None
        for index in indices:
            try:
                date_str = folder.GetDetailsOf(item, index)
                cleaned = _clean_date_str(date_str)
                if cleaned:
                    value = cleaned
                    break
            except Exception:
                continue
        # Fallback: ExtendedProperty directo por nombre (funciona aunque la columna no esté en la vista)
        if not value:
            try:
                raw = item.ExtendedProperty(prop_name)
                if raw:
                    value = _clean_date_str(str(raw))
            except Exception:
                pass
        result[prop_name] = value
    return result

def _get_props_direct(path, prop_names):
    """Lee propiedades vía Property Store API (más directa, funciona aunque ParseName falle).
    Usa GPS_DEFAULT (solo lectura) en vez de GPS_READWRITE para evitar fallos
    de permisos en archivos de solo lectura o protegidos."""
    if not PROPSYS_OK:
        return None
    try:
        from win32com.shell import shell, shellcon
        ps = shell.SHGetPropertyStoreFromParsingName(
            path, None, shellcon.GPS_DEFAULT, propsys.IID_IPropertyStore
        )
        result = {}
        for prop_name in prop_names:
            try:
                if prop_name == "Medio creado":
                    pkey_name = "System.Media.DateEncoded"
                elif prop_name == "Fecha de captura":
                    pkey_name = "System.Photo.DateTaken"
                else:
                    result[prop_name] = None
                    continue
                pkey = propsys.PSGetPropertyKeyFromName(pkey_name)
                val = ps.GetValue(pkey)
                if val is not None:
                    raw = val.GetValue() if hasattr(val, 'GetValue') else str(val)
                    result[prop_name] = str(raw) if raw is not None else None
                else:
                    result[prop_name] = None
            except Exception:
                result[prop_name] = None
        return result
    except Exception:
        return None

def _get_media_date_pkey(path):
    """Lee System.Media.DateEncoded vía Property Store API (solo lectura).
    Es la ruta más directa y locale-independiente para obtener la fecha
    de creación de un archivo multimedia.
    IMPORTANTE: Windows a veces devuelve fechas "epoch" corruptas (1969,
    1970, 1601, etc.) cuando el valor real es nulo o inválido internamente.
    Por eso TODA fecha obtenida aquí se valida contra un rango razonable
    (1990 - año actual) antes de devolverla."""
    if not PROPSYS_OK:
        return None
    cur_year = datetime.now().year

    def _reasonable(dt):
        # Rango más estricto que el general (1900+) porque aquí es donde
        # aparecen los falsos positivos de epoch corrupto (1969/1970/1601).
        return dt is not None and 1990 <= dt.year <= cur_year

    try:
        from win32com.shell import shell, shellcon
        ps = shell.SHGetPropertyStoreFromParsingName(
            path, None, shellcon.GPS_DEFAULT, propsys.IID_IPropertyStore
        )
        pkey = propsys.PSGetPropertyKeyFromName("System.Media.DateEncoded")
        val = ps.GetValue(pkey)
        if val is None:
            return None
        raw = val.GetValue() if hasattr(val, 'GetValue') else str(val)
        if raw is None:
            return None
        # Si ya es datetime, validar rango antes de devolverlo
        if isinstance(raw, datetime):
            return raw if _reasonable(raw) else None
        # Si es string, intentar parsear y validar
        s = str(raw).strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%Y:%m:%d"):
            try:
                dt = datetime.strptime(s[:10], fmt)
                if _reasonable(dt):
                    return dt
            except Exception:
                continue
        m = re.search(r'(\d{1,2})\s*[-/]\s*(\d{4})', s)
        if m:
            dt = _valid_date(int(m.group(2)), int(m.group(1)), 1)
            if _reasonable(dt):
                return dt
        return None
    except Exception:
        return None

def get_file_properties(path, prop_names):
    """Lee múltiples propiedades de un archivo en UNA sola operación COM (mucho más rápido).
    Reintenta con un namespace fresco si el primero falla (el namespace puede quedar
    desactualizado en COM si la carpeta cambió de contenido, ej. tras mover archivos)."""
    if not WIN32_OK:
        return {p: None for p in prop_names}
    cache_key = os.path.normcase(os.path.abspath(path))
    if cache_key in FILE_PROPS_CACHE:
        cached = FILE_PROPS_CACHE[cache_key]
        if all(p in cached for p in prop_names):
            return cached
    dir_path = os.path.dirname(path)
    file_name = os.path.basename(path)
    result = None
    # Intento 1: namespace cacheado
    try:
        folder = _get_cached_namespace(dir_path)
        result = _read_props_with_namespace(folder, file_name, dir_path, prop_names)
    except Exception:
        result = None
    # Intento 2: namespace fresco si el primero falló o no encontró el item
    if result is None:
        try:
            folder = _get_cached_namespace(dir_path, force_refresh=True)
            result = _read_props_with_namespace(folder, file_name, dir_path, prop_names)
        except Exception:
            result = None
    # Intento 3: Property Store API directa (fallback más confiable)
    if result is None or all(v is None for v in result.values()):
        direct = _get_props_direct(path, prop_names)
        if direct is not None and any(v is not None for v in direct.values()):
            result = direct
    if result is None:
        result = {p: None for p in prop_names}
    FILE_PROPS_CACHE[cache_key] = result
    return result

def get_property(path, prop_name):
    """Mantiene compatibilidad: lee una sola propiedad usando el cache combinado."""
    props = get_file_properties(path, [prop_name])
    return props.get(prop_name)

def _parse_moov_mvhd(data, offset, size, header_len=8):
    """Busca el box mvhd dentro de un box moov y devuelve la fecha si la encuentra.
    Maneja tamaño extendido de 64 bits tanto en el propio 'moov' (header_len)
    como en los sub-átomos internos (mvhd y otros que puedan venir antes)."""
    moov_end = min(offset + size, len(data))
    moov_data = data[offset:moov_end]
    sub_pos = header_len
    n = len(moov_data)
    while sub_pos + 8 <= n:
        sub_size = struct.unpack('>I', moov_data[sub_pos:sub_pos+4])[0]
        sub_type = moov_data[sub_pos+4:sub_pos+8]
        sub_header_len = 8
        if sub_size == 1:
            if sub_pos + 16 > n:
                break
            sub_size = struct.unpack('>Q', moov_data[sub_pos+8:sub_pos+16])[0]
            sub_header_len = 16
        elif sub_size == 0:
            sub_size = n - sub_pos
        if sub_type == b'mvhd':
            body_start = sub_pos + sub_header_len
            if body_start >= n:
                return None
            version = moov_data[body_start]
            try:
                if version == 0:
                    time_val = struct.unpack('>I', moov_data[body_start+4:body_start+8])[0]
                else:
                    time_val = struct.unpack('>Q', moov_data[body_start+4:body_start+12])[0]
            except struct.error:
                return None
            if time_val == 0:
                return None
            epoch = datetime(1904, 1, 1)
            try:
                dt = epoch + timedelta(seconds=time_val)
            except (OverflowError, ValueError):
                return None
            # Validar que la fecha resultante sea razonable. Si el átomo
            # 'mvhd' se leyó desalineado (por una coincidencia falsa de la
            # firma 'moov' en datos binarios comprimidos), el timestamp
            # calculado puede caer fuera de cualquier rango con sentido
            # para un archivo multimedia real (ej. 1969, 1970, 2040+).
            cur_year_check = datetime.now().year
            if not (1995 <= dt.year <= cur_year_check):
                return None
            return dt
        if sub_size < sub_header_len:
            break
        sub_pos += sub_size
    return None

def _scan_for_moov(data):
    """Busca el box 'moov' en el buffer y extrae la fecha vía mvhd.
    IMPORTANTE: no asume que el buffer empieza alineado con un límite de átomo
    (esto pasa cuando se lee solo el final de archivos grandes, donde el buffer
    puede empezar en medio del payload binario de 'mdat'). Por eso busca la
    firma 'moov' como texto en cualquier posición del buffer."""
    idx = 0
    while True:
        idx = data.find(b'moov', idx)
        if idx == -1 or idx < 4:
            break
        # El tamaño del box está 4 bytes antes del tipo 'moov'
        box_size = struct.unpack('>I', data[idx-4:idx])[0]
        header_len = 8
        box_start = idx - 4
        if box_size == 1:
            # tamaño extendido de 64 bits, ubicado justo después del header normal
            if idx + 12 <= len(data):
                box_size = struct.unpack('>Q', data[idx+4:idx+12])[0]
                header_len = 16
        dt = _parse_moov_mvhd(data, box_start, box_size if box_size > 0 else len(data) - box_start, header_len)
        if dt:
            return dt
        idx += 4
    return None

def _search_date_in_binary(data):
    """Busca fechas en texto plano dentro del binario (formato YYYY-MM-DD,
    YYYY/MM/DD, YYYY:MM:DD). Solo se usa como último recurso para
    contenedores no-MP4 (MKV, WebM, etc.) que incluyen metadata en texto.

    IMPORTANTE: este fallback es propenso a falsos positivos, porque
    secuencias de bytes en video/audio comprimido pueden coincidir por
    azar con el patrón de una fecha. Por eso:
    - Exige un año razonable y RECIENTE (2000+), no solo "válido" (1900+),
      ya que coincidencias accidentales en binario casi nunca caen en
      rangos de años muy antiguos de forma intencional.
    - Exige que el match esté rodeado de texto imprimible (no en medio
      de un bloque de bytes binarios), lo cual indica que es metadata
      real y no una coincidencia aleatoria.
    """
    try:
        text = data.decode('utf-8', errors='ignore')
    except Exception:
        return None
    cur_year = datetime.now().year
    for m in re.finditer(r'(\d{4})[-/:](\d{2})[-/:](\d{2})', text):
        try:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if not (2000 <= y <= cur_year):
                continue
            # Verificar que el contexto alrededor sea texto imprimible
            # (metadata real), no una coincidencia accidental en binario
            start = max(0, m.start() - 5)
            end = min(len(text), m.end() + 5)
            context = text[start:end]
            printable_ratio = sum(1 for c in context if c.isprintable()) / max(1, len(context))
            if printable_ratio < 0.8:
                continue
            dt = _valid_date(y, mo, d)
            if dt:
                return dt
        except Exception:
            continue
    return None

# Meses en inglés usados en el formato de fecha tipo C (asctime) que usa AVI
_AVI_MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}

def _read_avi_creation_date(path):
    """Lee la fecha de creación del chunk 'IDIT' en archivos RIFF/AVI.
    El formato típico es texto estilo C: 'Fri Feb 03 07:48:12 2012'.
    Este chunk normalmente está cerca del inicio del archivo (dentro de
    la cabecera 'hdrl'), así que basta con leer los primeros KB."""
    try:
        with open(path, 'rb') as f:
            header = f.read(12)
            if header[0:4] != b'RIFF' or header[8:12] != b'AVI ':
                return None
            data = header + f.read(65536)  # 64 KB suele ser de sobra para la cabecera
    except Exception:
        return None

    idx = data.find(b'IDIT')
    if idx == -1:
        return None
    try:
        # Estructura del chunk: 'IDIT' + size(4 bytes LE) + datos
        size = struct.unpack('<I', data[idx+4:idx+8])[0]
        text = data[idx+8:idx+8+size].decode('ascii', errors='ignore').strip().strip('\x00')
        # Formato típico: "Fri Feb 03 07:48:12 2012"
        m = re.search(
            r'([A-Za-z]{3})\s+(\d{1,2})\s+(\d{1,2}):(\d{2}):(\d{2})\s+(\d{4})',
            text
        )
        if m:
            month_str = m.group(1).lower()
            month = _AVI_MONTH_MAP.get(month_str)
            if month:
                day = int(m.group(2))
                year = int(m.group(6))
                dt = _valid_date(year, month, day)
                if dt:
                    return dt
        # Formato alternativo: YYYY-MM-DD o similar ya cubierto por _search_date_in_binary
        return _search_date_in_binary(text.encode('utf-8', errors='ignore'))
    except Exception:
        return None

def _read_file_creation_date(path):
    """Lee la fecha de creación directamente del archivo binario (sin COM),
    detectando el formato del contenedor por su firma:
    - RIFF/AVI: lee el chunk 'IDIT' (fecha en texto tipo C).
    - MP4/MOV/QuickTime (ftyp/moov): lee el átomo 'mvhd'.
    - Otros formatos: intenta encontrar fechas en texto plano dentro
      del archivo como último recurso (cabecera y cola)."""
    try:
        with open(path, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
            f.seek(0)
            signature = f.read(12)
    except Exception:
        return None

    # --- Formato RIFF/AVI ---
    if signature[0:4] == b'RIFF' and signature[8:12] == b'AVI ':
        return _read_avi_creation_date(path)

    # --- Formato MP4/MOV/QuickTime (cualquier variante con ftyp o moov) ---
    try:
        with open(path, 'rb') as f:
            head_size = min(file_size, 262144)  # 256 KB
            f.seek(0)
            head = f.read(head_size)
            tail_size = min(file_size, 1048576)  # 1 MB
            f.seek(max(0, file_size - tail_size))
            tail = f.read(tail_size)
    except Exception:
        return None

    dt = _scan_for_moov(head)
    if dt:
        return dt
    dt = _scan_for_moov(tail)
    if dt:
        return dt

    # Fallback genérico: buscar fechas en texto plano dentro del archivo
    # (cubre otros contenedores como MKV, WebM, formatos con metadata en texto)
    for buf in (head, tail):
        dt = _search_date_in_binary(buf)
        if dt:
            return dt
    return None

def _get_property_legacy(path, prop_name):
    """Versión legacy con Shell.Application por-hilo + Filter/ParseName (más confiable).
    Usa una instancia de Shell.Application creada en el hilo actual, porque los
    objetos COM están vinculados al apartment del hilo donde se crean."""
    if not WIN32_OK:
        return None
    shell = _get_thread_shell()
    if shell is None:
        return None
    try:
        dir_path = os.path.dirname(path)
        file_name = os.path.basename(path)
        index = get_property_index(dir_path, prop_name)
        if index is None:
            return None
        folder = shell.NameSpace(dir_path)
        item = _get_item_by_name(folder, file_name)
        if item is None:
            return None
        date_str = folder.GetDetailsOf(item, index)
        if date_str:
            date_str = date_str.replace('\u200e', '').replace('\u200f', '').replace('\xa0', ' ').replace('a. m.', 'AM').replace('p. m.', 'PM').replace('a.m.', 'AM').replace('p.m.', 'PM')
            return date_str.strip()
        return None
    except Exception:
        return None

# --- SISTEMA DE DETECCIÓN ORIGINAL (v1.8.2) ---
def has_year_subdirs(folder_path):
    """Detecta si la carpeta tiene subdirectorios con nombre de año (4 dígitos 1900-2100)."""
    try:
        for entry in os.scandir(folder_path):
            if entry.is_dir():
                name = entry.name
                if name.isdigit() and len(name) == 4 and 1900 <= int(name) <= 2100:
                    return True
    except Exception:
        pass
    return False

def is_folder_organized(folder_path):
    try:
        entries = list(os.scandir(folder_path))
        year_folders = []
        months = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
        for entry in entries:
            if entry.is_dir():
                dir_name = entry.name
                if dir_name.isdigit() and len(dir_name) == 4 and 1900 <= int(dir_name) <= 2100:
                    year_path = os.path.join(folder_path, dir_name)
                    try:
                        month_entries = list(os.scandir(year_path))
                        month_folders = [e for e in month_entries if e.is_dir() and
                                         (e.name[:1].isdigit() or e.name.lower() in months)]
                        if month_folders:
                            year_folders.append(dir_name)
                    except:
                        continue
        return len(year_folders) > 0
    except Exception:
        return False

def undo_organization(folder_path):
    moved_count = 0
    try:
        entries = list(os.scandir(folder_path))
        for entry in entries:
            if entry.is_dir():
                dir_name = entry.name
                if dir_name.isdigit() and len(dir_name) == 4 and 1900 <= int(dir_name) <= 2100:
                    year_path = os.path.join(folder_path, dir_name)
                    try:
                        month_entries = list(os.scandir(year_path))
                        for month_entry in month_entries:
                            if month_entry.is_dir():
                                month_path = os.path.join(year_path, month_entry.name)
                                for file_path in iter_all_files(month_path):
                                    file_name = os.path.basename(file_path)
                                    target_path = os.path.join(folder_path, file_name)
                                    target_path = _dedupe_name_static(target_path)
                                    shutil.move(file_path, target_path)
                                    moved_count += 1
                                try:
                                    if not list(os.scandir(month_path)):
                                        os.rmdir(month_path)
                                except:
                                    pass
                        try:
                            if not list(os.scandir(year_path)):
                                os.rmdir(year_path)
                        except:
                            pass
                    except Exception as e:
                        print(f"Error procesando año {dir_name}: {e}")
        return moved_count
    except Exception as e:
        print(f"Error deshaciendo organización: {e}")
        return moved_count

def _dedupe_name_static(path):
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(path):
        path = f"{base} ({i}){ext}"
        i += 1
    return path

def iter_all_files_including_organized(folder):
    try:
        for entry in os.scandir(folder):
            if entry.is_file() and not entry.name.startswith('.'):
                yield os.path.join(folder, entry.name)
        for entry in os.scandir(folder):
            if entry.is_dir():
                dir_name = entry.name
                if dir_name.isdigit() and len(dir_name) == 4 and 1900 <= int(dir_name) <= 2100:
                    year_path = os.path.join(folder, dir_name)
                    try:
                        months = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
                        for month_entry in os.scandir(year_path):
                            if month_entry.is_dir() and (month_entry.name[:1].isdigit() or month_entry.name.lower() in months):
                                month_path = os.path.join(year_path, month_entry.name)
                                for file_entry in os.scandir(month_path):
                                    if file_entry.is_file() and not file_entry.name.startswith('.'):
                                        yield os.path.join(month_path, file_entry.name)
                    except Exception:
                        pass
    except Exception:
        pass

def count_all_files_including_organized(folder):
    return sum(1 for _ in iter_all_files_including_organized(folder))

def _long_path(p):
    """En Windows antepone el prefijo especial que usa Windows para rutas
    largas, evitando que se recorten al limite clasico de 260 caracteres.
    Es facil llegar a ese limite con carpetas de ano/mes y nombres de
    archivo largos. En otros sistemas operativos no cambia nada."""
    if os.name != "nt":
        return p
    try:
        ap = os.path.abspath(p)
    except Exception:
        return p
    prefix = "\\\\?\\"
    if ap.startswith(prefix):
        return ap
    if ap.startswith("\\\\"):
        return prefix + "UNC\\" + ap[2:]
    return prefix + ap

def count_folder_contents(folder):
    """Cuenta las subcarpetas directas de 'folder' y el total de archivos que
    contiene, sueltos en la raiz o dentro de cualquiera de sus subcarpetas
    (a cualquier profundidad)."""
    folder_lp = _long_path(folder)
    subfolders = 0
    try:
        for entry in os.scandir(folder_lp):
            if entry.is_dir():
                subfolders += 1
    except Exception:
        pass
    files = 0
    try:
        for _root, _dirs, filenames in os.walk(folder_lp):
            files += sum(1 for fn in filenames if not fn.startswith('.'))
    except Exception:
        pass
    return files, subfolders

def get_status_text(folder, english=False):
    """Generate status text showing folder contents."""
    files, subfolders = count_folder_contents(folder)
    parts = []
    if subfolders > 0:
        parts.append(f"{subfolders} {'folders' if english else 'carpetas'}")
    if files > 0:
        parts.append(f"{files} {'files' if english else 'archivos'}")
    if parts:
        return ", ".join(parts)
    return "0 items"

class _ColumnResizer:
    """Permite redimensionar columnas del Treeview arrastrando los bordes."""

    # Colores de las líneas divisorias verticales entre columnas
    LINE_COLOR_HEAD = "#ffffff"   # blanco, sobre el encabezado azul
    LINE_COLOR_BODY = "#9ca3af"   # gris, sobre las filas

    def __init__(self, tree, columns, locked=("sel",)):
        self.tree = tree
        self.columns = list(columns)
        # Columnas cuyo borde derecho es fijo: no se puede mover y no muestra el
        # cursor de doble flecha (Sel solo tiene el checkbox). La línea sí se ve.
        self._locked = {i for i, c in enumerate(self.columns) if c in locked}
        self._drag_col = None
        self._drag_start_x = 0
        self._drag_start_width = 0
        self._drag_start_status_width = 0
        self._hit_margin = 6
        self._lines = []          # pares (línea del encabezado, línea de las filas)
        self._head_h = None       # alto del encabezado
        self._last_sig = None
        self._ok = False          # True cuando las líneas ya quedaron colocadas

        self.tree.bind("<Motion>", self._on_motion, add="+")
        self.tree.bind("<Button-1>", self._on_press, add="+")
        self.tree.bind("<B1-Motion>", self._on_drag, add="+")
        self.tree.bind("<ButtonRelease-1>", self._on_release, add="+")
        self.tree.bind("<Leave>", lambda e: self.tree.configure(cursor=""), add="+")
        self.tree.bind("<Configure>", lambda e: self.tree.after_idle(self.update_lines), add="+")
        self.tree.bind("<Map>", lambda e: self.tree.after_idle(self.update_lines), add="+")
        # Al abrirse la ventana por primera vez, si las líneas aún no están, se reintenta
        self.tree.bind("<Expose>", lambda e: (not self._ok) and self.tree.after_idle(self.update_lines), add="+")
        self.tree.after(150, self._watch)

    # ------------------------------------------------------------------
    # Líneas divisorias verticales (una por cada borde entre columnas).
    # Son marcos de 1px puestos justo sobre la unión de las columnas: blancos
    # en el encabezado y grises en las filas. No hay línea en el borde derecho
    # de la última columna (Estado) porque ahí no se puede mover nada.
    # ------------------------------------------------------------------
    class _FwdEvent:
        """Evento simplificado para pasar al Treeview los clics hechos sobre una línea."""
        def __init__(self, x, y, x_root, y_root):
            self.x, self.y, self.x_root, self.y_root = x, y, x_root, y_root

    def _forward(self, handler):
        def _h(e):
            ev = self._FwdEvent(e.x_root - self.tree.winfo_rootx(),
                                e.y_root - self.tree.winfo_rooty(),
                                e.x_root, e.y_root)
            handler(ev)
            return "break"
        return _h

    def _make_line(self, color, locked=False):
        if locked:
            # Línea fija: solo se ve; cursor normal y sin arrastre
            return tk.Frame(self.tree, width=1, height=1, bg=color, bd=0,
                            highlightthickness=0, cursor="arrow")
        line = tk.Frame(self.tree, width=1, height=1, bg=color, bd=0,
                        highlightthickness=0, cursor="sb_h_double_arrow")
        # Un clic o arrastre sobre la línea funciona igual que sobre el borde de la columna
        line.bind("<Motion>", self._forward(self._on_motion))
        line.bind("<ButtonPress-1>", self._forward(self._on_press))
        line.bind("<B1-Motion>", self._forward(self._on_drag))
        line.bind("<ButtonRelease-1>", self._forward(self._on_release))
        return line

    def _header_height(self):
        """Mide el alto del encabezado. Devuelve None si el Treeview aún no está dibujado."""
        h = 0
        try:
            while h < 80 and self.tree.identify_region(5, h) == "heading":
                h += 1
            if not (10 < h < 80):
                # Plan B: la primera fila empieza justo debajo del encabezado
                h = 0
                children = self.tree.get_children()
                if children:
                    box = self.tree.bbox(children[0])
                    if box and 10 < box[1] < 80:
                        h = box[1]
        except Exception:
            h = 0
        if 10 < h < 80:
            self._head_h = h
            return h
        return self._head_h    # última medida buena (o None si nunca se pudo medir)

    def update_lines(self):
        """Coloca las líneas sobre las uniones. Devuelve True si quedaron colocadas."""
        ok = False
        try:
            tw = self.tree.winfo_width()
            th = self.tree.winfo_height()
            hh = self._header_height()
            if tw > 10 and th > 10 and hh:
                positions = self._get_positions()
                while len(self._lines) < len(positions):
                    fixed = len(self._lines) in self._locked
                    self._lines.append((self._make_line(self.LINE_COLOR_HEAD, fixed),
                                        self._make_line(self.LINE_COLOR_BODY, fixed)))
                for (line_head, line_body), px in zip(self._lines, positions):
                    x = px - 1     # último píxel de la columna, justo en la unión con la siguiente
                    if 0 < x < tw - 1:
                        line_head.place(x=x, y=0, width=1, height=hh)
                        line_body.place(x=x, y=hh, width=1, height=max(1, th - hh))
                    else:
                        line_head.place_forget()
                        line_body.place_forget()
                ok = True
        except Exception:
            ok = False
        self._ok = ok
        return ok

    def _watch(self):
        """Cada 150 ms revisa si cambió el ancho de alguna columna (o si las líneas
        todavía no se han podido colocar, por ejemplo al abrir el programa) y las reubica."""
        try:
            sig = (tuple(self.tree.column(c)["width"] for c in self.columns),
                   self.tree.winfo_width(), self.tree.winfo_height())
            if sig != self._last_sig or not self._ok:
                if self.update_lines():
                    self._last_sig = sig
            self.tree.after(150, self._watch)
        except Exception:
            pass    # el Treeview ya no existe

    def _get_positions(self):
        positions = []
        x = 0
        for i, col in enumerate(self.columns):
            x += self.tree.column(col)["width"]
            if i < len(self.columns) - 1:
                positions.append(x)
        return positions

    def _on_motion(self, event):
        if self._drag_col is not None:
            return
        x = event.x
        for i, px in enumerate(self._get_positions()):
            if i in self._locked:
                continue    # borde fijo (Sel): no muestra el cursor de doble flecha
            if abs(x - px) <= self._hit_margin:
                self.tree.configure(cursor="sb_h_double_arrow")
                return
        self.tree.configure(cursor="")
        # Bordes que no se pueden mover (derecho de Estado y el de Sel): se corta el
        # evento para que Tk no vuelva a mostrar el cursor de doble flecha
        if self._is_fixed_edge(event.x, event.y):
            return "break"

    def _is_fixed_edge(self, x, y):
        """True si (x, y) está sobre un borde que no se puede mover: el borde derecho
        de la última columna (Estado) o el de una columna fija (Sel)."""
        if self.tree.identify_region(x, y) != "separator":
            return False
        edges = self._get_positions() + [sum(self.tree.column(c)["width"] for c in self.columns)]
        nearest = min(range(len(edges)), key=lambda i: abs(x - edges[i]))
        return nearest == len(edges) - 1 or nearest in self._locked

    def _on_press(self, event):
        positions = self._get_positions()
        if not positions:
            return None
        x = event.x
        region = self.tree.identify_region(event.x, event.y)
        # Borde (separador) más cercano al punto donde se hizo clic
        nearest = min(range(len(positions)), key=lambda i: abs(x - positions[i]))
        dist = abs(x - positions[nearest])
        # En el encabezado el separador es un poco más ancho que en las filas
        margin = max(self._hit_margin, 12) if region == "separator" else self._hit_margin
        if nearest in self._locked:
            # Borde fijo (Sel): no se arrastra. En el encabezado se bloquea el
            # redimensionado nativo de Tk; en las filas el clic sigue su curso normal
            # (así el checkbox se marca aunque se haga clic cerca de la línea).
            if region == "separator" and dist <= margin:
                return "break"
            return None
        if dist <= margin:
            self._drag_col = nearest
            self._drag_start_x = event.x_root
            self._drag_start_width = self.tree.column(self.columns[nearest])["width"]
            self._drag_start_status_width = self.tree.column("status")["width"]
            return "break"
        if region == "separator":
            # Separador que no se puede mover (borde exterior): se bloquea el
            # redimensionado nativo para que no rompa el ajuste de columnas
            return "break"
        return None

    def _on_drag(self, event):
        if self._drag_col is None:
            return
        dx = event.x_root - self._drag_start_x
        col = self.columns[self._drag_col]
        try:
            min_w = int(self.tree.column(col)["minwidth"])
        except Exception:
            min_w = 30
        min_w = max(30, min_w)
        new_width = max(min_w, self._drag_start_width + dx)
        try:
            tw = self.tree.winfo_width()
            if tw > 10:
                # Evita que Estado quede más angosta de 60px (no se sale del treeview)
                fixed = sum(self.tree.column(c)["width"] for c in self.columns
                            if c != "status" and c != col)
                max_width = tw - fixed - 60
                new_width = max(min_w, min(new_width, max_width))
            self.tree.column(col, width=new_width)
            other = sum(self.tree.column(c)["width"] for c in self.columns if c != "status")
            new_status = max(60, tw - other)
            self.tree.column("status", width=new_status)
        except Exception:
            pass
        self.update_lines()

    def _on_release(self, event):
        self._drag_col = None
        self.after_correct_last_col()
        # Al soltar el clic, Tk vuelve a poner el cursor de doble flecha sobre cualquier
        # separador, incluido el borde derecho de Estado (que no se puede mover).
        # Se corrige justo después de que Tk termine de procesar el evento.
        x, y = event.x, event.y

        def _fix_cursor():
            try:
                if self._is_fixed_edge(x, y):
                    self.tree.configure(cursor="")
            except Exception:
                pass
        self.tree.after_idle(_fix_cursor)

    def after_correct_last_col(self):
        def _correct():
            try:
                tw = self.tree.winfo_width()
                if tw <= 10:
                    return
                other = sum(self.tree.column(c)["width"] for c in self.columns if c != "status")
                correct_status = max(60, tw - other)
                current = self.tree.column("status")["width"]
                if current != correct_status:
                    self.tree.column("status", width=correct_status)
                self.update_lines()
            except Exception:
                pass
        self.tree.after_idle(_correct)


class OneShotWindow:
    def __init__(self):
        self.win = None

    def exists(self):
        return self.win and self.win.winfo_exists()

    def destroy_if_exists(self):
        if self.exists():
            try:
                self.win.destroy()
            except Exception:
                pass
        self.win = None


class Click2FoldersApp(tk.Tk):
    MODES = {
        "medio_y_nombre": "1. Por Fecha de Captura, Medio Creado o Nombre",
        "nombre": "2. Por Fecha en el Nombre",
        "creacion": "3. Por Fecha de Creación",
        "modificacion": "4. Por Fecha de Modificación",
    }
    MODES_EN = {
        "medio_y_nombre": "1. By Capture Date, Media Created or Name",
        "nombre": "2. By Date in the Name",
        "creacion": "3. By Creation Date",
        "modificacion": "4. By Modification Date",
    }

    def __init__(self):
        super().__init__()
        self.withdraw()
        self.title(WINDOW_TITLE)
        self.minsize(900, 620)
        self.configure(bg="#f0f4f8")
        safe_icon(self)
        
        if not ensure_single_instance():
            sys.exit(0)
        # Nota: Shell.Application se crea por-hilo (ver _get_thread_shell),
        # no aquí en el hilo principal, para evitar problemas de apartment COM
        # entre el hilo de la UI y los hilos de trabajo que organizan archivos.
        self.premium = True
        self.no_show_name_tip = False
        self.no_show_creacion_tip = False
        self.no_show_medio_tip = False
        self.queue = []
        self.folder_indexes = {}
        self.moved_ops = []
        self.created_dirs = set()
        self.total_analyzed = 0
        self.total_organized = 0
        self.total_dirs_created = 0
        self.start_time = None
        self.processed_roots = set()
        self.carpetas_procesadas_deshacer = 0
        self.total_carpetas_deshacer = 0
        self.tutorial_win = OneShotWindow()
        self.limits_win = OneShotWindow()
        self.support_win = OneShotWindow()
        self.donate_win = OneShotWindow()
        self._has_update = False
        self._update_checked = False
        self._donate_shown = False
        self._donate_closed = False
        self.toolbar = None
        self.is_processing = False
        self.english_mode = False
        self.btn_add_folder = None
        self.btn_start = None
        self.btn_undo = None
        self.btn_remove = None
        self._live_popups = []
        self._build_toolbar()
        self._build_options()
        self._build_queue_area()
        self._build_progress_bar()
        self._build_counters_bar()
        self._build_log_area()
        self.overlay = None
        self.overlay_text = None
        self.marquee = None
        self._update_undo_button_state()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        # Centrar y mostrar ventana
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = 900
        h = 620
        old_h = 580
        x = (sw - w) // 2
        y = (sh - old_h) // 2 - (h - old_h)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.deiconify()
        self.after(10, self._fit_folder)
        # Mostrar donaciones cada 5 lanzamientos
        self.after(500, self._check_launch_donation)

    # [Métodos restantes idénticos... se mantienen todos los métodos UI y organización sin cambios]

    def _build_toolbar(self):
        if self.toolbar:
            self.toolbar.destroy()
        self.toolbar = ctk.CTkFrame(self, fg_color="#e8eef5", corner_radius=12)
        self.toolbar.pack(fill="x", padx=10, pady=(5, 3))
        eng = getattr(self, 'english_mode', False)
        
        # Botones del toolbar con estilo neoformismo
        btn_style = {"corner_radius": 8, "height": 32, "font": ("Segoe UI", 12, "bold"),
                     "hover_color": "#3b82f6", "text_color": "white"}
        
        self.btn_tutorial = ctk.CTkButton(self.toolbar, text="Tutorial", 
                                          fg_color="#3b82f6", command=self.on_tutorial, **btn_style)
        self.btn_tutorial.pack(side="left", padx=(8, 4))
        self.btn_support = ctk.CTkButton(self.toolbar, text="Support" if eng else "Soporte", 
                                         fg_color="#10b981", command=self.on_support, **btn_style)
        self.btn_support.pack(side="left", padx=4)
        self.btn_lang = ctk.CTkButton(self.toolbar, text="Traducir al Español" if eng else "Translate to English", 
                                       fg_color="#8b5cf6", command=self._toggle_lang, **btn_style)
        self.btn_lang.pack(side="left", padx=4)
        self.btn_donate = ctk.CTkButton(self.toolbar, text="Donations" if eng else "Donaciones", 
                                        fg_color="#f59e0b", command=self.on_donate, **btn_style)
        self.btn_donate.pack(side="left", padx=4)
        self.btn_updates = ctk.CTkButton(self.toolbar, text="Actualización" if not eng else "Update",
                                          fg_color="#ef4444",
                                          command=lambda: webbrowser.open(GITHUB_RELEASES_URL), **btn_style)
        self.btn_updates.pack(side="left", padx=(4, 8))
        self._lang_tooltip = None
        def _show_lang_tip(e):
            if self._lang_tooltip: return
            tip = tk.Toplevel(self)
            tip.wm_overrideredirect(True)
            tip.wm_geometry(f"+{e.x_root+12}+{e.y_root+20}")
            eng2 = getattr(self, 'english_mode', False)
            if not eng2:
                txt = "Cambia de español a ingles la interfaz y al organizar\nnombra las subcarpetas de mes también en ingles:\n(1 January, 2 February...)"
            else:
                txt = "Switches from English to Spanish interface and\nnames month subfolders in Spanish when organizing:\n(1 Enero, 2 Febrero...)"
            tk.Label(tip, text=txt, background="#fef3c7", fg="#92400e",
                     relief="solid", borderwidth=1, font=("Segoe UI", 10), padx=8, pady=4, justify="left").pack()
            self._lang_tooltip = tip
        def _hide_lang_tip(e):
            if self._lang_tooltip:
                self._lang_tooltip.destroy()
                self._lang_tooltip = None
        self.btn_lang.bind("<Enter>", _show_lang_tip)
        self.btn_lang.bind("<Leave>", _hide_lang_tip)

    def _toggle_lang(self):
        if getattr(self, "is_processing", False):
            return
        try:
            # Detectar ventanas abiertas antes de cambiar idioma
            windows_to_reopen = []
            if hasattr(self, 'donate_win') and self.donate_win.exists():
                windows_to_reopen.append('donate')
            if hasattr(self, 'support_win') and self.support_win.exists():
                windows_to_reopen.append('support')
            if hasattr(self, 'tutorial_win') and self.tutorial_win.exists():
                windows_to_reopen.append('tutorial')
            
            self.english_mode = not self.english_mode
            eng = self.english_mode
            
            # Cerrar ventanas auxiliares abiertas
            self._close_aux_windows()
            
            # Actualizar título de la ventana principal
            self.title(f"Click2Folders - Chronological Photo & Video Organizer {APP_VERSION}" if eng else f"Click2Folders - Organizador Cronológico de Fotos y Videos {APP_VERSION}")
            self.btn_support.configure(text="Support" if eng else "Soporte")
            self.btn_donate.configure(text="Donations" if eng else "Donaciones")
            self.btn_lang.configure(text="Traducir al Español" if eng else "Translate to English")
            self.btn_updates.configure(text="Actualización" if not eng else "Update")
            # Actualizar botones de la cola
            self.btn_add_folder.configure(text="Add folder" if eng else "Agregar carpeta")
            self.btn_add_multiple.configure(text="Add multiple folders" if eng else "Agregar varias carpetas")
            self.btn_start.configure(text="Organize" if eng else "Organizar")
            self.btn_undo.configure(text="Undo organization" if eng else "Deshacer organización")
            # Actualizar encabezados del árbol
            self.tree.heading("folder", text="Folder" if eng else "Carpeta")
            self.tree.heading("cantidad", text="Content" if eng else "Contenido")
            self.tree.heading("status", text="Status" if eng else "Estado")
            # Actualizar botones adicionales
            self.btn_remove.configure(text="Remove selected folders" if eng else "Quitar Carpetas Seleccionadas")
            self.btn_sel_all.configure(text="Select all" if eng else "Seleccionar todo")
            self.btn_desel_all.configure(text="Deselect all" if eng else "Deseleccionar todo")
            self.lbl_cf_prefix.configure(text="Organizing folder: " if eng else "Organizando Carpeta: ")
            if self.lbl_cf_name:
                self.lbl_cf_name.configure(text="None" if eng else "Ninguna")
            # Actualizar contadores
            self.lbl_analyzed.configure(text=f"{'Total files organized:' if eng else 'Total de archivos organizados:'} {self.total_organized}")
            self.lbl_dirs.configure(text=f"{'Total folders created:' if eng else 'Total de carpetas creadas:'} {self.total_dirs_created}")
            if self.start_time:
                elapsed = time.time() - self.start_time
                minutes = int(elapsed // 60)
                seconds = int(elapsed % 60)
                self.lbl_time.configure(text=f"{'Elapsed time:' if eng else 'Tiempo transcurrido:'} {minutes}m {seconds}s")
            else:
                self.lbl_time.configure(text=f"{'Elapsed time:' if eng else 'Tiempo transcurrido:'} 0m 0s")
            # Actualizar combo de modos
            self._rebuild_options_lang()
            # Actualizar tooltip
            if self._lang_tooltip:
                self._lang_tooltip.destroy()
                self._lang_tooltip = None
            # Actualizar textos de estado y contenido del árbol
            children = self.tree.get_children()
            for iid in children:
                values = self.tree.item(iid, "values")
                if len(values) >= 4:
                    current_status = str(values[3])
                    new_status = self._translate_status(current_status, eng)
                    self.tree.set(iid, "status", new_status)
                    current_cant = str(values[2])
                    new_cant = self._translate_cantidad_text(current_cant, eng)
                    self.tree.set(iid, "cantidad", new_cant)

            # Re-ajustar ancho de columnas con los textos ya traducidos
            self.after(10, self._fit_folder)

            # Traducir el texto que ya está escrito en el log
            try:
                self.txt.configure(state="normal")
                scroll_pos = self.txt.yview()
                current_log = self.txt.get("1.0", "end-1c")
                if current_log.strip():
                    new_log = self._translate_log_text(current_log, eng)
                    self.txt.delete("1.0", "end")
                    self.txt.insert("1.0", new_log)
                    self.txt.yview_moveto(scroll_pos[0])
                self.txt.configure(state="disabled")
            except Exception:
                pass

            # Actualizar popups modales abiertos (Aviso, selección, fin de organización...)
            alive_popups = []
            for entry in getattr(self, '_live_popups', []):
                try:
                    if not entry["win"].winfo_exists():
                        continue
                    entry["win"].title(entry["title_en"] if eng else entry["title_es"])
                    for wgt, t_es, t_en in entry["widgets"]:
                        wgt.configure(text=t_en if eng else t_es)
                    alive_popups.append(entry)
                except Exception:
                    pass
            self._live_popups = alive_popups

            # Reabrir ventanas que estaban abiertas
            if 'donate' in windows_to_reopen:
                self.after(100, self.on_donate)
            if 'support' in windows_to_reopen:
                self.after(100, self.on_support)
            if 'tutorial' in windows_to_reopen:
                self.after(100, self.on_tutorial)
        except Exception:
            pass

    def _translate_cantidad_text(self, current_text, to_english):
        """Traduce texto de la columna cantidad entre español e inglés."""
        if not current_text:
            return current_text
        result = current_text
        if to_english:
            result = result.replace("Carpeta Vacía", "Empty Folder")
            result = result.replace("carpetas", "folders")
            result = result.replace("Archivos en total", "Total files")
            result = result.replace("archivos organizados", "files organized")
            result = result.replace("sin fecha", "without date")
        else:
            result = result.replace("Empty Folder", "Carpeta Vacía")
            result = result.replace("folders", "carpetas")
            result = result.replace("Total files", "Archivos en total")
            result = result.replace("files organized", "archivos organizados")
            result = result.replace("without date", "sin fecha")
        return result

    def _translate_log_text(self, text, to_english):
        """Traduce las etiquetas fijas de los mensajes del log ya escritos
        (p. ej. 'Organizando carpeta:', 'Sin fecha detectada:'), sin tocar
        nombres de archivo o carpeta, fechas ni las lineas separadoras."""
        pairs = [
            ("carpeta(s) agregada(s)", "folder(s) added"),
            ("Deshaciendo organización previa en:", "Undoing previous organization in:"),
            ("Deshaciendo organización en:", "Undoing organization in:"),
            ("Organización deshecha en:", "Organization undone in:"),
            ("Error deshaciendo organización:", "Error undoing organization:"),
            ("Iniciando organización desde cero...", "Starting organization from scratch..."),
            ("Organizando carpeta:", "Organizing folder:"),
            ("ARCHIVOS SIN FECHA DETECTADA:", "FILES WITHOUT DETECTED DATE:"),
            ("Sin fecha detectada:", "No date detected:"),
            ("Total de archivos organizados:", "Total files organized:"),
            ("Total de archivos sin fecha detectable:", "Total files without date:"),
            ("Total de carpetas creadas:", "Total folders created:"),
            ("Fecha/hora final:", "Final date/time:"),
            ("\u2014 se omite.", "\u2014 skipped."),
            ("se omite.", "skipped."),
            ("Movido:", "Moved:"),
            ("Restaurando archivos...", "Restoring files..."),
            ("Error restaurando", "Error restoring"),
            ("Restauración de", "Restoration of"),
            ("archivos completada.", "files completed."),
            ("Inicio:", "Start:"),
            ("Fin:", "End:"),
            ("RESUMEN FINAL", "FINAL SUMMARY"),
            ("archivos organizados", "files organized"),
            ("sin fecha", "without date"),
            ("carpetas creadas", "folders created"),
        ]
        result = text
        if to_english:
            for es, en in pairs:
                result = result.replace(es, en)
        else:
            for es, en in pairs:
                result = result.replace(en, es)
        return result

    def _translate_status(self, current_status, to_english):
        if to_english:
            # Handle new format: "X carpetas, Y archivos" or single items
            result = current_status
            result = result.replace("carpetas", "folders").replace("archivos", "files")
            result = result.replace("carpeta", "folder").replace("archivo", "file")
            result = result.replace("0 items", "0 items")
            mapping = {
                "Organizado": "Organized",
                "Organizando...": "Organizing...",
                "En espera": "Waiting",
                "Deshaciendo...": "Undoing...",
                "Deshecho": "Undone",
                "Sin organizar": "Unorganized",
            }
            return mapping.get(result, result)
        else:
            result = current_status
            result = result.replace("folders", "carpetas").replace("files", "archivos")
            result = result.replace("folder", "carpeta").replace("file", "archivo")
            result = result.replace("0 items", "0 elementos")
            mapping = {
                "Organized": "Organizado",
                "Organizing...": "Organizando...",
                "Waiting": "En espera",
                "Undoing...": "Deshaciendo...",
                "Undone": "Deshecho",
                "Unorganized": "Sin organizar",
            }
            return mapping.get(result, result)

    def _rebuild_options_lang(self):
        """Reconstruye los textos del área de opciones según el idioma actual."""
        eng = getattr(self, 'english_mode', False)
        # Actualizar label de modo
        self._mode_label.configure(text="Organization mode:" if eng else "Modo de organización:")
        # Actualizar checkbox "No anteponer número"
        self._cb_no_num.configure(text="Do not add month number" if eng else "No poner número de mes")
        # Cambiar valores del combo de modos
        modes_dict = self.MODES_EN if eng else self.MODES
        current_key = self._get_mode_key()
        new_values = list(modes_dict.values())
        new_text = modes_dict[current_key]
        self.mode_combo.configure(values=new_values)
        self.mode_var.set(new_text)
        self.mode_combo.set(new_text)

    def _build_options(self):
        box = ctk.CTkFrame(self, fg_color="#e8eef5", corner_radius=12)
        box.pack(fill="x", padx=10, pady=3)
        options_frame = tk.Frame(box, bg="#f0f4f8")
        options_frame.pack(fill="x", pady=8, padx=10)
        self.mode_enabled_var = tk.BooleanVar(value=True)
        modes_init = self.MODES_EN if getattr(self, 'english_mode', False) else self.MODES
        self.mode_var = tk.StringVar(value=modes_init["medio_y_nombre"])
        eng = getattr(self, 'english_mode', False)
        self._mode_label = ctk.CTkLabel(options_frame, text="Organization mode:" if eng else "Modo de organización:", 
                                        font=("Segoe UI", 13, "bold"), text_color="#1e3a5f")
        self._mode_label.pack(side="left", padx=(0, 8))
        self.mode_combo = ctk.CTkComboBox(
            options_frame, variable=self.mode_var,
            values=list(modes_init.values()), state="readonly", width=400,
            fg_color="white", border_color="#3b82f6", button_color="#3b82f6",
            dropdown_fg_color="white", text_color="#1e3a5f")
        self.mode_combo.pack(side="left", padx=(0, 10))

        self.var_dupes = tk.BooleanVar(value=False)
        self.var_reubicar = tk.BooleanVar(value=False)
        self.var_no_month_num = tk.BooleanVar(value=False)
        self._cb_no_num = ctk.CTkCheckBox(options_frame, text="No poner número de mes",
                                         variable=self.var_no_month_num,
                                         fg_color="#3b82f6", hover_color="#1d4ed8",
                                         text_color="#1e3a5f")
        self._cb_no_num.pack(side="left", padx=(8, 0))
        # Tooltip para el checkbox
        self._no_num_tooltip = None
        def _show_no_num_tip(e):
            if self._no_num_tooltip: return
            tip = tk.Toplevel(self)
            tip.wm_overrideredirect(True)
            tip.wm_geometry(f"+{e.x_root+12}+{e.y_root+20}")
            eng_tip = getattr(self, 'english_mode', False)
            tip_txt = "If checked, subfolders will not have\nthe corresponding month number." if eng_tip else "Si está marcada, las subcarpetas\nno tendrán número correspondiente al mes."
            tk.Label(tip, text=tip_txt, background="#fef3c7", fg="#92400e",
                     relief="solid", borderwidth=1, font=("Segoe UI", 10), padx=8, pady=4, justify="left").pack()
            self._no_num_tooltip = tip
        def _hide_no_num_tip(e):
            if self._no_num_tooltip:
                self._no_num_tooltip.destroy()
                self._no_num_tooltip = None
        self._cb_no_num.bind("<Enter>", _show_no_num_tip)
        self._cb_no_num.bind("<Leave>", _hide_no_num_tip)
    def _get_mode_key(self):
        selected_text = self.mode_var.get()
        # Buscar en ambos diccionarios (el combo puede tener texto EN o ES)
        for d in (self.MODES, self.MODES_EN):
            r = next((k for k, v in d.items() if v == selected_text), None)
            if r:
                return r
        return "medio_y_nombre"
    def _build_queue_area(self):
        frame = ctk.CTkFrame(self, fg_color="#e8eef5", corner_radius=12)
        frame.pack(fill="both", expand=False, padx=10, pady=3)

        # Botones Seleccionar/Deseleccionar ENCIMA del tree
        sel_top_bar = tk.Frame(frame, bg="#f0f4f8")
        sel_top_bar.pack(fill="x", pady=(8, 3), padx=10)

        body = tk.Frame(frame, bg="#f0f4f8")
        body.pack(fill="both", expand=True, padx=10)

        # Estilo Treeview: neoformismo
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading",
                        background="#3b82f6",
                        foreground="white",
                        relief="flat",
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview.Heading",
                  background=[("active", "#2563eb"), ("!active", "#3b82f6")],
                  foreground=[("active", "white"), ("!active", "white")])
        style.configure("Treeview",
                        background="#ffffff",
                        fieldbackground="#ffffff",
                        rowheight=30,
                        borderwidth=1,
                        relief="solid",
                        font=("Segoe UI", 11))
        style.layout("Treeview", [
            ("Treeview.treearea", {"sticky": "nswe"})
        ])

        self.tree = ttk.Treeview(body, height=6, columns=("sel", "folder", "cantidad", "status"), show="headings")
        self.tree.column("sel", width=30, minwidth=30, stretch=False, anchor="center")
        self.tree.column("folder", width=320, minwidth=200, stretch=False, anchor="w")
        self.tree.column("cantidad", width=350, minwidth=300, stretch=False, anchor="center")
        self.tree.column("status", width=130, minwidth=110, stretch=False, anchor="center")
        self.tree.heading("sel", text="Sel.")
        self.tree.heading("folder", text="Folder" if self.english_mode else "Carpeta")
        self.tree.heading("cantidad", text="Contenido" if not getattr(self, 'english_mode', False) else "Content")
        self.tree.heading("status", text="Status" if self.english_mode else "Estado")
        self._add_placeholder_rows()
        scroll = tk.Scrollbar(body, command=self.tree.yview, width=22)
        self.tree.configure(yscrollcommand=scroll.set)
        hscroll = tk.Scrollbar(body, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=hscroll.set)
        self._hscroll = hscroll
        self._hscroll_shown = False
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        # Redimensionamiento de columnas arrastrando separadores
        self._col_resizer = _ColumnResizer(self.tree, ("sel", "folder", "cantidad", "status"))

        # Ajustar columna Carpeta para llenar espacio restante (sin stretch)
        def _fit_folder(event=None):
            if self._col_resizer._drag_col is not None:
                return
            try:
                tw = self.tree.winfo_width()
                if tw <= 10:
                    self.after(50, _fit_folder)
                    return
                try:
                    fnt = tkfont.Font(family="Segoe UI", size=11)
                except Exception:
                    fnt = None
                eng_f = getattr(self, 'english_mode', False)
                heads = ("Sel.", "Folder" if eng_f else "Carpeta",
                         "Content" if eng_f else "Contenido",
                         "Status" if eng_f else "Estado")

                def _col_needed(idx, default):
                    w = default
                    if fnt is None:
                        return w
                    w = max(w, fnt.measure(heads[idx]) + 24)
                    for iid in self.tree.get_children():
                        vals = self.tree.item(iid, "values")
                        if len(vals) > idx:
                            t = str(vals[idx])
                            if t:
                                w = max(w, fnt.measure(t) + 24)
                    return w

                # Sin tope de ancho: el texto de Contenido/Estado nunca queda cortado
                sel_w = 30
                cant_w = _col_needed(2, 300)
                status_w = _col_needed(3, 110)
                folder_w = max(200, tw - sel_w - cant_w - status_w)
                total_w = sel_w + folder_w + cant_w + status_w
                self.tree.column("sel", width=sel_w, minwidth=sel_w)
                self.tree.column("folder", width=folder_w, minwidth=200)
                self.tree.column("cantidad", width=cant_w, minwidth=300)
                self.tree.column("status", width=status_w, minwidth=110)
                # Barra horizontal solo si algo queda fuera de la vista
                need_h = total_w > tw + 2
                if need_h != self._hscroll_shown:
                    if need_h:
                        self._hscroll.grid(row=1, column=0, sticky="ew")
                    else:
                        self._hscroll.grid_remove()
                    self._hscroll_shown = need_h
            except Exception:
                pass
        self._fit_folder = _fit_folder
        self.tree.bind("<Configure>", _fit_folder, add="+")
        self.after(50, _fit_folder)

        # Líneas divisorias: filas alternas
        self.tree.tag_configure("oddrow", background="#f0f4f8")
        self.tree.tag_configure("evenrow", background="#ffffff")

        btn_frame = tk.Frame(frame, bg="#f0f4f8")
        btn_frame.pack(pady=(8, 10), padx=10, anchor="w")
        
        btn_style = {"corner_radius": 8, "height": 36, "font": ("Segoe UI", 12, "bold"),
                     "hover_color": "#2563eb", "text_color": "white"}
        
        self.btn_add_folder = ctk.CTkButton(btn_frame, text="Add folder" if self.english_mode else "Agregar carpeta", 
                                            fg_color="#3b82f6", command=self.on_add_folder, **btn_style)
        self.btn_add_folder.pack(side="left", padx=4)
        self.btn_add_multiple = ctk.CTkButton(btn_frame, text="Add multiple folders" if self.english_mode else "Agregar varias carpetas", 
                                              fg_color="#6366f1", command=self.on_add_multiple_folders, **btn_style)
        self.btn_add_multiple.pack(side="left", padx=4)
        self.btn_start = ctk.CTkButton(btn_frame, text="Organize" if self.english_mode else "Organizar", 
                                       fg_color="#10b981", command=self.on_start, **btn_style)
        self.btn_start.pack(side="left", padx=4)
        self.btn_undo = ctk.CTkButton(btn_frame, text="Undo organization" if self.english_mode else "Deshacer organización", 
                                      fg_color="#f59e0b", command=self.on_undo, **btn_style)
        self.btn_undo.pack(side="left", padx=4)

        # Diccionario de checkboxes: item_id -> bool
        self._tree_checked = {}

        def toggle_check(item_id):
            val = self._tree_checked.get(item_id, False)
            self._tree_checked[item_id] = not val
            self.tree.set(item_id, "sel", "☑" if not val else "☐")

        def on_tree_click(event):
            if self._col_resizer._drag_col is not None:
                return
            col = self.tree.identify_column(event.x)
            row = self.tree.identify_row(event.y)
            if row and col == "#1":
                self.after(1, lambda r=row: toggle_check(r))

        self.tree.bind("<Button-1>", on_tree_click, add="+")
        # Deshabilitar selección visual azul
        self.tree.configure(selectmode="none")

        def remove_checked():
            checked = [iid for iid, v in self._tree_checked.items() if v]
            if not checked:
                self._show_modern_popup(("Marca con ☑ las carpetas que deseas quitar de la lista.",
                                         "Check ☑ the folders you want to remove from the list."))
                return
            for iid in checked:
                try:
                    item = self.tree.item(iid)
                    folder = item["values"][1]  # col 1 = folder
                    folder_norm = os.path.normcase(os.path.abspath(folder))
                    self.tree.delete(iid)
                    self._tree_checked.pop(iid, None)
                    if folder_norm in self.folder_indexes:
                        del self.folder_indexes[folder_norm]
                    if folder_norm in self.queue:
                        self.queue.remove(folder_norm)
                    self.processed_roots.discard(folder_norm)
                except Exception:
                    pass
            self._update_undo_button_state()
            # Limpiar log si no quedan carpetas
            if not self.queue:
                self.after(0, self._clear_log)
                self.after(0, self._add_placeholder_rows)

        def select_all_tree():
            valid_items = []
            for iid in list(self._tree_checked.keys()):
                if self.tree.exists(iid):
                    self._tree_checked[iid] = True
                    self.tree.set(iid, "sel", "☑")
                    valid_items.append(iid)
            # Limpiar IDs inválidos del diccionario
            stale = [k for k in self._tree_checked if k not in valid_items]
            for k in stale:
                del self._tree_checked[k]

        def deselect_all_tree():
            valid_items = []
            for iid in list(self._tree_checked.keys()):
                if self.tree.exists(iid):
                    self._tree_checked[iid] = False
                    self.tree.set(iid, "sel", "☐")
                    valid_items.append(iid)
            # Limpiar IDs inválidos del diccionario
            stale = [k for k in self._tree_checked if k not in valid_items]
            for k in stale:
                del self._tree_checked[k]

        self.btn_remove = ctk.CTkButton(btn_frame, text="Remove selected folders" if self.english_mode else "Quitar Carpetas Seleccionadas", 
                                         fg_color="#ef4444", command=remove_checked, **btn_style)
        self.btn_remove.pack(side="left", padx=4)
        # status_label oculto (referencias internas lo usan pero no se muestra)
        self.status_label = ctk.CTkLabel(self, text="", font=("Segoe UI", 12, "bold"), text_color="#1e3a5f")

        # Botones seleccionar/deseleccionar en barra superior (Seleccionar primero)
        self.btn_sel_all = ctk.CTkButton(sel_top_bar, text="Select all" if self.english_mode else "Seleccionar todo", 
                                         fg_color="#64748b", hover_color="#475569", command=select_all_tree,
                                         corner_radius=8, height=28, font=("Segoe UI", 11), text_color="white", width=120)
        self.btn_sel_all.pack(side="left", padx=(0, 4))
        self.btn_desel_all = ctk.CTkButton(sel_top_bar, text="Deselect all" if self.english_mode else "Deseleccionar todo", 
                                           fg_color="#64748b", hover_color="#475569", command=deselect_all_tree,
                                           corner_radius=8, height=28, font=("Segoe UI", 11), text_color="white", width=120)
        self.btn_desel_all.pack(side="left")
        # Deshabilitar clic derecho en el árbol para evitar confusiones al usuario
        self.tree.bind("<Button-3>", lambda e: "break")
        self.tree.bind("<Button-2>", lambda e: "break")

        # Tooltip para ruta completa en columna Carpeta
        self._tree_folder_tooltip = None
        def _on_tree_folder_hover(event):
            try:
                col = self.tree.identify_column(event.x)
                row = self.tree.identify_row(event.y)
                if row and col == "#2":
                    folder_val = self.tree.set(row, "folder")
                    if folder_val:
                        if self._tree_folder_tooltip and self._tree_folder_tooltip.winfo_exists():
                            self._tree_folder_tooltip.destroy()
                        tip = tk.Toplevel(self)
                        tip.wm_overrideredirect(True)
                        tip.wm_geometry(f"+{event.x_root + 12}+{event.y_root + 18}")
                        ctk.CTkLabel(tip, text=folder_val, fg_color="#1e293b", text_color="#e2e8f0",
                                    corner_radius=6, font=("Segoe UI", 11), padx=8, pady=4).pack()
                        self._tree_folder_tooltip = tip
                else:
                    if self._tree_folder_tooltip and self._tree_folder_tooltip.winfo_exists():
                        self._tree_folder_tooltip.destroy()
                        self._tree_folder_tooltip = None
            except Exception:
                pass
        def _on_tree_folder_leave(event):
            try:
                if self._tree_folder_tooltip and self._tree_folder_tooltip.winfo_exists():
                    self._tree_folder_tooltip.destroy()
                    self._tree_folder_tooltip = None
            except Exception:
                pass
        self.tree.bind("<Motion>", _on_tree_folder_hover, add="+")
        self.tree.bind("<Leave>", _on_tree_folder_leave, add="+")

    def _add_placeholder_rows(self):
        for i in range(6):
            tag = "oddrow" if i % 2 == 0 else "evenrow"
            self.tree.insert("", "end", values=("", "", "", ""), tags=(tag, "ph"))

    def _clear_placeholder_rows(self):
        # Borrar SOLO las filas placeholder (tag "ph"): las carpetas reales
        # del usuario se conservan al agregar nuevas (acumular, no reemplazar)
        for item in self.tree.get_children():
            if "ph" in self.tree.item(item, "tags"):
                self.tree.delete(item)
        # Limpiar IDs inválidos del diccionario de checks
        if hasattr(self, '_tree_checked'):
            stale = [k for k in self._tree_checked if not self.tree.exists(k)]
            for k in stale:
                del self._tree_checked[k]

    def _build_progress_bar(self):
        self.progress = ctk.CTkProgressBar(self, orientation="horizontal", progress_color="#3b82f6",
                                          fg_color="#e2e8f0", height=20, corner_radius=10)
        self.progress.pack(fill="x", padx=10, pady=(5, 3))
        self.progress.set(0)

    def _build_log_area(self):
        frame = ctk.CTkFrame(self, fg_color="#e8eef5", corner_radius=12)
        frame.pack(fill="both", expand=True, padx=10, pady=3)
        self.lbl_cf_frame = tk.Frame(frame, bg="#f0f4f8")
        self.lbl_cf_frame.pack(fill="x", pady=(8, 4), padx=10)
        self.lbl_cf_prefix = ctk.CTkLabel(self.lbl_cf_frame, text="Organizing folder: " if self.english_mode else "Organizando Carpeta: ", 
                                         font=("Segoe UI", 12), text_color="#3b82f6", anchor="w")
        self.lbl_cf_prefix.pack(side="left")
        self.lbl_cf_name = ctk.CTkLabel(self.lbl_cf_frame, text="None" if self.english_mode else "Ninguna", 
                                         font=("Segoe UI", 12, "bold"), text_color="#1e3a5f", anchor="w")
        self.lbl_cf_name.pack(side="left")
        self.lbl_wait = ctk.CTkLabel(self.lbl_cf_frame, text="", 
                                     font=("Segoe UI", 12, "bold"), text_color="#f59e0b")
        self.lbl_wait.place(relx=0.5, rely=0.5, anchor="center")
        txt_frame = ctk.CTkFrame(frame, fg_color="white", corner_radius=8)
        txt_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.txt = tk.Text(txt_frame, height=10, state="disabled", bg="#ffffff", fg="#1e3a5f",
                          font=("Consolas", 10), relief="flat", borderwidth=0, highlightthickness=0)
        scroll = ctk.CTkScrollbar(txt_frame, command=self.txt.yview, fg_color="#cbd5e1", button_color="#94a3b8")
        self._log_scroll = scroll
        self.txt.configure(yscrollcommand=self._on_log_scroll)
        scroll.pack(side="right", fill="y", padx=(2, 5), pady=5)
        self.txt.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.txt.bind("<Configure>", self._on_log_configure)

    def _on_log_scroll(self, first, last):
        try:
            self._log_scroll.set(first, last)
            if not getattr(self, "_log_resizing", False):
                self._log_at_end = float(last) >= 0.999
        except Exception:
            pass

    def _on_log_configure(self, event=None):
        try:
            if event is not None and event.widget is not self.txt:
                return
            self._log_resizing = True
            if getattr(self, "_log_realign_id", None):
                try:
                    self.after_cancel(self._log_realign_id)
                except Exception:
                    pass
            self._log_realign_id = self.after(120, self._realign_log_view)
        except Exception:
            pass

    def _realign_log_view(self):
        self._log_realign_id = None
        try:
            if getattr(self, "_log_at_end", True):
                self.txt.yview_moveto(1.0)
        except Exception:
            pass
        finally:
            self._log_resizing = False

    def _build_counters_bar(self):
        bar = tk.Frame(self, bg="#1e3a5f")
        bar.pack(fill="x", padx=0, pady=0, side="bottom")
        self.lbl_analyzed = tk.Label(bar, text="Total files organized: 0" if self.english_mode else "Total de archivos organizados: 0",
                                    font=("Segoe UI", 11), bg="#1e3a5f", fg="white")
        self.lbl_dirs = tk.Label(bar, text="Total folders created: 0" if self.english_mode else "Total de carpetas creadas: 0",
                                font=("Segoe UI", 11), bg="#1e3a5f", fg="white")
        self.lbl_dupes = tk.Label(bar, text="", font=("Segoe UI", 11), bg="#1e3a5f", fg="white")
        self.lbl_time = tk.Label(bar, text="Elapsed time: 0m 0s" if self.english_mode else "Tiempo transcurrido: 0m 0s",
                                font=("Segoe UI", 11), bg="#1e3a5f", fg="white")
        self.lbl_analyzed.pack(side="left", padx=12)
        self.lbl_dirs.pack(side="left", padx=12)
        self.lbl_time.pack(side="left", padx=12)

    def _clear_log(self):
        try:
            self.txt.configure(state="normal")
            self.txt.delete("1.0", tk.END)
            self.txt.configure(state="disabled")
            self.lbl_cf_name.configure(text="None" if getattr(self, 'english_mode', False) else "Ninguna")
        except Exception:
            pass

    def _close_aux_windows(self):
        donate_was_open = False
        for attr in ['donate_win', 'support_win', 'tutorial_win', 'limits_win']:
            win_holder = getattr(self, attr, None)
            if win_holder and hasattr(win_holder, 'win') and win_holder.win:
                if attr == 'donate_win':
                    donate_was_open = True
                try:
                    win_holder.win.destroy()
                except Exception:
                    pass
                win_holder.win = None
        if donate_was_open:
            self.after(100, self._on_donate_closed)
    def _update_undo_button_state(self):
        if self.btn_undo:
            if self.is_processing:
                self.btn_undo.configure(state="disabled")
            else:
                self.btn_undo.configure(state="normal")

    def _set_buttons_state(self, state):
        state_str = "normal" if state else "disabled"
        if self.btn_add_folder:
            self.btn_add_folder.configure(state=state_str)
        if self.btn_start:
            self.btn_start.configure(state=state_str)
        if self.btn_undo:
            self._update_undo_button_state()
        if self.btn_remove:
            self.btn_remove.configure(state=state_str)
        if getattr(self, "btn_lang", None):
            self.btn_lang.configure(state=state_str)

    def on_tutorial(self):
        self._close_aux_windows()
        w = tk.Toplevel(self)
        w.withdraw()
        w.title("Tutorial — Click2Folders" if getattr(self, 'english_mode', False) else "Tutorial")
        w.resizable(True, True)
        w.configure(bg="#f0f4f8")
        safe_icon(w)

        # Usar canvas con scrollbar para que quepa en pantalla
        main_frame = tk.Frame(w, bg="#f0f4f8")
        main_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(main_frame, highlightthickness=0, bg="#f0f4f8")
        vsb = ctk.CTkScrollbar(main_frame, orientation="vertical", command=canvas.yview, fg_color="#cbd5e1", button_color="#94a3b8")
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y", padx=(0, 5), pady=5)
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        pad = tk.Frame(canvas, bg="#f0f4f8")
        pad_id = canvas.create_window((0, 0), window=pad, anchor="nw")
        pad.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(pad_id, width=e.width))
        # Deshabilitar clic derecho en el tutorial
        for widget in (w, main_frame, canvas, pad):
            widget.bind("<Button-3>", lambda e: "break")
            widget.bind("<Button-2>", lambda e: "break")
        def _on_mousewheel(e):
            bbox2 = canvas.bbox("all")
            if bbox2:
                content_h = bbox2[3] - bbox2[1]
                visible_h = canvas.winfo_height()
                if content_h <= visible_h:
                    return
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        wrap_width = 760

        # ── Encabezado siempre visible ──────────────────────────────
        ctk.CTkLabel(pad, text="📁  Click2Folders — Chronological Photo & Video Organizer" if getattr(self, 'english_mode', False) else "📁  Click2Folders — Organizador Cronológico de Fotos y Videos",
                     font=("Segoe UI", 14, "bold"), text_color="#1e3a5f").pack(anchor="w", pady=(0,8), padx=10)

        # ── Secciones desplegables ───────────────────────────────────
        eng = getattr(self, 'english_mode', False)
        if eng:
            sections_data = [
                ("🤔  What does the program do?", [
                    ("The program detects the dates of your photos and videos to create year folders,", False),
                    ("month subfolders and then moves them to their corresponding folder.", False),
                    ("", False),
                    ("__The program offers 4 organization modes:__", False),
                    ("1. By Capture Date, Media Created or Name.", True),
                    ("2. By Date in the Filename.", True),
                    ("3. By File Creation Date.", True),
                    ("4. By Modification Date.", True),
                ]),
                ("📋  How to use the program?", [
                    ("1. Add the folder or folders you want.", False),
                    ("2. Choose one of the 4 organization modes.", False),
                    ("3. Check the selection column for the folders you want and click organize.", False),
                ]),
                ("📅  What dates does the program detect?", [
                    ("  Capture date:", True),
                    ("  Created by the camera at the exact moment the photo was taken.", False),
                    ("  Date in the filename:", True),
                    ("  Some cameras include the date in the filename when saving the photo or video.", False),
                    ("  Modification date:", True),
                    ("  Indicates the last time the file was edited.", False),
                    ("  File creation date:", True),
                    ("  OS date indicating when the file was saved.", False),
                ]),
                ("🗂  Organization modes", [
                    ("1. By Capture Date, Media Created or Name:", True),
                    ("   First looks for Capture Date in photos (the most precise, taken by the camera).", False),
                    ("   If not found, looks for the Media Created date.", False),
                    ("   If not found, looks for a date in the filename.", False),
                    ("   **Note:** Videos don't have a Capture Date, they have a Media Created date", False),
                    ("   (the most precise when recorded). In videos, the program first looks", False),
                    ("   for the Media Created date, and if not found, looks for the date in the Name.", False),
                    ("2. By Date in the Name:", True),
                    ("   Detects the date in the filename.", False),
                    ("   Formats: YYYYMMDD, DD-Mon-YYYY, DD_Mon_YYYY, DDMonYYYY, DDMMYYYY, etc.", False),
                    ("3. By Creation Date:", True),
                    ("   Uses the date the file was saved to disk.", False),
                    ("4. By Modification Date:", True),
                    ("   Uses the last date the file was edited.", False),
                    ("⚠ **If a file has no detectable date in the chosen mode, it stays in the root folder.**", False),
                ]),
                ("🔘  Main buttons", [
                    ("• Add folder:", True),
                    ("   Adds a single folder to organize.", False),
                    ("• Add multiple folders:", True),
                    ("   Select a root folder and choose which subfolders to add.", False),
                    ("• Organize:", True),
                    ("   Starts organizing the loaded folders according to the chosen mode.", False),
                    ("• Select all / Deselect all:", True),
                    ("   Check or uncheck all folders in the list.", False),
                    ("• Remove selected folders:", True),
                    ("   Removes the checked folders from the list.", False),
                    ("• Undo organization:", True),
                    ("   Moves all files from subfolders back to the root folder and removes empty month folders.", False),
                    ("• Do not add month number:", True),
                    ("   If checked, subfolders won't have the corresponding month number.", False),
                    ("• Translate to English / Traducir al Español:", True),
                    ("   Changes the interface language, tutorial and sets month", False),
                    ("   subfolder names to English when organizing: (1 January, 2 February, etc...).", False),
                    ("   To create the folders in English, just set the program to English and click Organize.", False),
                    ("• Update / Actualización:", True),
                    ("   Opens the GitHub page to download the latest version of the program.", False),
                    ("   The program also automatically checks for updates when it starts.", False),
                ]),
                ("ℹ  Additional information", [
                    ("• Root folder:", True),
                    ("   The original folder you load or select in the program.", False),
                    ("• Supported extensions:", True),
                    ("   The program processes any file type (jpeg, png, mp4, Word, Excel, PDF, etc.):", False),
                    ("   photos/videos use metadata or dates in the name; documents organize best", False),
                    ("   with mode 3 (Creation Date) or 4 (Modification Date), or dates in the name.", False),
                    ("• Interface:", True),
                    ("   Has a window for loading folders, another that shows real-time progress,", False),
                    ("   and at the bottom shows data like: total files organized, total folders created, and elapsed time.", False),
                    ("• Organizing Folder:", True),
                    ("   Shows in real-time which folder is being processed.", False),
                    ("• Status column:", True),
                    ("   Indicates whether the folder has been organized or not. Shows: 'Organized', 'Unorganized', or intermediate states like 'Organizing...' or 'Undoing...'.", False),
                    ("• Content column:", True),
                    ("   When adding a folder, shows total folders and files: 'X folders / Total files'.", False),
                    ("   If the folder is empty, shows: 'Empty Folder'.", False),
                    ("   After organizing, shows files organized and without date: 'Y files organized / Z without date'.", False),
                    ("• Selection column \"Sel\":", True),
                    ("   Check the folders you want to organize or undo.", False),
                    ("• GIF files:", True),
                    ("   They have no capture date or media created date. Only date in the name, creation and modification dates.", False),
                    ("• Valid date range:", True),
                    ("   The program only recognizes valid dates from year **1900** onwards.", False),
                ]),
                ("⚠  Important", [
                    ("• The program **NEVER** deletes your files, it only organizes them.", False),
                    ("• You can always undo the organization done by the program and reorganize in any of the 4 modes.", False),
                    ("• The program does not create empty folders. If a month subfolder is missing, no files had that date.", False),
                    ("• If you don't check **\"Do not add month number\"** the subfolders will include the month number.", False),
                    ("   Example: **\"1 January / 6 June / 12 December\"**.", False),
                    ("• The program does not rename your files or year folders.", False),
                    ("**• Keep in mind that if you add folders you organized yourself, your personal organization**", False),
                    ("**  is lost since the program sorts chronologically and does not save your custom order.**", False),
                ]),
            ]
        else:
            sections_data = [
                ("🤔  ¿Qué hace el programa?", [
                    ("El programa detecta las fechas de tus fotos y videos para crear carpetas por año,", False),
                    ("subcarpetas por mes y luego los mueve a su carpeta correspondiente.", False),
                    ("", False),
                    ("__El programa ofrece 4 modos de organización:__", False),
                    ("1. Por Fecha de Captura, Medio Creado o Nombre.", True),
                    ("2. Por Fecha en el Nombre.", True),
                    ("3. Por Fecha de Creación.", True),
                    ("4. Por Fecha de Modificación.", True),
                ]),
                ("📋  ¿Cómo usar el programa?", [
                    ("1. Agrega la carpeta o carpetas que quieras.", False),
                    ("2. Elige alguno de los 4 modos de organización.", False),
                    ("3. Marca en la columna de selección las carpetas que quieras y da click en organizar.", False),
                ]),
                ("📅  ¿Qué fechas detecta el programa?", [
                    ("  Fecha de captura:", True),
                    ("  Creada por la cámara en el momento exacto en que se tomó la fotografía.", False),
                    ("  Fecha en el nombre del archivo:", True),
                    ("  Algunas cámaras incluyen la fecha en el nombre del archivo al guardar la foto o video.", False),
                    ("  Fecha de modificación:", True),
                    ("  Indica la última vez que el archivo fue editado.", False),
                    ("  Fecha de creación del archivo:", True),
                    ("  Fecha del sistema operativo que indica cuándo se guardó.", False),
                ]),
                ("🗂  Modos de organización", [
                    ("1. Por Fecha de Captura, Medio Creado o Nombre:", True),
                    ("   Organiza primero buscando la Fecha de Captura en fotos (la más precisa tomada por la cámara).", False),
                    ("   Si no la encuentra, busca la fecha de Medio Creado,", False),
                    ("   Si no la tiene, busca fecha en el Nombre del archivo.", False),
                    ("   **Nota:** Los videos no tienen Fecha de Captura sino fecha en", False),
                    ("   Medio Creado (la más precisa cuando se grabo), en los videos,", False),
                    ("   el programa busca primero la fecha en Medio Creado y si no", False),
                    ("   la tiene por último busca la fecha en el Nombre.", False),
                    ("2. Por Fecha en el Nombre:", True),
                    ("   Detecta la fecha en el nombre del archivo.", False),
                    ("   Formatos: YYYYMMDD, DD-Mes-YYYY, DD_Mes_YYYY, DDMesYYYY, DDMMYYYY, etc.", False),
                    ("3. Por Fecha de Creación:", True),
                    ("   Usa la fecha en que el archivo fue guardado en el disco.", False),
                    ("4. Por Fecha de Modificación:", True),
                    ("   Usa la última fecha en que el archivo fue editado.", False),
                    ("⚠ **Si un archivo no tiene fecha detectable en el modo elegido, se deja en la carpeta raíz sin moverla a ninguna subcarpeta de mes.**", False),
                ]),
                ("🔘  Botones principales", [
                    ("• Agregar carpeta:", True),
                    ("   Agrega una sola carpeta para organizar.", False),
                    ("• Agregar varias carpetas:", True),
                    ("   Selecciona una carpeta raíz y elige qué subcarpetas agregar.", False),
                    ("• Organizar:", True),
                    ("   Comienza a organizar las carpetas cargadas según el modo elegido.", False),
                    ("• Seleccionar todo / Deseleccionar todo:", True),
                    ("   Marca o desmarca todas las carpetas de la lista.", False),
                    ("• Quitar Carpetas Seleccionadas:", True),
                    ("   Elimina de la lista las carpetas marcadas con ☑.", False),
                    ("• Deshacer organización:", True),
                    ("   Mueve todos los archivos de las subcarpetas de vuelta a la carpeta raíz y elimina las carpetas de mes vacías.", False),
                    ("   Úsalo cuando quieras reorganizar tus fotos con un modo diferente.", False),
                    ("• No poner número de mes:", True),
                    ("   Si está marcada, las subcarpetas no tendrán número correspondiente al mes.", False),
                    ("• Traducir al Español / Translate to English:", True),
                    ("   Cambia el idioma de la interfaz, el tutorial y al organizar las carpetas pone los nombres de", False),
                    ("   las subcarpetas por mes en ingles: (1 January, 2 February, etc...).", False),
                    ("   Para crear las carpetas en inglés solo pon el programa en inglés y da click en Organizar.", False),
                    ("• Actualización / Update:", True),
                    ("   Abre la página de GitHub para descargar la última versión del programa.", False),
                    ("   El programa también verifica actualizaciones automáticamente al iniciar.", False),
                ]),
                ("ℹ  Información adicional", [
                    ("• Carpeta raíz:", True),
                    ("   Es la misma carpeta original que cargas o seleccionas en el programa.", False),
                    ("• Extensiones soportadas:", True),
                    ("   El programa procesa cualquier tipo de archivo (jpeg, png, mp4, Word, Excel, PDF, etc.):", False),
                    ("   fotos/videos usan metadatos o fechas en el nombre; los documentos organizan mejor", False),
                    ("   con el modo 3 (Fecha de Creación) o 4 (Fecha de Modificación), o con fechas en el nombre.", False),
                    ("• Interfaz:", True),
                    ("   Cuenta con una ventana para carga de carpetas, otra que muestra en tiempo real lo que hace el programa,", False),
                    ("   en la parte inferior muestra datos como: total de archivos organizados, total de carpetas creadas, y el tiempo que duró la organización.", False),
                    ("• Organizando Carpeta:", True),
                    ("   Muestra en tiempo real qué carpeta se está procesando durante la organización o desorganización.", False),
                    ("• Columna Estado:", True),
                    ("   Indica si la carpeta ha sido organizada o no. Muestra: 'Organizado', 'Sin organizar', o estados intermedios como 'Organizando...' o 'Deshaciendo...'.", False),
                    ("• Columna Contenido:", True),
                    ("   Al agregar una carpeta, muestra el total de carpetas y archivos: 'X carpetas / Y Archivos en total'.", False),
                    ("   Si la carpeta está vacía, muestra: 'Carpeta Vacía'.", False),
                    ("   Después de organizar, muestra archivos organizados y sin fecha: 'Y archivos organizados / Z sin fecha'.", False),
                    ("• Columna Selección \"Sel\":", True),
                    ("   Marca las carpetas que quieras organizar o desorganizar.", False),
                    ("• Archivos Gif:", True),
                    ("   No tienen fecha de captura, ni fecha en medio creado, solo se pueden organizar por fecha en el nombre, creación y modificación.", False),
                    ("• Rango de fechas detectadas:", True),
                    ("   El programa solo reconoce fechas válidas desde el año **1.900** en adelante.", False),
                ]),
                ("⚠  Importante", [
                    ("• El programa **NUNCA** borra tus archivos, solo los organiza.", False),
                    ("• Siempre puedes deshacer la organización hecha previamente con el programa y volver a organizarla en cualquiera de los 4 modos las veces que quieras.", False),
                    ("• El programa no crea carpetas vacías, Si falta una subcarpeta de mes es porque no se detectaron fotos con esa fecha en el modo elegido.", False),
                    ("• Si no marcas **\"No poner número de mes\"** las subcarpetas se nombrarán con el número correspondiente al mes,", False),
                    ("   Ejemplo: **\"1 Enero / 6 Junio / 12 Diciembre\"**.", False),
                    ("• El programa no renombra tus archivos ni las carpetas por año.", False),
                    ("• Puedes subir carpetas organizadas y directamente darle a organizar en el modo elegido, el programa deshará la organización previa moviendo todos los archivos a la raíz, eliminando todas las carpetas vacías para organizar todo desde cero.", False),
                    ("**• Ten encuenta que si agregas carpetas organizadas por ti al organizarlas con el programa,**", False),
                    ("**  tu organización personal se pierde ya que el programa ordena cronológicamente**", False),
                    ("**  y no se guarda tu orden personal.**", False),
                ]),
            ]

        section_widgets = {}  # title -> (header_frame, body_frame, open_var)

        # Lista de (sep, hdr, body) para poder insertar body DESPUÉS del hdr
        accordion_items = []

        for sec_title, sec_lines in sections_data:
            sep = ttk.Separator(pad, orient="horizontal")
            sep.pack(fill="x", pady=(8, 2))
            open_var = tk.BooleanVar(value=False)
            hdr = tk.Frame(pad, bg="#f0f4f8", cursor="hand2")
            hdr.pack(fill="x", anchor="w")
            arrow_lbl = tk.Label(hdr, text="► ", font=("Segoe UI", 10, "bold"), fg="#3b82f6", bg="#f0f4f8", cursor="hand2")
            arrow_lbl.pack(side="left")
            title_lbl = tk.Label(hdr, text=sec_title, font=("Segoe UI", 10, "bold"), fg="#3b82f6",
                     justify="left", bg="#f0f4f8", cursor="hand2")
            title_lbl.pack(side="left")
            body = tk.Frame(pad, bg="#f0f4f8")
            # NO hacemos body.pack() aquí — se hará en toggle justo después del hdr
            for text, is_bold in sec_lines:
                if '**' in text or '__' in text:
                    parts = re.split(r'(\*\*.*?\*\*|__.*?__)', text)
                    row = tk.Frame(body, bg="#f0f4f8")
                    row.pack(anchor="w", padx=16, pady=1)
                    for part in parts:
                        if part.startswith('**') and part.endswith('**') and len(part) > 4:
                            inner = part[2:-2]
                            tk.Label(row, text=inner, font=("Segoe UI", 9, "bold"),
                                     justify="left", anchor="w", fg="#1e3a5f", bg="#f0f4f8").pack(side="left")
                        elif part.startswith('__') and part.endswith('__') and len(part) > 4:
                            inner = part[2:-2]
                            tk.Label(row, text=inner, font=("Segoe UI", 9, "underline"),
                                     justify="left", anchor="w", fg="#1e3a5f", bg="#f0f4f8").pack(side="left")
                        else:
                            tk.Label(row, text=part, font=("Segoe UI", 9),
                                     justify="left", anchor="w", fg="#1e3a5f", bg="#f0f4f8").pack(side="left")
                else:
                    font = ("Segoe UI", 9, "bold") if is_bold else ("Segoe UI", 9)
                    tk.Label(body, text=text, font=font, justify="left",
                             wraplength=wrap_width - 20, anchor="w", fg="#1e3a5f", bg="#f0f4f8").pack(anchor="w", padx=16, pady=1)
            accordion_items.append((sep, hdr, body, open_var, arrow_lbl))
            section_widgets[sec_title] = (hdr, body, open_var, arrow_lbl)

        # Separador y botón cerrar al final (para poder usar pack(before=...))
        final_sep = ttk.Separator(pad, orient="horizontal")
        final_sep.pack(fill="x", pady=(12, 0))
        close_btn = ttk.Button(pad, text="Close" if getattr(self, 'english_mode', False) else "Cerrar", command=lambda: [canvas.unbind_all("<MouseWheel>"), w.destroy()])
        close_btn.pack(pady=(34, 0))

        def make_toggle(bv, bd, al, after_widget, current_i):
            def toggle(e=None):
                if bv.get():
                    bd.pack_forget()
                    bv.set(False)
                    al.configure(text="► ")
                else:
                    for j, (_, _, other_body, other_var, other_arrow) in enumerate(accordion_items):
                        if j != current_i and other_var.get():
                            other_body.pack_forget()
                            other_var.set(False)
                            other_arrow.configure(text="► ")
                    bd.pack(fill="x", anchor="w", before=after_widget)
                    bv.set(True)
                    al.configure(text="▼ ")
                pad.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
            return toggle

        for i, (sep, hdr, body, open_var, arrow_lbl) in enumerate(accordion_items):
            if i + 1 < len(accordion_items):
                after_widget = accordion_items[i + 1][0]
            else:
                after_widget = final_sep
            fn = make_toggle(open_var, body, arrow_lbl, after_widget, i)
            hdr.bind("<Button-1>", fn)
            arrow_lbl.bind("<Button-1>", fn)
            for child in hdr.winfo_children():
                child.bind("<Button-1>", fn)


        # Ajustar tamaño: ancho fijo 780 para que el texto quepa, alto adaptable
        w.update_idletasks()
        sw = w.winfo_screenwidth()
        sh = w.winfo_screenheight()
        desired_width = 820
        # Posicionar debajo de los botones de la ventana principal
        main_x = self.winfo_rootx()
        main_y = self.winfo_rooty()
        main_w = self.winfo_width()
        main_h = self.winfo_height()
        # Ancho casi igual al de la ventana principal
        desired_width = max(820, min(main_w - 20, sw - 40))
        # Posición: justo debajo de la barra de botones y opciones (~130px desde el top de la ventana principal)
        toolbar_offset = 130  # toolbar + modo de organización + checkbox
        x = main_x + 10
        y_start = main_y + toolbar_offset
        # Forzar el ancho del contenido ANTES de medir altura, para que
        # wraplength se calcule correctamente y no quede espacio extra
        canvas.itemconfig(pad_id, width=desired_width - 20)
        pad.update_idletasks()
        canvas.update_idletasks()
        bbox = canvas.bbox("all")
        real_content_height = (bbox[3] - bbox[1] + 20) if bbox else (pad.winfo_reqheight() + 20)
        taskbar = 60
        avail_h = sh - taskbar - y_start
        # Ventana ajustada al contenido real, con margen mínimo para no recortar el botón Cerrar
        desired_content_height = real_content_height - 5  # compensar padding extra del botón Cerrar
        if avail_h >= 300:
            max_h = avail_h - 40
            final_height = min(desired_content_height, max(360, max_h))
            y = y_start
        else:
            final_height = min(desired_content_height, sh - taskbar - 60)
            y = max(30, main_y + toolbar_offset)
        w.geometry(f"{desired_width}x{final_height}+{x}+{y}")
        w.deiconify()
        w.focus_force()
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.yview_moveto(0)
        self.tutorial_win.win = w
    def _action_icon(self, parent, glyph, cmd):
        return ctk.CTkButton(parent, text=glyph, width=34, height=28, corner_radius=8,
                             fg_color="white", hover_color="#f1f5f9", border_width=2,
                             border_color="#cbd5e1", text_color="#475569",
                             font=("Segoe UI", 15), command=cmd)

    def on_support(self):
        self._close_aux_windows()
        w = tk.Toplevel(self)
        w.withdraw()
        eng = getattr(self, 'english_mode', False)
        w.title("Support" if eng else "Soporte")
        w.resizable(False, False)
        w.configure(bg="#f0f4f8")
        w.transient(self)
        pad = ctk.CTkFrame(w, fg_color="#e8eef5", corner_radius=12)
        pad.pack(fill="both", expand=True, padx=15, pady=15)
        ctk.CTkLabel(pad, text="¿Do you have any questions,\nsuggestions or want to report a problem?" if eng else "¿Tienes alguna duda, sugerencia\no reportar un problema del programa?",
                     font=("Segoe UI", 15, "bold"), text_color="#1e3a5f", justify="center").pack(pady=(0, 10))
        ctk.CTkLabel(pad, text="👇", font=("Segoe UI", 22), text_color="#f59e0b").pack(pady=(0, 4))
        ctk.CTkLabel(pad, text="¡Write to us!" if eng else "¡Escríbenos!",
                     font=("Segoe UI", 14, "bold"), text_color="#475569").pack(pady=(0, 4))

        def copy_mail(e=None, widget=None):
            self.clipboard_clear()
            self.clipboard_append("click2folders@gmail.com")
            msg = "Email copied to clipboard" if getattr(self, 'english_mode', False) else "Correo copiado al portapapeles"
            if e:
                x = e.x_root
                y = e.y_root - 30
                self._show_tooltip_at(msg, x, y)
            elif widget is not None:
                self._show_tooltip_temporal(msg, widget=widget)

        mail_row = ctk.CTkFrame(pad, fg_color="#e8eef5")
        mail_row.pack(pady=(0, 8))
        mail = ctk.CTkLabel(mail_row, text="click2folders@gmail.com",
                            font=("Segoe UI", 15, "underline"), text_color="#3b82f6", cursor="hand2")
        mail.pack(side="left", padx=(0, 10))
        mail.bind("<Button-1>", copy_mail)
        mail_icon = self._action_icon(mail_row, "⧉", lambda: copy_mail(widget=mail_icon))
        mail_icon.pack(side="left")
        self.support_win.win = w
        safe_icon(w)
        center_window(w, self)
        w.deiconify()
        for sw in (w, pad):
            sw.bind("<Button-3>", lambda e: "break")
            sw.bind("<Button-2>", lambda e: "break")

    def _show_tooltip_at(self, message, x, y):
        tooltip = tk.Toplevel(self)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(tooltip, text=message,
                             fg_color="#fef3c7", text_color="#92400e", corner_radius=8,
                             font=("Segoe UI", 11), padx=10, pady=6)
        label.pack()
        tooltip.after(2000, lambda: tooltip.destroy())

    def _show_tooltip_temporal(self, message, widget=None, event=None):
        try:
            tooltip = tk.Toplevel(self)
            tooltip.wm_overrideredirect(True)
            if event is not None:
                x, y = event.x_root + 8, event.y_root - 28
            elif widget is not None:
                x = widget.winfo_rootx() + widget.winfo_width() // 2 - 40
                y = widget.winfo_rooty() - 32
            else:
                x, y = self.winfo_rootx() + 100, self.winfo_rooty() + 100
            tooltip.wm_geometry(f"+{x}+{y}")
            ctk.CTkLabel(tooltip, text=message, fg_color="#fef3c7", text_color="#92400e",
                        corner_radius=8, font=("Segoe UI", 11), padx=10, pady=6).pack()
            tooltip.after(2000, lambda: tooltip.destroy() if tooltip.winfo_exists() else None)
        except Exception:
            pass

    def on_donate(self):
        try:
            self._do_on_donate()
        except Exception as ex:
            import traceback
            traceback.print_exc()
            try:
                self._show_modern_popup(f"Error: {ex}")
            except Exception:
                pass

    def _do_on_donate(self):
        self._close_aux_windows()
        w = tk.Toplevel(self)
        w.withdraw()
        eng = getattr(self, 'english_mode', False)
        w.title("Donations" if eng else "Donaciones")
        w.resizable(False, False)
        w.configure(bg="#f0f4f8")
        safe_icon(w)

        pad = ctk.CTkFrame(w, fg_color="#e8eef5", corner_radius=12)
        pad.pack(fill="both", expand=True, padx=15, pady=15)

        # Títulos
        ctk.CTkLabel(pad, text="Thank you for using Click2Folders!" if eng else "¡Gracias por usar Click2Folders!", 
                     font=("Segoe UI", 14, "bold"), text_color="#1e3a5f", justify="center").pack(pady=(0, 4))
        ctk.CTkLabel(pad, text="Click2Folders is free and has no annoying ads." if eng else "Click2Folders es libre y no tiene molestos anuncios.", 
                     font=("Segoe UI", 12), text_color="#475569", justify="center").pack(pady=(0, 3))
        ctk.CTkLabel(pad, text="Consider donating to keep it that way!" if eng else "¡Considera donar para que siga siendo así!", 
                     font=("Segoe UI", 12, "bold"), text_color="#475569", justify="center").pack(pady=(0, 10))

        # --- PAYPAL ---
        paypal_outer = ctk.CTkFrame(pad, fg_color="white", corner_radius=12, border_width=2, border_color="#1e3a5f")
        paypal_outer.pack(fill="x", pady=(0, 6), padx=10)
        paypal_content = ctk.CTkFrame(paypal_outer, fg_color="white", corner_radius=12)
        paypal_content.pack(anchor="center", pady=8, padx=8)
        paypal_logo = load_image("BAUL/paypal-logo.jpg", max_width=100, max_height=55)
        if paypal_logo:
            lbl = ctk.CTkLabel(paypal_content, image=paypal_logo, text="", cursor="hand2", fg_color="white")
            lbl.image = paypal_logo
            lbl.pack(side="left", padx=12)
            lbl.bind("<Button-1>", lambda e: webbrowser.open("https://www.paypal.com/donate?hosted_button_id=JMPWGD5VA32UW"))

        paypal_btn_img = load_image("BAUL/paypal_donate.gif")
        if paypal_btn_img:
            btn = ctk.CTkLabel(paypal_content, image=paypal_btn_img, text="", cursor="hand2", fg_color="white")
            btn.image = paypal_btn_img
            btn.pack(side="left", padx=(12, 0))
            btn.bind("<Button-1>", lambda e: webbrowser.open("https://www.paypal.com/donate?hosted_button_id=JMPWGD5VA32UW"))
        self._action_icon(paypal_content, "↗", lambda: webbrowser.open("https://www.paypal.com/donate?hosted_button_id=JMPWGD5VA32UW")).pack(side="left", padx=(14, 6))

        # Separador
        ctk.CTkFrame(pad, fg_color="#e8eef5", height=1).pack(fill="x", pady=1, padx=10)

        # --- NEQUI ---
        nequi_outer = ctk.CTkFrame(pad, fg_color="white", corner_radius=12, border_width=2, border_color="#1e3a5f")
        nequi_outer.pack(fill="x", pady=(0, 6), padx=10)
        nequi_content = ctk.CTkFrame(nequi_outer, fg_color="white", corner_radius=12)
        nequi_content.pack(anchor="center", pady=8, padx=8)

        def open_nequi_checkout(e=None):
            try:
                webbrowser.open("https://checkout.nequi.wompi.co/l/EYGaPV")
            except Exception:
                self.clipboard_clear()
                self.clipboard_append("https://checkout.nequi.wompi.co/l/EYGaPV")

        nequi_logo = load_image("BAUL/nequi.jpg", max_width=60, max_height=40)
        if nequi_logo:
            lbl = ctk.CTkLabel(nequi_content, image=nequi_logo, text="", cursor="hand2", fg_color="white")
            lbl.image = nequi_logo
            lbl.pack(side="left", padx=(10, 10))
            lbl.bind("<Button-1>", open_nequi_checkout)
        nequi_right = ctk.CTkFrame(nequi_content, fg_color="white")
        nequi_right.pack(side="left")
        ctk.CTkLabel(nequi_right, text="Donate with Nequi:" if eng else "Donaciones por Nequi:", 
                     font=("Segoe UI", 12, "bold"), text_color="#1e3a5f", fg_color="white").pack(anchor="w")

        nequi_link = ctk.CTkLabel(nequi_right, text="https://checkout.nequi.wompi.co/l/EYGaPV", 
                                  font=("Segoe UI", 11), text_color="#3b82f6", cursor="hand2", fg_color="white")
        nequi_link.bind("<Button-1>", open_nequi_checkout)
        nequi_link.pack(anchor="w")
        self._action_icon(nequi_content, "↗", open_nequi_checkout).pack(side="left", padx=(12, 6))

        # Separador
        ctk.CTkFrame(pad, fg_color="#e8eef5", height=1).pack(fill="x", pady=1, padx=10)

        # --- TETHER ---
        tether_outer = ctk.CTkFrame(pad, fg_color="white", corner_radius=12, border_width=2, border_color="#1e3a5f")
        tether_outer.pack(fill="x", pady=(0, 6), padx=10)
        tether_content = ctk.CTkFrame(tether_outer, fg_color="white", corner_radius=12)
        tether_content.pack(anchor="center", pady=8, padx=8)
        tether_left = ctk.CTkFrame(tether_content, fg_color="white")
        tether_left.pack(side="left", padx=(10, 10))
        tether_logo = load_image("BAUL/Tether.png", max_width=50, max_height=50)
        if tether_logo:
            lbl = ctk.CTkLabel(tether_left, image=tether_logo, text="", fg_color="white")
            lbl.image = tether_logo
            lbl.pack()
        tether_right = ctk.CTkFrame(tether_content, fg_color="white")
        tether_right.pack(side="left")
        ctk.CTkLabel(tether_right, text="Tether USDT (TRC20):", 
                     font=("Segoe UI", 12, "bold"), text_color="#1e3a5f", fg_color="white").pack(anchor="w")

        def copy_usdt(e=None, widget=None):
            self.clipboard_clear()
            self.clipboard_append("TFKbpPK5n5Dv3NV3svEDAyd68fxNyUzmDn")
            msg = "USDT address copied to clipboard" if getattr(self, 'english_mode', False) else "Dirección USDT copiada al portapapeles"
            if e is not None:
                self._show_tooltip_temporal(msg, event=e)
            elif widget is not None:
                self._show_tooltip_temporal(msg, widget=widget)

        addr_row = ctk.CTkFrame(tether_right, fg_color="white")
        addr_row.pack(anchor="w")
        usdt_label = ctk.CTkLabel(addr_row, text="TFKbpPK5n5Dv3NV3svEDAyd68fxNyUzmDn", 
                                  font=("Segoe UI", 11), text_color="#3b82f6", cursor="hand2", fg_color="white")
        usdt_label.bind("<Button-1>", copy_usdt)
        usdt_label.pack(side="left", padx=(0, 8))
        usdt_icon = self._action_icon(addr_row, "⧉", lambda: copy_usdt(widget=usdt_icon))
        usdt_icon.pack(side="left")

        # Separador
        ctk.CTkFrame(pad, fg_color="#e8eef5", height=1).pack(fill="x", pady=1, padx=10)

        # Pie
        thanks_emoji_frame = tk.Frame(pad, bg="#e8eef5")
        thanks_emoji_frame.pack(pady=(0, 4))
        ctk.CTkLabel(thanks_emoji_frame, text="Thank you for your support!" if eng else "¡Gracias por tu apoyo!", 
                     font=("Segoe UI", 13, "bold"), text_color="#1e3a5f", justify="center", bg_color="#e8eef5").pack(side="left")
        emoji_img = load_image("BAUL/Emoji.png", max_width=80, max_height=80)
        if emoji_img:
            emoji_lbl = tk.Label(thanks_emoji_frame, image=emoji_img, bg="#e8eef5")
            emoji_lbl.image = emoji_img
            emoji_lbl.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(pad, text="Developed by: Germán Vargas" if eng else "Desarrollado por: Germán Vargas", 
                     font=("Segoe UI", 12, "bold"), text_color="#475569", justify="center").pack(pady=(0, 2))
        ctk.CTkLabel(pad, text="© 2026 Click2Folders. All rights reserved." if eng else "© 2026 Click2Folders. Todos los derechos reservados.", 
                     font=("Segoe UI", 11), text_color="#64748b", justify="center").pack(pady=(0, 4))

        # === CENTRADO Y FOCO ===
        w.update_idletasks()
        w.minsize(440, 420)
        center_window(w)
        w.deiconify()
        w.focus_force()
        w.lift()
        self.donate_win.win = w
        w.protocol("WM_DELETE_WINDOW", lambda: (w.destroy(), self._on_donate_closed()))
        for dw in (w, pad):
            dw.bind("<Button-3>", lambda e: "break")
            dw.bind("<Button-2>", lambda e: "break")

    def _check_launch_donation(self):
        count = _get_launch_count()
        self._donate_shown = False
        self._donate_closed = False
        if count > 1 and count % 2 == 0:
            self._donate_shown = True
            self.on_donate()
        else:
            self._donate_closed = True
        self._check_for_updates()

    def _on_donate_closed(self):
        self._donate_closed = True
        self._try_show_update()

    def _try_show_update(self):
        if self._has_update and self._donate_closed:
            self.after(500, self._show_update_popup)
        elif not self._update_checked:
            self.after(200, self._try_show_update)

    def _check_for_updates(self):
        if self._update_checked:
            return
        self._update_checked = True
        def _do_check():
            try:
                import urllib.request
                import json
                req = urllib.request.Request(GITHUB_API_URL, headers={"User-Agent": "Click2Folders"})
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    remote_version = data.get("tag_name", "")
                    if remote_version and self._version_is_newer(remote_version, APP_VERSION):
                        self._has_update = True
                        self._latest_release_url = data.get("html_url", GITHUB_RELEASES_URL)
                        if not self._donate_shown:
                            self.after(100, self._show_update_popup)
            except Exception as ex:
                print(f"[Update check error] {ex}")
        threading.Thread(target=_do_check, daemon=True).start()

    def _version_is_newer(self, remote, local):
        def parse(v):
            v = v.lstrip("v").split(".")
            return tuple(int(x) for x in v)
        try:
            return parse(remote) > parse(local)
        except Exception:
            return False

    def _show_update_popup(self):
        eng = getattr(self, 'english_mode', False)
        popup = tk.Toplevel(self)
        popup.withdraw()
        popup.configure(bg="#f0f4f8")
        popup.title("Update available" if eng else "Actualización disponible")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
        safe_icon(popup)
        frm = ctk.CTkFrame(popup, fg_color="#e8eef5", corner_radius=12)
        frm.pack(fill="both", expand=True, padx=15, pady=15)
        t1_es = "🚀 ¡Actualización disponible!"
        t1_en = "🚀 Update available!"
        lbl1 = tk.Label(frm, text=(t1_en if eng else t1_es),
                 font=("Segoe UI", 12, "bold"), fg="#1e3a5f", justify="center", bg="#f0f4f8")
        lbl1.pack(pady=(10, 8))
        t2_es = f"Descarga la última versión desde GitHub.\n{APP_VERSION}"
        t2_en = f"Download the latest version from GitHub.\n{APP_VERSION}"
        lbl2 = tk.Label(frm, text=(t2_en if eng else t2_es),
                 font=("Segoe UI", 10), fg="#475569", justify="center", bg="#f0f4f8")
        lbl2.pack(pady=(0, 12))
        btn_frame = tk.Frame(frm, bg="#e8eef5")
        btn_frame.pack(pady=(0, 5))
        d_es, d_en = "Descargar", "Download"
        l_es, l_en = "Después", "Later"
        btn_dl = ctk.CTkButton(btn_frame, text=(d_en if eng else d_es),
                      fg_color="#10b981", hover_color="#059669", text_color="white",
                      command=lambda: (webbrowser.open(GITHUB_RELEASES_URL), popup.destroy()))
        btn_dl.pack(side="left", padx=6)
        btn_later = ctk.CTkButton(btn_frame, text=(l_en if eng else l_es),
                      fg_color="#64748b", hover_color="#475569", text_color="white",
                      command=popup.destroy)
        btn_later.pack(side="left", padx=6)
        self._register_live_popup(popup, "Actualización disponible", "Update available",
                                  [(lbl1, t1_es, t1_en), (lbl2, t2_es, t2_en),
                                   (btn_dl, d_es, d_en), (btn_later, l_es, l_en)])
        center_window(popup, self)
        popup.deiconify()

    # === FUNCIONES AUXILIARES PARA DONACIONES ===
    def _load_donation_img_async(self, container, url, parent, display_fn):
        try:
            import urllib.request
            from io import BytesIO
            with urllib.request.urlopen(url) as response:
                img_data = response.read()
                img = Image.open(BytesIO(img_data))
                photo = ImageTk.PhotoImage(img)
                self.after(0, lambda: display_fn(container, photo, parent))
        except Exception:
            pass

    def _load_qr_async(self, container, parent):
        try:
            import urllib.request
            from io import BytesIO
            with urllib.request.urlopen("https://postimg.cc/MvbVg5wT") as response:
                img_data = response.read()
                img = Image.open(BytesIO(img_data))
                img = img.resize((150, 150), Image.LANCZOS)
                qr_photo = ImageTk.PhotoImage(img)
                self.after(0, lambda: self._display_qr(container, qr_photo, parent))
        except Exception:
            pass

    def _display_qr(self, container, qr_photo, parent):
        qr_label = ctk.CTkLabel(container, image=qr_photo, text="")
        qr_label.image = qr_photo
        qr_label.pack()
        self.after(100, lambda: center_window(parent, self))

    def _load_paypal_async(self, container, parent):
        try:
            import urllib.request
            from io import BytesIO
            with urllib.request.urlopen("https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif") as response:
                img_data = response.read()
                img = Image.open(BytesIO(img_data))
                photo = ImageTk.PhotoImage(img)
                self.after(0, lambda: self._display_paypal_btn(container, photo, parent))
        except Exception:
            pass

    def _show_image_window(self, parent, img_path):
        w = tk.Toplevel(parent)
        w.withdraw()
        w.configure(bg="#f0f4f8")
        w.resizable(False, False)
        frm = tk.Frame(w, bg="#f0f4f8")
        frm.pack(fill="both", expand=True)
        img = load_image(img_path, max_width=860, max_height=560)
        if img is None:
            lbl = tk.Label(frm, text=f"No se pudo cargar la imagen:\n{img_path}", fg="#ef4444", justify="center", bg="#f0f4f8")
            lbl.pack()
        else:
            lbl = ctk.CTkLabel(frm, image=img, text="")
            lbl.image = img
            lbl.pack()
        center_window(w, parent)
        w.deiconify()
        return w

    def _register_live_popup(self, win, title_es, title_en, widgets):
        """Registra un popup modal para que sus textos se actualicen
        en vivo cuando el usuario cambia de idioma con el botón Traducir.
        widgets: lista de (widget, texto_es, texto_en)."""
        entry = {"win": win, "title_es": title_es, "title_en": title_en, "widgets": widgets}
        self._live_popups.append(entry)

        def _on_destroy(event, ent=entry):
            if event.widget is win:
                try:
                    self._live_popups.remove(ent)
                except ValueError:
                    pass
        win.bind("<Destroy>", _on_destroy, add="+")

    def _show_modern_popup(self, message):
        popup = tk.Toplevel(self)
        popup.withdraw()
        popup.configure(bg="#f0f4f8")
        eng_pop = getattr(self, 'english_mode', False)
        popup.title("Notice" if eng_pop else "Aviso")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
        safe_icon(popup)
        if isinstance(message, tuple):
            msg_es, msg_en = message
        else:
            msg_es = msg_en = message
        frm = ctk.CTkFrame(popup, fg_color="#e8eef5", corner_radius=12)
        frm.pack(fill="both", expand=True, padx=15, pady=15)
        lbl = tk.Label(frm, text=(msg_en if eng_pop else msg_es), font=("Segoe UI", 10), justify="center", fg="#1e3a5f", bg="#f0f4f8")
        lbl.pack(pady=(10, 20))
        ok_btn = ctk.CTkButton(frm, text="OK" if eng_pop else "Aceptar", command=popup.destroy,
                      fg_color="#3b82f6", hover_color="#2563eb", text_color="white")
        ok_btn.pack()
        self._register_live_popup(popup, "Aviso", "Notice",
                                  [(lbl, msg_es, msg_en), (ok_btn, "Aceptar", "OK")])
        center_window(popup, self)
        popup.deiconify()

    def on_add_folder(self):
        folder = filedialog.askdirectory(title="Select folder to organize" if self.english_mode else "Selecciona carpeta a organizar")
        if folder:
            self._add_single_folder(folder)

    def _add_single_folder(self, folder):
        folder_norm = os.path.normcase(os.path.abspath(folder))
        if folder_norm in self.queue:
            return
        self._clear_placeholder_rows()
        # Resetear log y contadores al agregar carpetas (nueva sesión)
        self._clear_log()
        self._reset_counters()
        eng_add = getattr(self, 'english_mode', False)
        status = "Sin organizar" if not eng_add else "Unorganized"
        files, subfolders = count_folder_contents(folder)
        cantidad = f"{subfolders} {'carpetas' if not eng_add else 'folders'} / {files} {'Archivos en total' if not eng_add else 'Total files'}" if (files > 0 or subfolders > 0) else ("Carpeta Vacía" if not eng_add else "Empty Folder")
        tag = "oddrow" if len(self.queue) % 2 == 0 else "evenrow"
        item_id = self.tree.insert("", "end", values=("☐", folder, cantidad, status), tags=(tag,))
        if hasattr(self, '_tree_checked'):
            self._tree_checked[item_id] = False
        self.queue.append(folder_norm)
        self.folder_indexes[folder_norm] = item_id
        self._update_undo_button_state()
        self.after(100, self._fit_folder)

    def on_add_multiple_folders(self):
        if getattr(self, '_no_show_multiple_intro', False):
            self._pick_multiple_folders()
            return
        eng = getattr(self, 'english_mode', False)
        # Ventana de instrucción previa
        intro = tk.Toplevel(self)
        intro.withdraw()
        intro.configure(bg="#f0f4f8")
        eng = getattr(self, 'english_mode', False)
        intro.title("Add multiple folders" if eng else "Agregar varias carpetas")
        intro.resizable(False, False)
        intro.transient(self)
        intro.grab_set()
        safe_icon(intro)
        frm = ctk.CTkFrame(intro, fg_color="#e8eef5", corner_radius=12)
        frm.pack(fill="both", expand=True, padx=15, pady=15)
        tk.Label(frm, text="How does it work?" if eng else "¿Cómo funciona?", font=("Segoe UI", 11, "bold"), fg="#1e3a5f", bg="#f0f4f8").pack(pady=(0,10))
        tk.Label(frm, text="Select a root folder and the program will show\nall its subfolders so you can choose which ones to add." if eng else "Selecciona una carpeta raíz y el programa mostrará\ntodas sus subcarpetas para que elijas cuáles agregar.",
                     font=("Segoe UI", 10), justify="center", fg="#1e3a5f", bg="#f0f4f8").pack(pady=(0,16))
        no_show_intro_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(frm, text="Don't show this message again" if eng else "No volver a mostrar este mensaje", variable=no_show_intro_var,
                        fg_color="#3b82f6", hover_color="#1d4ed8", text_color="#1e3a5f").pack(pady=(0, 10))
        def do_intro_ok():
            self._no_show_multiple_intro = no_show_intro_var.get()
            intro.grab_release()
            intro.destroy()
            self._pick_multiple_folders()
        def do_intro_cancel():
            intro.grab_release()
            intro.destroy()
        btn_row = tk.Frame(frm, bg="#f0f4f8")
        btn_row.pack()
        ctk.CTkButton(btn_row, text="Got it" if eng else "Entendido", command=do_intro_ok,
                      fg_color="#3b82f6", hover_color="#2563eb", text_color="white").pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Cancel" if eng else "Cancelar", command=do_intro_cancel,
                      fg_color="#64748b", hover_color="#475569", text_color="white").pack(side="left", padx=6)
        center_window(intro, self)
        intro.deiconify()

    def _pick_multiple_folders(self):
        # Selección múltiple desde explorador de Windows usando tkinter con truco de múltiples selecciones
        # Tkinter no soporta selección múltiple nativa en askdirectory, pero podemos
        # usar una carpeta raíz y mostrar el árbol de selección
        root_folder = filedialog.askdirectory(title="Select the root folder containing subfolders" if getattr(self, 'english_mode', False) else "Selecciona la carpeta raíz que contiene las subcarpetas")
        if not root_folder:
            return
        try:
            subdirs = sorted([os.path.join(root_folder, d) for d in os.listdir(root_folder)
                              if os.path.isdir(os.path.join(root_folder, d))])
        except Exception:
            subdirs = []
        candidates = subdirs
        if not candidates:
            eng_sub = getattr(self, 'english_mode', False)
            messagebox.showinfo("No subfolders" if eng_sub else "Sin subcarpetas", "No subfolders found in the selected location." if eng_sub else "No se encontraron subcarpetas en la ubicación seleccionada.")
            return

        win = tk.Toplevel(self)
        win.withdraw()
        win.configure(bg="#f0f4f8")
        eng_pick2 = getattr(self, 'english_mode', False)
        win.title("Select folders" if eng_pick2 else "Seleccionar Carpetas")
        win.resizable(True, True)
        win.transient(self)
        win.grab_set()
        safe_icon(win)

        tk.Label(win, text=f"Raíz: {root_folder}", font=("Segoe UI", 9), fg="#64748b", bg="#f0f4f8").pack(anchor="w", padx=12, pady=(10,0))

        sel_bar = tk.Frame(win, bg="#f0f4f8")
        sel_bar.pack(fill="x", padx=12, pady=(0,4))
        check_vars = {}
        cb_list = []
        last_clicked = [None]

        def select_all():
            for path, (var, cb) in check_vars.items():
                norm = os.path.normcase(os.path.abspath(path))
                if norm not in self.queue: var.set(True)

        def deselect_all():
            for var, cb in check_vars.values(): var.set(False)

        eng_pick = getattr(self, 'english_mode', False)
        ctk.CTkButton(sel_bar, text="Select all" if eng_pick else "Seleccionar todo", command=select_all,
                      fg_color="#64748b", hover_color="#475569", text_color="white", corner_radius=8, height=28, font=("Segoe UI", 11)).pack(side="left", padx=4)
        ctk.CTkButton(sel_bar, text="Deselect all" if eng_pick else "Deseleccionar todo", command=deselect_all,
                      fg_color="#64748b", hover_color="#475569", text_color="white", corner_radius=8, height=28, font=("Segoe UI", 11)).pack(side="left", padx=4)

        # Tamaño adaptable: máx 15 items visibles, con scroll si hay más
        ITEM_H = 28
        MAX_VIS = 15
        n = len(candidates)
        list_h = min(n * ITEM_H + 10, MAX_VIS * ITEM_H)
        use_scroll = n > MAX_VIS

        frame_list = tk.Frame(win, bg="#f0f4f8")
        frame_list.pack(fill="both", expand=use_scroll, padx=12, pady=4)

        if use_scroll:
            canvas_w = tk.Canvas(frame_list, highlightthickness=0, height=list_h)
            vsb = ctk.CTkScrollbar(frame_list, command=canvas_w.yview, fg_color="#cbd5e1", button_color="#94a3b8")
            canvas_w.configure(yscrollcommand=vsb.set)
            vsb.pack(side="right", fill="y", padx=(2, 0), pady=5)
            canvas_w.pack(side="left", fill="both", expand=True)
            inner = tk.Frame(canvas_w, bg="#f0f4f8")
            inner_id = canvas_w.create_window((0,0), window=inner, anchor="nw")
            inner.bind("<Configure>", lambda e: canvas_w.configure(scrollregion=canvas_w.bbox("all")))
            canvas_w.bind("<Configure>", lambda e: canvas_w.itemconfig(inner_id, width=e.width))
            canvas_w.bind_all("<MouseWheel>", lambda e: canvas_w.yview_scroll(int(-1*(e.delta/120)), "units"))
            container = inner
        else:
            canvas_w = None
            container = frame_list

        for idx, path in enumerate(candidates):
            var = tk.BooleanVar(value=True)
            norm = os.path.normcase(os.path.abspath(path))
            already = norm in self.queue
            name = os.path.basename(path) or path
            extra = "  (ya en lista)" if already else ""
            cb = tk.Checkbutton(container, text=f"  {name}{extra}", variable=var,
                                 state="disabled" if already else "normal",
                                 selectcolor="white", anchor="w")
            if already: var.set(False)
            cb.pack(anchor="w", pady=2, padx=8)
            check_vars[path] = (var, cb)
            cb_list.append((path, var, cb))

            def make_handler(i):
                def handler(event):
                    if event.state & 0x0001 and last_clicked[0] is not None:  # Shift
                        start, end = sorted([last_clicked[0], i])
                        for k in range(start, end + 1):
                            p, v, _ = cb_list[k]
                            if os.path.normcase(os.path.abspath(p)) not in self.queue:
                                v.set(True)
                    last_clicked[0] = i
                return handler
            cb.bind("<Button-1>", make_handler(idx))

        btns = tk.Frame(win, bg="#f0f4f8")
        btns.pack(pady=8)

        def do_add():
            to_add = [p for p, (v, _) in check_vars.items() if v.get()]
            if canvas_w: canvas_w.unbind_all("<MouseWheel>")
            win.grab_release()
            win.destroy()
            added = 0
            if to_add:
                self._clear_placeholder_rows()
                # Resetear log y contadores al agregar carpetas (nueva sesión)
                self._clear_log()
                self._reset_counters()
            for path in to_add:
                norm = os.path.normcase(os.path.abspath(path))
                if norm not in self.queue:
                    eng_s = getattr(self, 'english_mode', False)
                    files, subfolders = count_folder_contents(path)
                    cantidad = f"{subfolders} {'carpetas' if not eng_s else 'folders'} / {files} {'Archivos en total' if not eng_s else 'Total files'}" if (files > 0 or subfolders > 0) else ("Carpeta Vacía" if not eng_s else "Empty Folder")
                    status = "Sin organizar" if not eng_s else "Unorganized"
                    tag = "oddrow" if len(self.queue) % 2 == 0 else "evenrow"
                    item_id = self.tree.insert("", "end", values=("☐", path, cantidad, status), tags=(tag,))
                    if hasattr(self, '_tree_checked'): self._tree_checked[item_id] = False
                    self.queue.append(norm)
                    self.folder_indexes[norm] = item_id
                    added += 1
            self._update_undo_button_state()
            if added:
                self._log(f"✓ {added} {'folder(s) added' if getattr(self, 'english_mode', False) else 'carpeta(s) agregada(s)'}")
                self.after(100, self._fit_folder)

        def do_cancel():
            if canvas_w: canvas_w.unbind_all("<MouseWheel>")
            win.grab_release()
            win.destroy()
            # No agrega nada

        eng_b = getattr(self, 'english_mode', False)
        ctk.CTkButton(btns, text="Add selected" if eng_b else "Agregar seleccionadas", command=do_add,
                      fg_color="#10b981", hover_color="#059669", text_color="white").pack(side="left", padx=8)
        ctk.CTkButton(btns, text="Cancel" if eng_b else "Cancelar", command=do_cancel,
                      fg_color="#ef4444", hover_color="#dc2626", text_color="white").pack(side="left", padx=8)

        # Tamaño adaptable: no exceder la pantalla menos barra de tareas
        win.update_idletasks()
        win.update()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        taskbar_h = 70
        # Calcular alto exacto del contenido
        actual_h = win.winfo_reqheight() + 20
        final_h = min(actual_h, sh - taskbar_h - 40)
        final_w = min(560, sw - 80)
        x = (sw - final_w) // 2
        y = max(30, min((sh - final_h) // 2, sh - final_h - taskbar_h - 10))
        win.geometry(f"{final_w}x{final_h}+{x}+{y}")
        win.deiconify()
    def _undo_organization_for_folder(self, folder_path, show_message=True):
        try:
            self.after(0, lambda fp=folder_path, e2=getattr(self, 'english_mode', False): self._log(f"{'Undoing organization in:' if e2 else 'Deshaciendo organización en:'} {os.path.basename(fp)}"))
            undo_organization_simple(folder_path)
            self.after(0, lambda fp=folder_path, e3=getattr(self, 'english_mode', False): self._log(f"✓ {'Organization undone in:' if e3 else 'Organización deshecha en:'} {os.path.basename(fp)}"))
            if show_message:
                eng_und = getattr(self, 'english_mode', False)
                messagebox.showinfo("Sin organizar" if not eng_und else "Undone",
                                    "The organization has been undone successfully.\nAll files have been moved back to the root folder." if eng_und else "La organización ha sido deshecha correctamente.\nTodos los archivos han sido movidos de vuelta a la carpeta raíz.")
        except Exception as e:
            self.after(0, lambda err=e, e4=getattr(self, 'english_mode', False): self._log(
                f"{'Error undoing organization:' if e4 else 'Error deshaciendo organización:'} {err}"))
            if show_message:
                eng_und2 = getattr(self, 'english_mode', False)
                messagebox.showerror("Error" if eng_und2 else "Error", f"Could not undo the organization: {e}" if eng_und2 else f"No se pudo deshacer la organización: {e}")

    def _set_status(self, msg):
        base_msg = msg
        # Resolver el idioma AL MOMENTO y en cada tick del animation:
        # si el usuario cambia de idioma mientras trabaja, el mensaje
        # naranja cambia solo (antes se quedaba en el idioma inicial)
        self.status_label.configure(text=status_text(base_msg, getattr(self, 'english_mode', False)))
        self.lbl_wait.configure(text="")

        def animate_wait(dots=0):
            if not self.is_processing:
                self.lbl_wait.configure(text="")
                return
            ellipsis = "." * dots
            txt = status_text(base_msg, getattr(self, 'english_mode', False))
            self.lbl_wait.configure(text=txt + ellipsis)
            next_dots = (dots % 3) + 1
            self.after(300, lambda: animate_wait(next_dots))

        animate_wait()

    def _open_overlay(self, first_text="Organizando archivos", indeterminate=False):
        if self.overlay and self.overlay.winfo_exists():
            return
        self.overlay = tk.Toplevel(self)
        self.overlay.withdraw()
        self.overlay.configure(bg="#f0f4f8")
        self.overlay.title("Procesando")
        self.overlay.resizable(False, False)
        self.overlay.transient(self)
        self.overlay.grab_set()
        safe_icon(self.overlay)
        frm = ctk.CTkFrame(self.overlay, fg_color="#e8eef5", corner_radius=12)
        frm.pack(fill="both", expand=True, padx=15, pady=15)
        self.overlay_text = tk.Label(frm, text=first_text, font=("Segoe UI", 10, "bold"), fg="#1e3a5f", bg="#f0f4f8")
        self.overlay_text.pack(pady=(4, 10))
        mode = "indeterminate" if indeterminate else "determinate"
        self.marquee = ctk.CTkProgressBar(frm, mode=mode, progress_color="#3b82f6", fg_color="#e2e8f0")
        self.marquee.pack(fill="x")
        if indeterminate:
            self.marquee.start(20)
        center_window(self.overlay, None)
        self.overlay.deiconify()
        self.update_idletasks()

    def _update_overlay(self, msg, indeterminate=False):
        if self.overlay and self.overlay.winfo_exists():
            self.overlay_text.configure(text=msg)
            if self.marquee:
                new_mode = "indeterminate" if indeterminate else "determinate"
                if self.marquee.cget("mode") != new_mode:
                    if new_mode == "indeterminate":
                        self.marquee.stop()
                        self.marquee.configure(mode="indeterminate")
                        self.marquee.start(20)
                    else:
                        self.marquee.stop()
                        self.marquee.configure(mode="determinate")
            self.update_idletasks()

    def _close_overlay(self):
        if self.overlay and self.overlay.winfo_exists():
            if self.marquee:
                self.marquee.stop()
            self.overlay.destroy()
            self.overlay = None
            self.marquee = None

    def _reset_counters(self):
        self.total_analyzed = 0
        self.total_organized = 0
        self.total_dirs_created = 0
        self.start_time = None
        self._refresh_counters()
        self._clear_log()

    def _refresh_counters(self):
        elapsed = time.time() - self.start_time if self.start_time else 0
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        eng = getattr(self, 'english_mode', False)
        self.lbl_analyzed.configure(text=f"{'Total files organized:' if eng else 'Total de archivos organizados:'} {self.total_organized}")
        self.lbl_dirs.configure(text=f"{'Total folders created:' if eng else 'Total de carpetas creadas:'} {self.total_dirs_created}")
        self.lbl_time.configure(text=f"{'Elapsed time:' if eng else 'Tiempo transcurrido:'} {minutes}m {seconds}s")

    def _log(self, text):
        self.txt.configure(state="normal")
        self.txt.insert("end", text + "\n")
        self.txt.see("end")
        self.txt.configure(state="disabled")

    def _log_summary(self, text):
        self.txt.configure(state="normal")
        self.txt.insert("end", text)
        # Fijar el scroll al final: la última línea del log (fecha/hora final + cierre)
        # nunca debe quedar cortada en la vista
        self.txt.yview_moveto(1.0)
        self.txt.configure(state="disabled")

    def _clear_log(self):
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.configure(state="disabled")
        try:
            self.lbl_cf_name.configure(text="None" if getattr(self, 'english_mode', False) else "Ninguna")
        except Exception:
            pass

    def on_start(self):
        if not self.queue:
            self._show_modern_popup(("Agrega una carpeta a la cola para iniciar.",
                                     "Add a folder to the queue to start."))
            return

        # Determinar qué carpetas procesar: marcadas con ☑
        checked_folders = []
        if hasattr(self, '_tree_checked'):
            for iid, checked in self._tree_checked.items():
                if checked:
                    try:
                        folder = self.tree.item(iid)["values"][1]
                        if folder:
                            checked_folders.append(folder)
                    except Exception:
                        pass
        
        if not checked_folders:
            popup = tk.Toplevel(self)
            popup.withdraw()
            popup.configure(bg="#f0f4f8")
            eng_start = getattr(self, 'english_mode', False)
            popup.title("Selection required" if eng_start else "Selección requerida")
            popup.resizable(False, False)
            popup.transient(self)
            popup.grab_set()
            safe_icon(popup)
            frm = ctk.CTkFrame(popup, fg_color="#e8eef5", corner_radius=12)
            frm.pack(fill="both", expand=True, padx=15, pady=15)
            t_es = "Primero selecciona las carpetas que deseas organizar marcando el checkbox (☑)."
            t_en = "First select the folders you want to organize by checking the checkbox (☑)."
            lbl = tk.Label(frm, text=(t_en if eng_start else t_es), font=("Segoe UI", 10), justify="center", wraplength=280, fg="#1e3a5f", bg="#f0f4f8")
            lbl.pack(pady=(0, 16))
            b_es, b_en = "Entendido", "Got it"
            btn = ctk.CTkButton(frm, text=(b_en if eng_start else b_es), command=popup.destroy,
                          fg_color="#3b82f6", hover_color="#2563eb", text_color="white")
            btn.pack()
            self._register_live_popup(popup, "Selección requerida", "Selection required",
                                      [(lbl, t_es, t_en), (btn, b_es, b_en)])
            center_window(popup, self)
            popup.deiconify()
            return
            
        folders_to_process = checked_folders

        def _launch(folders):
            self._set_buttons_state(False)
            self._reset_counters()
            self.start_time = time.time()
            self.after(0, self._refresh_counters)
            self.is_processing = True
            self.after(0, lambda: self._set_status("Please wait" if getattr(self, 'english_mode', False) else "Por favor espere"))
            threading.Thread(target=self._process_all_folders, args=(folders,), daemon=True).start()

        def _show_mode_popup_then(callback):
            current_mode = self._get_mode_key()
            eng = getattr(self, 'english_mode', False)
            if current_mode == "medio_y_nombre" and not self.no_show_medio_tip:
                self._show_tip_with_action(
                    "",
                    "If the program does not find a date in any of the 3 options\n(media created, capture date or name), the file will not be moved\nto any subfolder and will remain in the root folder." if eng else
                    "Si el programa no encuentra fecha en ninguna de las 3 opciones\n(medio creado, fecha de captura o nombre), el archivo no se moverá\na ninguna subcarpeta y quedará en la carpeta raíz.",
                    flag_attr="no_show_medio_tip", on_continue=callback)
            elif current_mode == "creacion" and not self.no_show_creacion_tip:
                self._show_tip_with_action(
                    "Notice: organization by creation date" if eng else "Aviso: organización por fecha de creación",
                    "Files without a creation date will remain in the root folder." if eng else
                    "Los archivos que no tengan fecha de creación quedarán en la carpeta raiz.",
                    flag_attr="no_show_creacion_tip", on_continue=callback)
            elif current_mode == "nombre" and not self.no_show_name_tip:
                self._show_tip_with_action(
                    "Notice: organization by date in the name" if eng else "Aviso: organización por fecha en el nombre",
                    "If your files do not have a date in the name, they will not be moved.\nDetected formats: YYYYMMDD, DD-Mon-YYYY, DD_Mon_YYYY, DDMonYYYY, DDMMYYYY, etc." if eng else
                    "Si tus archivos no tienen fecha en el nombre, no se moverán.\nFormatos detectados: YYYYMMDD, DD-Mes-YYYY, DD_Mes_YYYY, DDMesYYYY, DDMMYYYY, etc.",
                    flag_attr="no_show_name_tip", on_continue=callback)
            elif current_mode == "modificacion" and not getattr(self, "no_show_modif_tip", False):
                self._show_tip_with_action(
                    "Notice: organization by modification date" if eng else "Aviso: organización por fecha de modificación",
                    "Files without a valid modification date will remain in the root folder." if eng else
                    "Los archivos que no tengan una fecha de modificación válida quedarán en la carpeta raíz.",
                    flag_attr="no_show_modif_tip", on_continue=callback)
            else:
                callback()

        _show_mode_popup_then(lambda: _launch(folders_to_process))

    def _show_tip_with_action(self, title, text, flag_attr, on_continue):
        tip = tk.Toplevel(self)
        tip.withdraw()
        tip.configure(bg="#f0f4f8")
        eng = getattr(self, 'english_mode', False)
        tip.title("Notice" if eng else "Aviso")
        safe_icon(tip)
        tip.resizable(False, False)
        tip.transient(self)
        tip.grab_set()
        frm = ctk.CTkFrame(tip, fg_color="#e8eef5", corner_radius=12)
        frm.pack(fill="both", expand=True, padx=15, pady=15)
        if title:
            tk.Label(frm, text=title, font=("Segoe UI", 10, "bold", "underline"), justify="left", fg="#1e3a5f", bg="#f0f4f8").pack(anchor="w", pady=(0,10))
        for line in text.split('\n'):
            if line.strip():
                tk.Label(frm, text=line, justify="left", font=("Segoe UI", 9), fg="#1e3a5f", bg="#f0f4f8").pack(anchor="w", pady=(2,0))
        # Solo mostrar checkbox "no volver a mostrar" si es un aviso de modo (no de reorganización)
        var = tk.BooleanVar(value=False)
        if not flag_attr.startswith("_dummy"):
            ctk.CTkCheckBox(frm, text="Don't show again" if eng else "No volver a mostrar", variable=var,
                            fg_color="#3b82f6", hover_color="#1d4ed8", text_color="#1e3a5f").pack(anchor="w", pady=(10,10))
        else:
            tk.Frame(frm, bg="#f0f4f8").pack(pady=5)
        btns = tk.Frame(frm, bg="#f0f4f8")
        btns.pack()
        def do_continue():
            if not flag_attr.startswith("_dummy"):
                setattr(self, flag_attr, var.get())
            tip.grab_release()
            tip.destroy()
            on_continue()
        def do_cancel():
            tip.grab_release()
            tip.destroy()
        ctk.CTkButton(btns, text="Continue" if eng else "Continuar", command=do_continue,
                      fg_color="#10b981", hover_color="#059669", text_color="white").pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Cancel" if eng else "Cancelar", command=do_cancel,
                      fg_color="#64748b", hover_color="#475569", text_color="white").pack(side="left", padx=6)
        center_window(tip, self)
        tip.deiconify()
    def _undo_folder(self, folder):
        """Deshace la organización de una carpeta: mueve archivos de subcarpetas a la raíz y elimina carpetas vacías."""
        self._undo_organization_for_folder(folder, show_message=False)
        # Eliminar carpetas vacías
        dirs_to_remove = []
        for root, dirs, files in os.walk(folder, topdown=False):
            if root == folder:
                continue
            dirs_to_remove.append(root)
        dirs_to_remove.sort(key=lambda x: len(x), reverse=True)
        for d in dirs_to_remove:
            try:
                if os.path.isdir(d) and not os.listdir(d):
                    os.rmdir(d)
                    self.created_dirs.discard(d)
            except Exception:
                pass


    def _process_all_folders(self, folders_to_process, reubicar_dupes=False):
        if WIN32_OK:
            pythoncom.CoInitialize()
        def constant_time_update():
            if self.is_processing:
                self.after(0, self._refresh_counters)
            self.timer_id = self.after(1000, constant_time_update)
        self.after(0, constant_time_update)
        summary_data = []
        try:
            for folder in folders_to_process:
                folder_norm = os.path.normcase(os.path.abspath(folder))
                folder_basename = os.path.basename(folder)
                self.after(0, lambda f=folder_basename: self.lbl_cf_name.configure(text=f))
                timestamp_start = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                self.after(0, lambda ts=timestamp_start, f=folder_basename, eng=getattr(self, 'english_mode', False): self._log(f"\n{'='*60}\n  {'Inicio:' if not eng else 'Start:'} {ts}  |  {f}\n{'='*60}"))
                # Auto-undo si la carpeta tiene subcarpetas año/mes (organización previa)
                if has_year_subdirs(folder):
                    self.after(0, lambda fn=folder_norm: self.tree.set(self.folder_indexes.get(fn, ""), "status", "Undoing..." if getattr(self, 'english_mode', False) else "Deshaciendo..."))
                    self.after(0, lambda f=folder_basename, e5=getattr(self, 'english_mode', False): self._log(f"{'Undoing previous organization in:' if e5 else 'Deshaciendo organización previa en:'} {f}"))
                    self._undo_folder(folder)
                    self.created_dirs.clear()
                    self.after(0, lambda fn=folder_norm: self.tree.set(self.folder_indexes.get(fn, ""), "status", "Waiting" if getattr(self, 'english_mode', False) else "En espera"))
                    self.after(0, lambda e6=getattr(self, 'english_mode', False): self._log("Starting organization from scratch..." if e6 else "Iniciando organización desde cero..."))
                self.after(0, lambda fn=folder_norm: self.tree.set(self.folder_indexes.get(fn, ""), "status", "Organizing..." if getattr(self, 'english_mode', False) else "Organizando..."))
                self.after(0, lambda: self.progress.set(0))
                self.after(0, lambda f=folder_basename, e7=getattr(self, 'english_mode', False): self._log(f"{'Organizing folder:' if e7 else 'Organizando carpeta:'} {f}"))
                self._organize_folder(folder)
                self.after(0, lambda fn=folder_norm: self.tree.set(self.folder_indexes.get(fn, ""), "status", "Organized" if getattr(self, 'english_mode', False) else "Organizado"))
                dirs_created = getattr(self, "_organize_dirs_created", 0)
                no_date = getattr(self, "_organize_no_date_count", 0)
                organized = getattr(self, "_organize_organized_count", 0)
                summary_data.append({"name": folder_basename, "dirs": dirs_created, "no_date": no_date, "organized": organized})
                def _update_cantidad_after_organize(f=folder, fn=folder_norm, dc=dirs_created, nd=no_date, oc=organized):
                    try:
                        e3 = getattr(self, 'english_mode', False)
                        cant = f"{oc} {'archivos organizados' if not e3 else 'files organized'} / {nd} {'sin fecha' if not e3 else 'without date'}"
                        self.tree.set(self.folder_indexes.get(fn, ""), "cantidad", cant)
                    except Exception:
                        pass
                self.after(0, _update_cantidad_after_organize)
                self.after(100, self._fit_folder)
                no_date_count = getattr(self, "_organize_no_date_count", 0)
                self.after(0, lambda n=no_date_count, eng=getattr(self, 'english_mode', False): self._log(
                    f"{'='*60}\n  {'FILES WITHOUT DETECTED DATE:' if eng else 'ARCHIVOS SIN FECHA DETECTADA:'} {n}"))
                timestamp_end = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                self.after(0, lambda ts=timestamp_end, f=folder_basename, eng=getattr(self, 'english_mode', False): self._log(f"{'='*60}\n  {'Fin:' if not eng else 'End:'} {ts}  |  {f}\n{'='*60}\n"))
                self.after(0, lambda: self.progress.set(1.0))
            # Resumen final
            if summary_data:
                eng_s = getattr(self, 'english_mode', False)
                total_no_date = sum(d["no_date"] for d in summary_data)
                total_dirs = sum(d["dirs"] for d in summary_data)
                total_organized = sum(d["organized"] for d in summary_data)
                lines = [f"{'='*60}"]
                lines.append(f"  {'Total de archivos organizados:' if not eng_s else 'Total files organized:'} {total_organized}")
                lines.append(f"  {'Total de archivos sin fecha detectable:' if not eng_s else 'Total files without date:'} {total_no_date}")
                lines.append(f"  {'Total de carpetas creadas:' if not eng_s else 'Total folders created:'} {total_dirs}")
                ts_final = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                lines.append(f"{'='*60}")
                lines.append(f"  {'Fecha/hora final:' if not eng_s else 'Final date/time:'} {ts_final}")
                lines.append(f"{'='*60}")
                self.after_idle(lambda txt="\n".join(lines): self._log_summary(txt))
        finally:
            if WIN32_OK:
                pythoncom.CoUninitialize()
            if hasattr(self, 'timer_id'):
                self.after_cancel(self.timer_id)
            self.after(0, self._refresh_counters)
            self.is_processing = False
            self.after(0, lambda: self.status_label.configure(text=""))
            self.after(0, lambda: self.lbl_wait.configure(text=""))
            self.after(0, lambda: self.progress.set(0))
            self.after(0, lambda: self._set_buttons_state(True))
            self.after(0, self._update_undo_button_state)
            self.after(0, self._show_completion_dialog)
    def _uncheck_all(self):
        if hasattr(self, '_tree_checked'):
            for iid in self._tree_checked:
                self._tree_checked[iid] = False
                self.tree.set(iid, "sel", "☐")
    def _show_completion_dialog(self):
        self._uncheck_all()
        popup = tk.Toplevel(self)
        popup.withdraw()
        popup.configure(bg="#f0f4f8")
        eng = getattr(self, 'english_mode', False)
        popup.title(APP_NAME)
        popup.resizable(False, False)
        popup.transient(self)
        safe_icon(popup)
        frm = ctk.CTkFrame(popup, fg_color="#e8eef5", corner_radius=12)
        frm.pack(fill="both", expand=True, padx=15, pady=15)
        t_es = "Proceso de organización finalizado."
        t_en = "Organization process completed."
        lbl = tk.Label(frm, text=(t_en if eng else t_es),
                     font=("Segoe UI", 12, "bold"), fg="#1e3a5f", justify="center", bg="#f0f4f8")
        lbl.pack(pady=(10, 16))
        ctk.CTkButton(frm, text="OK", command=popup.destroy,
                      fg_color="#10b981", hover_color="#059669", text_color="white").pack()
        self._register_live_popup(popup, APP_NAME, APP_NAME, [(lbl, t_es, t_en)])
        center_window(popup, self)
        popup.deiconify()

    def _show_restored_popup(self):
        popup = tk.Toplevel(self)
        popup.withdraw()
        popup.configure(bg="#f0f4f8")
        eng = getattr(self, 'english_mode', False)
        popup.title(APP_NAME)
        popup.resizable(False, False)
        popup.transient(self)
        safe_icon(popup)
        frm = ctk.CTkFrame(popup, fg_color="#e8eef5", corner_radius=12)
        frm.pack(fill="both", expand=True, padx=15, pady=15)
        t_es = "¡Todo ha sido restaurado exitosamente!"
        t_en = "All folders have been restored successfully!"
        lbl = tk.Label(frm, text=(t_en if eng else t_es),
                     font=("Segoe UI", 12, "bold"), fg="#1e3a5f", justify="center", bg="#f0f4f8")
        lbl.pack(pady=(10, 16))
        ctk.CTkButton(frm, text="OK", command=popup.destroy,
                      fg_color="#10b981", hover_color="#059669", text_color="white").pack()
        self._register_live_popup(popup, APP_NAME, APP_NAME, [(lbl, t_es, t_en)])
        center_window(popup, self)
        popup.deiconify()

    def _get_target_date(self, path, fname, mode):
        cur_year = datetime.now().year
        ext = os.path.splitext(fname)[1].lower()

        def valid(dt):
            return dt and 1900 <= dt.year <= cur_year

        def from_ctime():
            try:
                dt = datetime.fromtimestamp(os.path.getctime(path))
                return dt if valid(dt) else None
            except: return None

        def from_mtime():
            try:
                dt = datetime.fromtimestamp(os.path.getmtime(path))
                return dt if valid(dt) else None
            except: return None

        def from_name():
            dt = extract_date_from_filename(fname)
            return dt if valid(dt) else None

        def from_exif_pil():
            """Lee EXIF directamente con PIL, solo para imágenes (rápido, sin COM)."""
            PIL_EXIF_EXTS = {'.jpg', '.jpeg', '.tiff', '.tif', '.heic', '.heif'}
            if not (PIL_OK and ext in PIL_EXIF_EXTS):
                return None
            try:
                from PIL import Image as _Img
                with _Img.open(path) as _img:
                    exif_data = _img._getexif()
                if exif_data:
                    for tag in [36867, 36868, 306]:
                        val = exif_data.get(tag)
                        if val:
                            try:
                                dt = datetime.strptime(str(val)[:19], "%Y:%m:%d %H:%M:%S")
                                if valid(dt): return dt
                            except Exception:
                                pass
            except Exception:
                pass
            return None

        if mode == "creacion":
            return from_ctime()

        if mode == "modificacion":
            return from_mtime()

        if mode == "nombre":
            return from_name()

        if mode == "medio_y_nombre":
            # En vez de mantener una lista cerrada de extensiones "de video"
            # (que siempre se queda corta: .MOD, .MTS, formatos de cámaras
            # específicas, etc.), se trata como imagen SOLO lo que tiene
            # extensión de imagen conocida. Todo lo demás (cualquier formato
            # de video, sea cual sea su extensión) pasa por lectura binaria.
            IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
                          '.heic', '.heif', '.webp', '.raw', '.cr2', '.nef', '.arw'}

            if ext not in IMAGE_EXTS:
                # Posible video (cualquier extensión: mp4, mov, avi, mkv, mod,
                # mts, wmv, flv, etc.): lectura binaria directa primero
                # (rápida, sin COM, sin depender de hilos ni de qué columnas
                # expone Windows para esa extensión específica).
                dt = _read_file_creation_date(path)
                if dt and valid(dt):
                    return dt
                # Si el contenedor no trae fecha embebida, intentar por nombre
                dt = from_name()
                if dt:
                    return dt
                # Último respaldo: Shell de Windows (por si el binario no la trae
                # pero Windows sí la conoce por otra vía, ej. metadata de carpeta)
                if WIN32_OK:
                    date_str = _get_property_legacy(path, "Medio creado")
                    if date_str:
                        try:
                            parts = date_str.split(' ')
                            d = datetime.strptime(parts[0], "%d/%m/%Y")
                            if valid(d):
                                return d
                        except Exception:
                            pass
                return None

            # Para imágenes: EXIF (PIL) → Property Store/Shell → Nombre
            dt = None
            if not dt:
                dt = from_exif_pil()
            if not dt and WIN32_OK:
                d = _get_media_date_pkey(path)
                if d and valid(d):
                    dt = d
                if not dt:
                    props = _get_props_direct(path, ["Fecha de captura", "Medio creado"])
                    if props:
                        for nombre in ("Fecha de captura", "Medio creado"):
                            val = props.get(nombre)
                            if not val:
                                continue
                            for fmt in ("%d/%m/%Y", "%Y/%m/%d", "%Y-%m-%d", "%Y:%m:%d"):
                                try:
                                    d = datetime.strptime(str(val).strip()[:10], fmt)
                                    if valid(d):
                                        break
                                except Exception:
                                    d = None
                            if not d:
                                m = re.search(r'(\d{4})', str(val))
                                if m:
                                    d = _valid_date(int(m.group(1)), 1, 1)
                            if d and valid(d):
                                dt = d
                                break
            if not dt:
                dt = from_name()
            if dt:
                return dt

        return None

    def _organize_folder(self, folder):
        mode = self._get_mode_key()
        file_list = list(iter_all_files_including_organized(folder))
        total_files = len(file_list)
        self.processed_roots.add(folder)
        self.after(0, lambda: self.progress.set(0))
        processed = 0
        self._organize_no_date_count = 0   # archivos sin fecha detectada en esta carpeta
        self._organize_dirs_created = 0    # carpetas creadas en esta carpeta
        self._organize_organized_count = 0 # archivos organizados en esta carpeta
        for path in file_list:
            processed += 1
            self.total_analyzed += 1
            fname = os.path.basename(path)
            dt = self._get_target_date(path, fname, mode)
            if not dt:
                self._organize_no_date_count += 1
                self.after(0, lambda n=fname, e8=getattr(self, 'english_mode', False): self._log(f"{'No date detected:' if e8 else 'Sin fecha detectada:'} {n} {'— skipped.' if e8 else '— se omite.'}"))
                continue
            year_dir = os.path.join(folder, str(dt.year))
            eng = getattr(self, 'english_mode', False)
            if getattr(self, "var_no_month_num", None) and self.var_no_month_num.get():
                month_dir = os.path.join(year_dir, readable_month(dt.month, eng))
            else:
                month_dir = os.path.join(year_dir, f"{dt.month} {readable_month(dt.month, eng)}")
            os.makedirs(year_dir, exist_ok=True)
            if year_dir not in self.created_dirs:
                self.created_dirs.add(year_dir)
                self.total_dirs_created += 1
                self._organize_dirs_created += 1
            os.makedirs(month_dir, exist_ok=True)
            if month_dir not in self.created_dirs:
                self.created_dirs.add(month_dir)
                self.total_dirs_created += 1
                self._organize_dirs_created += 1
            target = self._dedupe_name(os.path.join(month_dir, fname))
            self.moved_ops.append((target, path))
            shutil.move(path, target)
            self._organize_organized_count += 1
            self.total_organized += 1
            if processed % 50 == 0:
                eng = getattr(self, 'english_mode', False)
                self.after(0, lambda n=fname, y=dt.year, m=readable_month(dt.month, eng), e9=eng: self._log(
                    f"{'Moved:' if e9 else 'Movido:'} {n} \u2192 {y}/{m}"))
            if processed % max(1, total_files // 20) == 0 or processed == total_files:
                self.after(0, lambda v=int(processed/max(1,total_files)*100): self.progress.set(v/100))
        self.after(0, lambda: self.progress.set(1.0))
    def _dedupe_name(self, path):
        base, ext = os.path.splitext(path)
        i = 1
        while os.path.exists(path):
            path = f"{base} ({i}){ext}"
            i += 1
        return path

    def on_undo(self):
        eng_undo = getattr(self, 'english_mode', False)
        if not self.queue:
            self._show_modern_popup(("No hay carpetas cargadas para deshacer. Agrega una carpeta primero.",
                                     "There are no folders loaded to undo. Add a folder first."))
            return
        # Solo afectar carpetas marcadas con ☑
        checked_folders = []
        if hasattr(self, '_tree_checked'):
            for iid, checked in self._tree_checked.items():
                if checked:
                    try:
                        folder = self.tree.item(iid)["values"][1]
                        if folder:
                            checked_folders.append(folder)
                    except Exception:
                        pass
        if not checked_folders:
            # Ninguna marcada: mostrar aviso y no hacer nada
            popup = tk.Toplevel(self)
            popup.withdraw()
            popup.configure(bg="#f0f4f8")
            eng_undo = getattr(self, 'english_mode', False)
            popup.title("Selection required" if eng_undo else "Selección requerida")
            popup.resizable(False, False)
            popup.transient(self)
            popup.grab_set()
            safe_icon(popup)
            frm = ctk.CTkFrame(popup, fg_color="#e8eef5", corner_radius=12)
            frm.pack(fill="both", expand=True, padx=15, pady=15)
            t_es = "Primero selecciona las carpetas que deseas desorganizar marcando el checkbox (☑)."
            t_en = "First select the folders you want to undo by checking the checkbox (☑)."
            lbl = tk.Label(frm, text=(t_en if eng_undo else t_es),
                     font=("Segoe UI", 10), justify="center", wraplength=280, fg="#1e3a5f", bg="#f0f4f8")
            lbl.pack(pady=(0, 16))
            b_es, b_en = "Entendido", "Got it"
            btn = ctk.CTkButton(frm, text=(b_en if eng_undo else b_es), command=popup.destroy,
                          fg_color="#3b82f6", hover_color="#2563eb", text_color="white")
            btn.pack()
            self._register_live_popup(popup, "Selección requerida", "Selection required",
                                      [(lbl, t_es, t_en), (btn, b_es, b_en)])
            center_window(popup, self)
            popup.deiconify()
            return
        target_folders = checked_folders
        n = len(target_folders)
        names = "\n".join(f"  • {os.path.basename(f)}" for f in target_folders)
        msg_undo_es = (f"Se deshará la organización de {n} carpeta(s) seleccionada(s):\n{names}\n\n"
                       "Todos los archivos se moverán a su carpeta raíz y se eliminarán las carpetas vacías.")
        msg_undo_en = (f"The organization of {n} folder(s) will be undone:\n{names}\n\n"
                       "All files will be moved back to their root folder and empty folders will be removed.")
        confirm = self._show_confirm_dialog(msg=(msg_undo_es, msg_undo_en))
        if confirm == "cancel":
            return
        self._set_buttons_state(False)
        self.is_processing = True
        self._reset_counters()
        self.start_time = time.time()
        self.carpetas_procesadas_deshacer = 0
        self.total_carpetas_deshacer = len(target_folders)
        self.after(0, lambda: self._set_status("Undoing organization..." if getattr(self, 'english_mode', False) else "Deshaciendo organización..."))
        self.after(0, lambda: self.progress.set(0))
        threading.Thread(target=self._execute_undo_multiple_folders, args=(target_folders,), daemon=True).start()

    def _execute_undo_multiple_folders(self, folders_to_undo):
        if WIN32_OK:
            pythoncom.CoInitialize()
        def constant_time_update():
            if self.is_processing:
                self.after(0, self._refresh_counters)
            self.timer_id = self.after(1000, constant_time_update)

        self.after(0, constant_time_update)
        try:
            total_folders = len(folders_to_undo)
            for i, folder in enumerate(folders_to_undo):
                self.carpetas_procesadas_deshacer = i + 1
                folder_norm = os.path.normcase(os.path.abspath(folder))
                self.after(0, lambda f=os.path.basename(folder): self.lbl_cf_name.configure(text=f))
                self.after(0, lambda fn=folder_norm, e2=getattr(self, 'english_mode', False): self.tree.set(self.folder_indexes.get(fn, ""), "status", "Undoing..." if e2 else "Deshaciendo..."))
                self.after(0, lambda: self.progress.set(int((i+1) / total_folders * 80)/100))
                self._undo_organization_for_folder(folder, show_message=False)
                def _update_status_after_undo(f=folder, fn=folder_norm):
                    try:
                        fcount, fsub = count_folder_contents(f)
                        e3 = getattr(self, 'english_mode', False)
                        cant = f"{fsub} {'carpetas' if not e3 else 'folders'} / {fcount} {'Archivos en total' if not e3 else 'Total files'}" if (fcount > 0 or fsub > 0) else ("Carpeta Vacía" if not e3 else "Empty Folder")
                        self.tree.set(self.folder_indexes.get(fn, ""), "cantidad", cant)
                        self.tree.set(self.folder_indexes.get(fn, ""), "status", "Sin organizar" if not e3 else "Unorganized")
                    except Exception:
                        e3 = getattr(self, 'english_mode', False)
                        self.tree.set(self.folder_indexes.get(fn, ""), "status", "Sin organizar" if not e3 else "Unorganized")
                self.after(0, _update_status_after_undo)
                self.after(100, self._fit_folder)
            self.after(0, lambda: self.progress.set(0.9))
            other_dirs_to_remove = list(self.created_dirs)
            other_dirs_to_remove.sort(key=lambda x: (len(x), x), reverse=True)
            other_dirs_removed = 0
            for i, d in enumerate(other_dirs_to_remove):
                try:
                    if os.path.isdir(d) and not os.listdir(d):
                        os.rmdir(d)
                        other_dirs_removed += 1
                        self.created_dirs.discard(d)
                        if (i+1) % 50 == 0 or i == len(other_dirs_to_remove) - 1:
                            progress = 90 + int((i+1) / max(1, len(other_dirs_to_remove)) * 10)
                            self.after(0, lambda v=progress: self.progress.set(v/100))
                except Exception:
                    pass
            self.moved_ops.clear()
            self.processed_roots.clear()
            self.created_dirs.clear()
        finally:
            if WIN32_OK:
                pythoncom.CoUninitialize()
            if hasattr(self, 'timer_id'):
                self.after_cancel(self.timer_id)
            self.after(0, self._refresh_counters)
            self.after(0, lambda: self.progress.set(1.0))
            self.is_processing = False
            self.after(0, lambda: self.status_label.configure(text=""))
            self.after(0, lambda: self.lbl_wait.configure(text=""))
            self.after(0, lambda: self.progress.set(0))
            self.after(0, lambda: self._set_buttons_state(True))
            self.after(0, self._update_undo_button_state)
            self.after(0, self._uncheck_all)
            self.after(0, self._show_restored_popup)

    def _execute_undo(self, ops_to_undo):
        def constant_time_update_undo():
            if self.is_processing:
                self.after(0, self._refresh_counters)
            self.timer_id_undo = self.after(1000, constant_time_update_undo)

        self.after(0, self._reset_counters)
        self.start_time = time.time()
        self.after(0, constant_time_update_undo)
        self.is_processing = True
        self.after(0, lambda: self._set_status("Please wait" if getattr(self, 'english_mode', False) else "Por favor espere"))
        self.after(0, lambda: self.progress.set(0))
        try:
            eng_r = getattr(self, 'english_mode', False)
            self.after(0, lambda e10=eng_r: self._log("Restoring files..." if e10 else "Restaurando archivos..."))
            for i, (new_path, old_path) in enumerate(reversed(ops_to_undo)):
                try:
                    if os.path.exists(new_path):
                        os.makedirs(os.path.dirname(old_path), exist_ok=True)
                        shutil.move(new_path, old_path)
                        if (i+1) % 50 == 0 or i == len(ops_to_undo) - 1:
                            progress = int((i+1) / max(1, len(ops_to_undo)) * 60)
                            self.after(0, lambda v=progress: self.progress.set(v/100))
                except Exception as e:
                    self.after(0, lambda n=os.path.basename(new_path), err=e, e11=getattr(self, 'english_mode', False): self._log(
                        f"{'Error restoring' if e11 else 'Error restaurando'} {n}: {err}"))
            self.after(0, lambda n=len(ops_to_undo), e12=getattr(self, 'english_mode', False): self._log(
                f"{'Restoration of' if e12 else 'Restauración de'} {n} {'files completed.' if e12 else 'archivos completada.'}"))

            self.after(0, lambda: self.progress.set(0.7))
            self.after(0, lambda: self.progress.set(0.8))
            other_dirs_to_remove = list(self.created_dirs)
            other_dirs_to_remove.sort(key=lambda x: (len(x), x), reverse=True)
            other_dirs_removed = 0
            for i, d in enumerate(other_dirs_to_remove):
                try:
                    if os.path.isdir(d) and not os.listdir(d):
                        os.rmdir(d)
                        other_dirs_removed += 1
                        self.created_dirs.discard(d)
                        if (i+1) % 50 == 0 or i == len(other_dirs_to_remove) - 1:
                            progress = 80 + int((i+1) / max(1, len(other_dirs_to_remove)) * 20)
                            self.after(0, lambda v=progress: self.progress.set(v/100))
                except Exception:
                    pass
            self.moved_ops.clear()
            self.processed_roots.clear()
            self.created_dirs.clear()
            for f in self.queue:
                self.after(0, lambda root=f, e4=getattr(self, 'english_mode', False): self.tree.set(self.folder_indexes.get(root, ""), "status", "Sin organizar" if not e4 else "Unorganized"))
        finally:
            if hasattr(self, 'timer_id_undo'):
                self.after_cancel(self.timer_id_undo)
            self.after(0, self._refresh_counters)
            self.after(0, lambda: self.progress.set(1.0))
            self.is_processing = False
            self.after(0, lambda: self.status_label.configure(text=""))
            self.after(0, lambda: self.lbl_wait.configure(text=""))
            self.after(0, lambda: self.progress.set(0))
            self.after(0, lambda: self._set_buttons_state(True))
            self.after(0, self._update_undo_button_state)
            self.after(0, self._uncheck_all)
            self.after(0, self._show_restored_popup)

    def _show_confirm_dialog(self, msg=None):
        popup = tk.Toplevel(self)
        popup.withdraw()
        popup.configure(bg="#f0f4f8")
        popup.title("Confirm undo" if getattr(self, 'english_mode', False) else "Confirmar deshacer")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
        safe_icon(popup)
        eng = getattr(self, 'english_mode', False)
        frm = ctk.CTkFrame(popup, fg_color="#e8eef5", corner_radius=12)
        frm.pack(fill="both", expand=True, padx=15, pady=15)
        if msg is None:
            msg = ("Se moverán todos los archivos de las subcarpetas de vuelta "
                   "a su carpeta raíz y se eliminarán las carpetas vacías.\n\n"
                   "Esto te permitirá reorganizarlas con otro modo de organización.",
                   "All files in subfolders will be moved back\nto their root folder and empty folders will be removed.\n\n"
                   "This will let you reorganize them with another mode.")
        if isinstance(msg, tuple):
            msg_es, msg_en = msg
        else:
            msg_es = msg_en = msg
        lbl = tk.Label(frm, text=(msg_en if eng else msg_es), font=("Segoe UI", 10), justify="center",
                     wraplength=380, fg="#1e3a5f", bg="#f0f4f8")
        lbl.pack(pady=(10, 20))
        result = tk.StringVar(value="cancel")

        def cont():
            result.set("undo")
            popup.destroy()

        btns = tk.Frame(frm, bg="#f0f4f8")
        btns.pack()
        c_es, c_en = "Continuar", "Continue"
        x_es, x_en = "Cancelar", "Cancel"
        btn_cont = ctk.CTkButton(btns, text=(c_en if eng else c_es), command=cont,
                      fg_color="#10b981", hover_color="#059669", text_color="white")
        btn_cont.pack(side="left", padx=6)
        btn_cancel = ctk.CTkButton(btns, text=(x_en if eng else x_es), command=popup.destroy,
                      fg_color="#ef4444", hover_color="#dc2626", text_color="white")
        btn_cancel.pack(side="left", padx=6)
        self._register_live_popup(popup, "Confirmar deshacer", "Confirm undo",
                                  [(lbl, msg_es, msg_en), (btn_cont, c_es, c_en), (btn_cancel, x_es, x_en)])
        center_window(popup, self)
        popup.deiconify()
        self.wait_window(popup)
        return result.get()

    def _confirm_close(self):
        """Pregunta antes de cerrar el programa para evitar cierres accidentales."""
        popup = tk.Toplevel(self)
        popup.withdraw()
        popup.configure(bg="#f0f4f8")
        eng = getattr(self, 'english_mode', False)
        popup.title("Confirmar cierre" if not eng else "Confirm close")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
        safe_icon(popup)
        frm = ctk.CTkFrame(popup, fg_color="#e8eef5", corner_radius=12)
        frm.pack(fill="both", expand=True, padx=15, pady=15)
        t_es = "¿Deseas cerrar el programa?"
        t_en = "Do you want to close the program?"
        lbl = tk.Label(frm, text=(t_en if eng else t_es), font=("Segoe UI", 11, "bold"),
                       justify="center", wraplength=320, fg="#1e3a5f", bg="#f0f4f8")
        lbl.pack(pady=(14, 18))
        result = tk.StringVar(value="no")

        def yes():
            result.set("yes")
            popup.destroy()

        btns = tk.Frame(frm, bg="#f0f4f8")
        btns.pack()
        s_es, s_en = "Sí, cerrar", "Yes, close"
        c_es, c_en = "Cancelar", "Cancel"
        btn_yes = ctk.CTkButton(btns, text=(s_en if eng else s_es), command=yes,
                                fg_color="#ef4444", hover_color="#dc2626", text_color="white")
        btn_yes.pack(side="left", padx=6)
        btn_no = ctk.CTkButton(btns, text=(c_en if eng else c_es), command=popup.destroy,
                               fg_color="#64748b", hover_color="#475569", text_color="white")
        btn_no.pack(side="left", padx=6)
        self._register_live_popup(popup, "Confirmar cierre", "Confirm close",
                                  [(lbl, t_es, t_en), (btn_yes, s_es, s_en), (btn_no, c_es, c_en)])
        center_window(popup, self)
        popup.deiconify()
        self.wait_window(popup)
        return result.get() == "yes"

    def on_close(self):
        if not self._confirm_close():
            return
        self._close_aux_windows()
        self._close_overlay()
        self.destroy()

def undo_organization_simple(folder_path):
    try:
        entries = list(os.scandir(folder_path))
        for entry in entries:
            if entry.is_dir():
                dir_name = entry.name
                if dir_name.isdigit() and len(dir_name) == 4 and 1900 <= int(dir_name) <= 2100:
                    year_path = os.path.join(folder_path, dir_name)
                    try:
                        month_entries = list(os.scandir(year_path))
                        for month_entry in month_entries:
                            if month_entry.is_dir():
                                month_path = os.path.join(year_path, month_entry.name)
                                for file_path in iter_all_files(month_path):
                                    file_name = os.path.basename(file_path)
                                    target_path = os.path.join(folder_path, file_name)
                                    target_path = _dedupe_name_static(target_path)
                                    shutil.move(file_path, target_path)
                                try:
                                    if not list(os.scandir(month_path)):
                                        os.rmdir(month_path)
                                except:
                                    pass
                        try:
                            if not list(os.scandir(year_path)):
                                os.rmdir(year_path)
                        except:
                            pass
                    except Exception:
                        pass
        return True
    except Exception:
        return False

if __name__ == '__main__':
    if not PIL_OK:
        messagebox.showerror("Error", "Falta la librería 'Pillow'. Instálala con 'pip install Pillow'.")
        sys.exit(1)
    if not WIN32_OK and sys.platform == 'win32':
        messagebox.showwarning("Advertencia", "Falta la librería 'pywin32'. Instálala con 'pip install pywin32'. Las opciones de ordenamiento por 'Medio creado/Fecha de captura' no funcionarán.")
    try:
        app = Click2FoldersApp()
        app.mainloop()
    except Exception as e:
        import traceback
        messagebox.showerror("Error", f"Error al iniciar:\n{traceback.format_exc()}")

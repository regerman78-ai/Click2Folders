# -- coding: utf-8 --
"""
Click2Folders - Organizador automático de fotos y videos
Versión: v1.8.49
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
from tkinter import ttk, filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor

# Variables de la aplicación
APP_NAME = "Click2Folders"
APP_VERSION = "v1.8.49"
WINDOW_TITLE = f"Click2Folders - Organizador Automático de Fotos y Videos {APP_VERSION}"
ICON_FILE = "favicon.ico"
base_path = getattr(sys, '_MEIPASS', os.getcwd())

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
    win.update_idletasks()
    if parent is None:
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw - win.winfo_width()) // 2
        y = (sh - win.winfo_height()) // 2
    else:
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw - win.winfo_width()) // 2
        y = py + (ph - win.winfo_height()) // 2
    win.geometry(f"+{x}+{y}")

def safe_icon(win, icon_path=ICON_FILE):
    icon_full_path = os.path.join(base_path, icon_path)
    try:
        win.iconbitmap(default=icon_full_path)
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
    lock_file = os.path.join(tempfile.gettempdir(), ".click2folders.lock")
    if os.path.exists(lock_file):
        os.remove(lock_file)
    with open(lock_file, "w") as f:
        f.write(str(os.getpid()))
    return True

def _get_launch_count():
    """Lee y actualiza el contador de lanzamientos para mostrar donaciones cada 5 aperturas."""
    count_file = os.path.join(tempfile.gettempdir(), ".click2folders_launch_count.dat")
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
        self.title(WINDOW_TITLE)
        self.minsize(900, 600)
        # Tema neutro: dejar que ttk use el tema del sistema
        # Usar tema nativo de Windows para evitar parches de color
        _style = ttk.Style()
        try:
            _style.theme_use("winnative")
        except Exception:
            pass
        _style.configure("TCombobox", fieldbackground="white", background="white")
        _style.map("TCombobox", fieldbackground=[("readonly", "white")])
        safe_icon(self)
        self.withdraw()              # Ocultar temporalmente
        
        # Configurar tamaño y centrar
        self.geometry("900x600")     # Establecer tamaño
        self.update_idletasks()
        center_window(self)          # Centrar correctamente
        self.deiconify()
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
        self.total_dirs_created = 0
        self.start_time = None
        self.processed_roots = set()
        self.carpetas_procesadas_deshacer = 0
        self.total_carpetas_deshacer = 0
        self.tutorial_win = OneShotWindow()
        self.limits_win = OneShotWindow()
        self.support_win = OneShotWindow()
        self.donate_win = OneShotWindow()
        self.toolbar = None
        self.is_processing = False
        self.english_mode = False
        self.btn_add_folder = None
        self.btn_start = None
        self.btn_undo = None
        self.btn_remove = None
        self._build_toolbar()
        self._build_options()
        self._build_queue_area()
        self._build_progress_bar()
        self._build_log_area()
        self._build_counters_bar()
        self.overlay = None
        self.overlay_text = None
        self.marquee = None
        self._update_undo_button_state()
        self.deiconify()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        # Mostrar donaciones cada 5 lanzamientos
        self.after(500, self._check_launch_donation)

    # [Métodos restantes idénticos... se mantienen todos los métodos UI y organización sin cambios]

    def _build_toolbar(self):
        if self.toolbar:
            self.toolbar.destroy()
        self.toolbar = ttk.Frame(self, padding=(8, 8, 8, 0))
        self.toolbar.pack(fill="x")
        eng = getattr(self, 'english_mode', False)
        self.btn_tutorial = ttk.Button(self.toolbar, text="Tutorial", command=self.on_tutorial)
        self.btn_tutorial.pack(side="left", padx=(0,6))
        self.btn_support = ttk.Button(self.toolbar, text="Support" if eng else "Soporte", command=self.on_support)
        self.btn_support.pack(side="left", padx=6)
        self.btn_donate = ttk.Button(self.toolbar, text="Donations" if eng else "Donaciones", command=self.on_donate)
        self.btn_donate.pack(side="left", padx=6)
        self.btn_lang = ttk.Button(self.toolbar, text="Spanish Style" if eng else "Modo Ingles", command=self._toggle_lang)
        self.btn_lang.pack(side="left", padx=6)
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
            tk.Label(tip, text=txt, background="#ffffcc",
                     relief="solid", borderwidth=1, font=("Segoe UI", 9), padx=6, pady=4, justify="left").pack()
            self._lang_tooltip = tip
        def _hide_lang_tip(e):
            if self._lang_tooltip:
                self._lang_tooltip.destroy()
                self._lang_tooltip = None
        self.btn_lang.bind("<Enter>", _show_lang_tip)
        self.btn_lang.bind("<Leave>", _hide_lang_tip)
        
        # self.lbl_version = ttk.Label(self.toolbar, text="Versión Premium", 
        #                              font=("Segoe UI", 10, "bold"), foreground="red")
        # self.lbl_version.pack(side="right")

    def _toggle_lang(self):
        self.english_mode = not self.english_mode
        # Actualizar título de la ventana principal
        eng = self.english_mode
        self.title(f"Click2Folders - Automatic Photo & Video Organizer {APP_VERSION}" if eng else WINDOW_TITLE)
        self.btn_support.config(text="Support" if eng else "Soporte")
        self.btn_donate.config(text="Donations" if eng else "Donaciones")
        self.btn_lang.config(text="Spanish Style" if eng else "Modo Ingles")
        # Actualizar botones de la cola
        self.btn_add_folder.config(text="Add folder" if eng else "Agregar carpeta")
        self.btn_add_multiple.config(text="Add multiple folders" if eng else "Agregar varias carpetas")
        self.btn_start.config(text="Organize" if eng else "Organizar")
        self.btn_undo.config(text="Undo organization" if eng else "Deshacer organización")
        # Actualizar encabezados del árbol
        self.tree.heading("folder", text="Folder" if eng else "Carpeta")
        self.tree.heading("status", text="Status" if eng else "Estado")
        # Actualizar botones adicionales
        self.btn_remove.config(text="Remove folders" if eng else "Quitar Carpetas")
        self.btn_sel_all.config(text="Select all" if eng else "Seleccionar todo")
        self.btn_desel_all.config(text="Deselect all" if eng else "Deseleccionar todo")
        self.lbl_cf_prefix.config(text="Organizing folder: " if eng else "Organizando Carpeta: ")
        if self.lbl_cf_name:
            self.lbl_cf_name.config(text="None" if eng else "Ninguna")
        # Actualizar contadores
        self.lbl_analyzed.configure(text=f"{'Files analyzed:' if eng else 'Archivos analizados:'} {self.total_analyzed}")
        self.lbl_dirs.configure(text=f"{'Folders created:' if eng else 'Carpetas creadas:'} {self.total_dirs_created}")
        self.lbl_time.configure(text=f"{'Elapsed time:' if eng else 'Tiempo transcurrido:'} 0m 0s")
        # Actualizar combo de modos
        self._rebuild_options_lang()
        # Actualizar tooltip
        if self._lang_tooltip:
            self._lang_tooltip.destroy()
            self._lang_tooltip = None
        # Actualizar textos de estado del árbol
        for iid in self.tree.get_children():
            values = self.tree.item(iid, "values")
            if len(values) >= 3:
                current_status = values[2]
                new_status = self._translate_status(current_status, eng)
                if new_status != current_status:
                    self.tree.set(iid, "status", new_status)

    def _translate_status(self, current_status, to_english):
        if to_english:
            m = re.match(r'^(\d+)\s+archivos para organizar$', current_status)
            if m:
                return f"{m.group(1)} files to organize"
            mapping = {
                "Organizado ✓": "Organized ✓",
                "Organizando...": "Organizing...",
                "En espera": "Waiting",
                "Deshaciendo...": "Undoing...",
                "Deshecho": "Undone",
                "Desorganizada": "Unorganized",
            }
        else:
            m = re.match(r'^(\d+)\s+files to organize$', current_status)
            if m:
                return f"{m.group(1)} archivos para organizar"
            mapping = {
                "Organized ✓": "Organizado ✓",
                "Organizing...": "Organizando...",
                "Waiting": "En espera",
                "Undoing...": "Deshaciendo...",
                "Undone": "Deshecho",
                "Unorganized": "Desorganizada",
            }
        return mapping.get(current_status, current_status)

    def _rebuild_options_lang(self):
        """Reconstruye los textos del área de opciones según el idioma actual."""
        eng = getattr(self, 'english_mode', False)
        # Actualizar label de modo
        self._mode_label.config(text="Organization mode:" if eng else "Modo de organización:")
        # Actualizar checkbox "No anteponer número"
        self._cb_no_num.config(text="Do not prepend month number in subfolders" if eng else "No anteponer número de mes en subcarpetas")
        # Cambiar valores del combo de modos
        modes_dict = self.MODES_EN if eng else self.MODES
        current_key = self._get_mode_key()
        new_values = list(modes_dict.values())
        self.mode_combo["values"] = new_values
        # Mantener la misma clave seleccionada
        self.mode_var.set(modes_dict[current_key])

    def _build_options(self):
        box = tk.Frame(self, bg=self.cget("bg"), padx=8, pady=4)
        box.pack(fill="x")
        options_frame = tk.Frame(box, bg=self.cget("bg"))
        options_frame.pack(fill="x", pady=4)
        self.mode_enabled_var = tk.BooleanVar(value=True)
        modes_init = self.MODES_EN if getattr(self, 'english_mode', False) else self.MODES
        self.mode_var = tk.StringVar(value=modes_init["medio_y_nombre"])
        eng = getattr(self, 'english_mode', False)
        self._mode_label = ttk.Label(options_frame, text="Organization mode:" if eng else "Modo de organización:", font=("Segoe UI", 10))
        self._mode_label.pack(side="left", padx=(0, 8))
        self.mode_combo = ttk.Combobox(
            options_frame, textvariable=self.mode_var,
            values=list(modes_init.values()), state="readonly", width=47)
        self.mode_combo.pack(side="left", padx=(0, 10))

        self.var_dupes = tk.BooleanVar(value=False)
        self.var_reubicar = tk.BooleanVar(value=False)
        self.var_no_month_num = tk.BooleanVar(value=False)
        self._cb_no_num = tk.Checkbutton(options_frame, text="No anteponer número de mes en subcarpetas",
                                             variable=self.var_no_month_num,
                                             bg=self.cget("bg"), activebackground=self.cget("bg"),
                                             selectcolor="white")
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
            tk.Label(tip, text=tip_txt, background="#ffffcc",
                     relief="solid", borderwidth=1, font=("Segoe UI", 9), padx=6, pady=4, justify="left").pack()
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
        frame = ttk.Frame(self, padding=(8, 2, 8, 6))
        frame.pack(fill="both", expand=False)

        # Botones Seleccionar/Deseleccionar ENCIMA del tree
        sel_top_bar = ttk.Frame(frame)
        sel_top_bar.pack(fill="x", pady=(0, 3), anchor="w")

        body = ttk.Frame(frame)
        body.pack(fill="both", expand=True)

        # Estilo Treeview: gris oscuro permanente en encabezado + cuadrícula
        style = ttk.Style()
        style.configure("Treeview.Heading",
                        background="#909090",
                        foreground="white",
                        relief="raised",
                        font=("Segoe UI", 9, "bold"))
        style.map("Treeview.Heading",
                  background=[("active", "#707070"), ("!active", "#909090")],
                  foreground=[("active", "white"), ("!active", "white")])
        style.configure("Treeview",
                        background="#FFFFFF",
                        fieldbackground="#FFFFFF",
                        rowheight=22,
                        borderwidth=1,
                        relief="solid")
        style.layout("Treeview", [
            ("Treeview.treearea", {"sticky": "nswe"})
        ])

        self.tree = ttk.Treeview(body, height=6, columns=("sel", "folder", "status"), show="headings")
        self.tree.column("sel", width=28, minwidth=28, stretch=False, anchor="center")
        self.tree.column("folder", width=480, minwidth=200, stretch=True, anchor="w")
        self.tree.column("status", width=180, minwidth=140, stretch=False, anchor="center")
        self.tree.heading("sel", text="Sel.")
        self.tree.heading("folder", text="Folder" if self.english_mode else "Carpeta")
        self.tree.heading("status", text="Status" if self.english_mode else "Estado")
        scroll = tk.Scrollbar(body, command=self.tree.yview, width=22)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        # Líneas divisorias alternando color de fila
        self.tree.tag_configure("oddrow", background="#F5F5F5")
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(6, 0), anchor="w")
        self.btn_add_folder = ttk.Button(btn_frame, text="Add folder" if self.english_mode else "Agregar carpeta", command=self.on_add_folder)
        self.btn_add_folder.pack(side="left", padx=5)
        self.btn_add_multiple = ttk.Button(btn_frame, text="Add multiple folders" if self.english_mode else "Agregar varias carpetas", command=self.on_add_multiple_folders)
        self.btn_add_multiple.pack(side="left", padx=5)
        self.btn_start = ttk.Button(btn_frame, text="Organize" if self.english_mode else "Organizar", command=self.on_start)
        self.btn_start.pack(side="left", padx=5)
        self.btn_undo = ttk.Button(btn_frame, text="Undo organization" if self.english_mode else "Deshacer organización", command=self.on_undo)
        self.btn_undo.pack(side="left", padx=5)

        # Diccionario de checkboxes: item_id -> bool
        self._tree_checked = {}

        def toggle_check(item_id):
            val = self._tree_checked.get(item_id, False)
            self._tree_checked[item_id] = not val
            self.tree.set(item_id, "sel", "☑" if not val else "☐")

        def on_tree_click(event):
            col = self.tree.identify_column(event.x)
            row = self.tree.identify_row(event.y)
            if row and col == "#1":
                self.after(1, lambda r=row: toggle_check(r))

        self.tree.bind("<Button-1>", on_tree_click)
        # Deshabilitar selección visual azul
        self.tree.configure(selectmode="none")

        def remove_checked():
            checked = [iid for iid, v in self._tree_checked.items() if v]
            if not checked:
                self._show_modern_popup("Marca con ☑ las carpetas que deseas quitar de la lista.")
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

        def select_all_tree():
            for iid in self._tree_checked:
                self._tree_checked[iid] = True
                self.tree.set(iid, "sel", "☑")

        def deselect_all_tree():
            for iid in self._tree_checked:
                self._tree_checked[iid] = False
                self.tree.set(iid, "sel", "☐")

        self.btn_remove = ttk.Button(btn_frame, text="Remove folders" if self.english_mode else "Quitar Carpetas", command=remove_checked)
        self.btn_remove.pack(side="left", padx=5)
        self.status_label = ttk.Label(btn_frame, text="", font=("Segoe UI", 10, "bold"))
        self.status_label.pack(side="left", padx=10)

        # Botones seleccionar/deseleccionar en barra superior (Seleccionar primero)
        self.btn_sel_all = ttk.Button(sel_top_bar, text="Select all" if self.english_mode else "Seleccionar todo", command=select_all_tree)
        self.btn_sel_all.pack(side="left", padx=(0, 4))
        self.btn_desel_all = ttk.Button(sel_top_bar, text="Deselect all" if self.english_mode else "Deseleccionar todo", command=deselect_all_tree)
        self.btn_desel_all.pack(side="left")
        # Deshabilitar clic derecho en el árbol para evitar confusiones al usuario
        self.tree.bind("<Button-3>", lambda e: "break")
        self.tree.bind("<Button-2>", lambda e: "break")

    def _build_progress_bar(self):
        self.progress = ttk.Progressbar(self, mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=8, pady=(6, 6))

    def _build_log_area(self):
        frame = ttk.Frame(self, padding=(8, 0, 8, 0))
        frame.pack(fill="both", expand=True)
        self.lbl_cf_frame = ttk.Frame(frame)
        self.lbl_cf_frame.pack(fill="x", pady=(0, 2))
        self.lbl_cf_prefix = tk.Label(self.lbl_cf_frame, text="Organizing folder: " if self.english_mode else "Organizando Carpeta: ", font=("Segoe UI", 9), fg="#1a6eb5", anchor="w")
        self.lbl_cf_prefix.pack(side="left")
        self.lbl_cf_name = tk.Label(self.lbl_cf_frame, text="None" if self.english_mode else "Ninguna", font=("Segoe UI", 9, "bold"), fg="black", anchor="w")
        self.lbl_cf_name.pack(side="left")
        txt_frame = ttk.Frame(frame)
        txt_frame.pack(fill="both", expand=True)
        self.txt = tk.Text(txt_frame, height=10, state="disabled")
        scroll = tk.Scrollbar(txt_frame, command=self.txt.yview, width=22)
        self.txt.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.txt.pack(side="left", fill="both", expand=True)

    def _build_counters_bar(self):
        bar = ttk.Frame(self, padding=(8, 2, 8, 6))
        bar.pack(fill="x")
        self.lbl_analyzed = ttk.Label(bar, text="Files analyzed: 0" if self.english_mode else "Archivos analizados: 0")
        self.lbl_dirs = ttk.Label(bar, text="Folders created: 0" if self.english_mode else "Carpetas creadas: 0")
        self.lbl_dupes = ttk.Label(bar, text="")  # mantenido por compatibilidad, oculto
        self.lbl_time = ttk.Label(bar, text="Elapsed time: 0m 0s" if self.english_mode else "Tiempo transcurrido: 0m 0s")
        self.lbl_analyzed.pack(side="left")
        ttk.Label(bar, text=" ").pack(side="left")
        self.lbl_dirs.pack(side="left")
        ttk.Label(bar, text=" ").pack(side="left")
        self.lbl_time.pack(side="left")

    def _clear_log(self):
        try:
            self.txt.configure(state="normal")
            self.txt.delete("1.0", tk.END)
            self.txt.configure(state="disabled")
            self.lbl_cf_name.config(text="None" if getattr(self, 'english_mode', False) else "Ninguna")
        except Exception:
            pass

    def _close_aux_windows(self):
        for attr in ['donate_win', 'support_win', 'tutorial_win', 'limits_win']:
            win_holder = getattr(self, attr, None)
            if win_holder and hasattr(win_holder, 'win') and win_holder.win:
                try:
                    win_holder.win.destroy()
                except Exception:
                    pass
                win_holder.win = None
    def _update_undo_button_state(self):
        has_operations_to_undo = len(self.moved_ops) > 0
        has_folders = len(self.queue) > 0
        should_enable = (has_operations_to_undo or has_folders) and not self.is_processing
        if self.btn_undo:
            if should_enable:
                self.btn_undo.config(state="normal")
            else:
                self.btn_undo.config(state="disabled")

    def _set_buttons_state(self, state):
        state_str = "normal" if state else "disabled"
        if self.btn_add_folder:
            self.btn_add_folder.config(state=state_str)
        if self.btn_start:
            self.btn_start.config(state=state_str)
        if self.btn_undo:
            self._update_undo_button_state()
        if self.btn_remove:
            self.btn_remove.config(state=state_str)

    def on_tutorial(self):
        self._close_aux_windows()
        w = tk.Toplevel(self)
        w.title("Tutorial — Click2Folders" if getattr(self, 'english_mode', False) else "Tutorial")
        w.resizable(True, True)
        safe_icon(w)
        w.withdraw()

        # Usar canvas con scrollbar para que quepa en pantalla
        main_frame = ttk.Frame(w)
        main_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(main_frame, highlightthickness=0)
        vsb = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        pad = ttk.Frame(canvas, padding=(12, 2, 12, 12))
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
                    return  # nada que scrollear, ignorar la rueda
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        wrap_width = 760

        # ── Encabezado siempre visible ──────────────────────────────
        tk.Label(pad, text="📁  Click2Folders — Automatic Photo & Video Organizer" if getattr(self, 'english_mode', False) else "📁  Click2Folders — Organizador Automático de Fotos y Videos",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0,4))

        # ── Secciones desplegables ───────────────────────────────────
        eng = getattr(self, 'english_mode', False)
        if eng:
            sections_data = [
                ("🤔  What does the program do?", [
                    ("If you have many unorganized photos on your PC and you would like to sort them chronologically", False),
                    ("**now you can organize them with one click!**", False),
                    ("To achieve this, the program first detects the year and month dates of your files to", False),
                    ("create year folders and month subfolders, then moves them to the folder where they were taken.", False),
                    ("     **Structure example:**", False),
                    ("     **Year folder:** 2025", False),
                    ("     **Month subfolders:** 1 January / 2 February / 3 March / etc.", False),
                ]),
                ("📋  How to use the program?", [
                    ("1. Add the folder or folders you want.", False),
                    ("2. Choose one of the 4 organization modes.", False),
                    ("3. Check the selection column for the folders you want and click organize.", False),
                    ("If you don't want the month number prefix, before organizing check the box:", False),
                    ("   **\"Do not prepend month number in subfolders\"**.", False),
                ]),
                ("📅  What dates does it detect?", [
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
                    ("• Remove Folders:", True),
                    ("   Removes the checked folders from the list.", False),
                    ("• Undo organization:", True),
                    ("   Moves all files from subfolders back to the root folder and removes empty month folders.", False),
                    ("• Do not prepend month number in subfolders:", True),
                    ("   If checked, subfolders won't have the corresponding month number.", False),
                    ("• English Style / Spanish Style:", True),
                    ("   Changes the interface language, tutorial and sets month", False),
                    ("   subfolder names to English when organizing: (1 January, 2 February, etc...).", False),
                ]),
                ("ℹ  Additional information", [
                    ("• Root folder:", True),
                    ("   The original folder you load or select in the program.", False),
                    ("• Supported extensions:", True),
                    ("   The program processes any image or video file (jpeg, gif, png, mp4, etc.)", False),
                    ("   as long as it contains metadata or dates in its name.", False),
                    ("• Interface:", True),
                    ("   Has a window for loading folders, another that shows real-time progress,", False),
                    ("   and at the bottom shows data like: analyzed files, created folders, and elapsed time.", False),
                    ("• Organizing Folder:", True),
                    ("   Shows in real-time which folder is being processed.", False),
                    ("• Status column:", True),
                    ("   Shows the number of files in the folder or subfolder count.", False),
                    ("• Selection column \"Sel\":", True),
                    ("   Check the folders you want to organize or undo.", False),
                    ("• GIF files:", True),
                    ("   They have no capture date or media created date. Only date in the name, creation and modification dates.", False),
                    ("• Valid date range:", True),
                    ("   The program only recognizes valid dates from year **1900** onwards.", False),
                ]),
                ("⚠  Important", [
                    ("• The program **NEVER** deletes your photos or videos, it only organizes them.", False),
                    ("• You can always undo the organization done by the program and reorganize in any of the 4 modes.", False),
                    ("• The program does not create empty folders. If a month subfolder is missing, no files had that date.", False),
                    ("• If you don't check **\"Do not prepend month number in subfolders\"** the subfolders will include the month number.", False),
                    ("   Example: **\"1 January / 6 June / 12 December\"**.", False),
                    ("• The program does not rename your files or year folders.", False),
                    ("**• Keep in mind that if you add folders you organized yourself, your personal organization**", False),
                    ("**  is lost since the program sorts chronologically and does not save your custom order.**", False),
                ]),
            ]
        else:
            sections_data = [
                ("🤔  ¿Qué hace el programa?", [
                    ("Si tienes en tu pc muchas fotos en desorden y te gustaría ordenarlas cronológicamente", False),
                    ("**¡ahora las puedes organizar en un click!**", False),
                    ("Para lograrlo el programa primero detecta las fechas de año y mes de tus archivos para", False),
                    ("crear las carpetas de año y subcarpetas por mes, luego los mueve a la carpeta en que fueron tomadas.", False),
                    ("     **Ejemplo de estructura:**", False),
                    ("     **Carpeta año:** 2025", False),
                    ("     **Subcarpetas por mes:** 1 Enero / 2 Febrero / 3 Marzo / etc.", False),
                ]),
                ("📋  ¿Cómo usar el programa?", [
                    ("1. Agrega la carpeta o carpetas que quieras.", False),
                    ("2. Elige alguno de los 4 modos de organización.", False),
                    ("3. Marca en la columna de selección las carpetas que quieras y da click en organizar.", False),
                    ("Si no quieres anteponer el número de mes, antes de organizar marca la casilla:", False),
                    ("   **\"No anteponer número de mes en subcarpetas\"**.", False),
                ]),
                ("📅  ¿Qué fechas detecta?", [
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
                    ("• Quitar Carpetas:", True),
                    ("   Elimina de la lista las carpetas marcadas con ☑.", False),
                    ("• Deshacer organización:", True),
                    ("   Mueve todos los archivos de las subcarpetas de vuelta a la carpeta raíz y elimina las carpetas de mes vacías.", False),
                    ("   Úsalo cuando quieras reorganizar tus fotos con un modo diferente.", False),
                    ("• No anteponer número de mes en subcarpetas:", True),
                    ("   Si está marcada, las subcarpetas no tendrán número correspondiente al mes.", False),
                    ("• Modo Ingles / Spanish Style:", True),
                    ("   Cambia el idioma de la interfaz, el tutorial y al organizar las carpetas pone los nombres de", False),
                    ("   las subcarpetas por mes en ingles: (1 January, 2 February, etc...).", False),
                ]),
                ("ℹ  Información adicional", [
                    ("• Carpeta raíz:", True),
                    ("   Es la misma carpeta original que cargas o seleccionas en el programa.", False),
                    ("• Extensiones soportadas:", True),
                    ("   El programa procesa cualquier archivo de imagen o video (jpeg, gif, png, mp4, etc.)", False),
                    ("   siempre que contenga metadatos o fechas en su nombre.", False),
                    ("• Interfaz:", True),
                    ("   Cuenta con una ventana para carga de carpetas, otra que muestra en tiempo real lo que hace el programa,", False),
                    ("   en la parte inferior muestra datos como: archivos analizados, carpetas creadas, y el tiempo que duró la organización.", False),
                    ("• Organizando Carpeta:", True),
                    ("   Muestra en tiempo real qué carpeta se está procesando durante la organización o desorganización.", False),
                    ("• Columna Estado:", True),
                    ("   Muestra el número de archivos que contiene la carpeta o cantidad de subcarpetas.", False),
                    ("• Columna Selección \"Sel\":", True),
                    ("   Marca las carpetas que quieras organizar o desorganizar.", False),
                    ("• Archivos Gif:", True),
                    ("   No tienen fecha de captura, ni fecha en medio creado, solo se pueden organizar por fecha en el nombre, creación y modificación.", False),
                    ("• Rango de fechas detectadas:", True),
                    ("   El programa solo reconoce fechas válidas desde el año **1.900** en adelante.", False),
                ]),
                ("⚠  Importante", [
                    ("• El programa **NUNCA** borra tus fotos ni videos.", False),
                    ("• Siempre puedes deshacer la organización hecha previamente con el programa y volver a organizarla en cualquiera de los 4 modos las veces que quieras.", False),
                    ("• El programa no crea carpetas vacías, Si falta una subcarpeta de mes es porque no se detectaron fotos con esa fecha en el modo elegido.", False),
                    ("• Si no marcas **\"No anteponer número de mes en subcarpetas\"** las subcarpetas se nombrarán con el número correspondiente al mes,", False),
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
            hdr = tk.Frame(pad, cursor="hand2")
            hdr.pack(fill="x", anchor="w")
            arrow_lbl = tk.Label(hdr, text="► ", font=("Segoe UI", 10, "bold"), foreground="#1a6eb5")
            arrow_lbl.pack(side="left")
            tk.Label(hdr, text=sec_title, font=("Segoe UI", 10, "bold"), foreground="#1a6eb5",
                     justify="left").pack(side="left")
            body = tk.Frame(pad)
            # NO hacemos body.pack() aquí — se hará en toggle justo después del hdr
            for text, is_bold in sec_lines:
                if '**' in text:
                    parts = re.split(r'(\*\*.*?\*\*)', text)
                    row = tk.Frame(body)
                    row.pack(anchor="w", padx=16, pady=1)
                    for part in parts:
                        if part.startswith('**') and part.endswith('**') and len(part) > 4:
                            inner = part[2:-2]
                            tk.Label(row, text=inner, font=("Segoe UI", 9, "bold"),
                                     justify="left", anchor="w").pack(side="left")
                        else:
                            tk.Label(row, text=part, font=("Segoe UI", 9),
                                     justify="left", anchor="w").pack(side="left")
                else:
                    font = ("Segoe UI", 9, "bold") if is_bold else ("Segoe UI", 9)
                    tk.Label(body, text=text, font=font, justify="left",
                             wraplength=wrap_width - 20, anchor="w").pack(anchor="w", padx=16, pady=1)
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
                    al.config(text="► ")
                else:
                    for j, (_, _, other_body, other_var, other_arrow) in enumerate(accordion_items):
                        if j != current_i and other_var.get():
                            other_body.pack_forget()
                            other_var.set(False)
                            other_arrow.config(text="► ")
                    bd.pack(fill="x", anchor="w", before=after_widget)
                    bv.set(True)
                    al.config(text="▼ ")
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
        # Posición: justo debajo de la barra de botones (~100px desde el top de la ventana principal)
        toolbar_offset = 100  # botones + modo de organización
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
    def on_support(self):
        self._close_aux_windows()
        w = tk.Toplevel(self)
        eng = getattr(self, 'english_mode', False)
        w.title("Support" if eng else "Soporte")
        w.resizable(False, False)
        w.withdraw()
        w.transient(self)
        pad = ttk.Frame(w, padding=18)
        pad.pack(fill="both", expand=True)
        title = ttk.Label(pad, text="Do you have any questions or suggestions?" if eng else "¿Tienes alguna duda o sugerencia?", font=("Segoe UI", 12, "bold"))
        title.pack(pady=(0, 6))
        ttk.Label(pad, text="Contact us!\n" if eng else "¡Contáctanos!\n", font=("Segoe UI", 10)).pack()
        ttk.Label(pad, text="Click the email to copy it" if eng else "Haz click en el correo para copiarlo", font=("Segoe UI", 9, "italic")).pack(pady=(0, 6))

        def copy_mail(e=None):
            self.clipboard_clear()
            self.clipboard_append("click2folders@gmail.com")
            if e:
                x = e.x_root
                y = e.y_root - 30
                self._show_tooltip_at("Email copied to clipboard" if getattr(self, 'english_mode', False) else "Correo copiado al portapapeles", x, y)

        mail = tk.Label(pad, text="click2folders@gmail.com",
                        font=("Segoe UI", 11, "underline"), fg="blue", cursor="hand2")
        mail.bind("<Button-1>", copy_mail)
        mail.pack(pady=(0, 10))
        ttk.Label(pad, text="Developed by: Germán Vargas", font=("Segoe UI", 9)).pack(pady=(6, 10))
        ttk.Label(pad, text="© 2026 Click2Folders. All rights reserved." if eng else "© 2026 Click2Folders. Todos los derechos reservados.", font=("Segoe UI", 8)).pack()
        center_window(w, self)
        w.deiconify()
        self.support_win.win = w
        safe_icon(self.support_win.win)
        for sw in (w, pad):
            sw.bind("<Button-3>", lambda e: "break")
            sw.bind("<Button-2>", lambda e: "break")

    def _show_tooltip_at(self, message, x, y):
        tooltip = tk.Toplevel(self)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tooltip, text=message,
                         background="lightyellow", relief="solid", borderwidth=1,
                         font=("Segoe UI", 9), padx=8, pady=4)
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
            tk.Label(tooltip, text=message, background="lightyellow", relief="solid",
                     borderwidth=1, font=("Segoe UI", 9), padx=8, pady=4).pack()
            tooltip.after(2000, lambda: tooltip.destroy() if tooltip.winfo_exists() else None)
        except Exception:
            pass

    def on_donate(self):
        self._close_aux_windows()
        w = tk.Toplevel(self)
        eng = getattr(self, 'english_mode', False)
        w.title("Donations" if eng else "Donaciones")
        w.resizable(False, False)
        safe_icon(w)
        
        w.withdraw()   # Ocultar primero
        
        pad = ttk.Frame(w, padding=20)
        pad.pack(fill="both", expand=True)
        
        # Contenido
        ttk.Label(pad, text="Thank you for using Click2Folders!" if eng else "¡Gracias por usar Click2Folders!", font=("Segoe UI", 10, "bold"), justify="center").pack(pady=(0, 6))
        ttk.Label(pad, text="If you like the program, consider donating to support its development!" if eng else "¡Si te gusta el programa, considera donar para apoyar su desarrollo!", font=("Segoe UI", 10, "bold"), justify="center").pack(pady=(0, 6))
        ttk.Label(pad, text="", font=("Segoe UI", 10)).pack()
        ttk.Label(pad, text="Click the links to copy them" if eng else "Haz click en los links para copiarlos", font=("Segoe UI", 10, "italic"), justify="center").pack(pady=(0, 6))
        ttk.Label(pad, text="Paypal:", font=("Segoe UI", 10, "bold"), justify="center").pack(pady=(0, 6))

        def copy_paypal(e=None):
            self.clipboard_clear()
            self.clipboard_append("regerman78@gmail.com")
            self._show_tooltip_temporal("Email copied to clipboard" if getattr(self, 'english_mode', False) else "Correo copiado al portapapeles", event=e)

        paypal_label = tk.Label(pad, text="regerman78@gmail.com", font=("Segoe UI", 10), justify="center", fg="blue", cursor="hand2")
        paypal_label.bind("<Button-1>", copy_paypal)
        paypal_label.pack(pady=(0, 6))
        ttk.Separator(pad, orient='horizontal').pack(fill='x', pady=10)
        
        ttk.Label(pad, text="Nequi Colombia Key:" if eng else "Llave Nequi Colombia:", font=("Segoe UI", 10, "bold"), justify="center").pack(pady=(0, 6))

        def copy_nequi(e=None):
            self.clipboard_clear()
            self.clipboard_append("regerman78@gmail.com")
            self._show_tooltip_temporal("Email copied to clipboard" if getattr(self, 'english_mode', False) else "Correo copiado al portapapeles", event=e)

        nequi_label = tk.Label(pad, text="regerman78@gmail.com", font=("Segoe UI", 10), justify="center", fg="blue", cursor="hand2")
        nequi_label.bind("<Button-1>", copy_nequi)
        nequi_label.pack(pady=(0, 6))
        ttk.Label(pad, text="Red*** Var***", font=("Segoe UI", 10, "bold"), justify="center").pack(pady=(0, 6))
        ttk.Separator(pad, orient='horizontal').pack(fill='x', pady=10)
        ttk.Label(pad, text="Tether USDT (TRC20):", font=("Segoe UI", 10, "bold"), justify="center").pack(pady=(0, 6))

        def load_qr():
            try:
                import urllib.request
                from io import BytesIO
                with urllib.request.urlopen("https://postimg.cc/MvbVg5wT") as response:
                    img_data = response.read()
                    img = Image.open(BytesIO(img_data))
                    img = img.resize((150, 150), Image.LANCZOS)
                    return ImageTk.PhotoImage(img)
            except Exception:
                return None

        qr_container = ttk.Frame(pad)
        qr_container.pack(pady=(0, 6))
        threading.Thread(target=lambda: self._load_qr_async(qr_container, w), daemon=True).start()

        def copy_usdt(e=None):
            self.clipboard_clear()
            self.clipboard_append("TFKbpPK5n5Dv3NV3svEDAyd68fxNyUzmDn")
            self._show_tooltip_temporal("USDT address copied to clipboard" if getattr(self, 'english_mode', False) else "Dirección USDT copiada al portapapeles", event=e)

        usdt_label = tk.Label(pad, text="TFKbpPK5n5Dv3NV3svEDAyd68fxNyUzmDn",
                              font=("Segoe UI", 9), justify="center", fg="blue", cursor="hand2")
        usdt_label.bind("<Button-1>", copy_usdt)
        usdt_label.pack(pady=(0, 6))
        ttk.Separator(pad, orient='horizontal').pack(fill='x', pady=10)
        ttk.Label(pad, text="Developer's Whatsapp" if eng else "Whatsapp Desarrollador Germán:", font=("Segoe UI", 10, "bold"), justify="center").pack(pady=(0, 6))

        def open_whatsapp(e=None):
            try:
                webbrowser.open("https://bit.ly/click2folders")
            except Exception:
                self.clipboard_clear()
                self.clipboard_append("https://bit.ly/click2folders")

        whatsapp_label = tk.Label(pad, text="https://bit.ly/click2folders",
                                  font=("Segoe UI", 10), justify="center", fg="blue", cursor="hand2")
        whatsapp_label.bind("<Button-1>", open_whatsapp)
        whatsapp_label.pack(pady=(0, 6))
        ttk.Separator(pad, orient='horizontal').pack(fill='x', pady=10)
        ttk.Label(pad, text="", font=("Segoe UI", 10)).pack()
        ttk.Label(pad, text="Thank you for your support!" if eng else "¡Gracias por tu apoyo!", font=("Segoe UI", 10, "bold"), justify="center").pack(pady=(0, 6))
        ttk.Label(pad, text="", font=("Segoe UI", 10)).pack()
        ttk.Label(pad, text="Developed by: Germán Vargas" if eng else "Desarrollado por: Germán Vargas", font=("Segoe UI", 10, "bold"), justify="center").pack(pady=(0, 6))
        ttk.Label(pad, text="© 2026 Click2Folders. All rights reserved." if eng else "© 2026 Click2Folders. Todos los derechos reservados.", font=("Segoe UI", 10, "bold"), justify="center").pack(pady=(0, 6))

        # === CENTRADO Y FOCO FUERTE ===
        def finalize_window():
            w.update_idletasks()
            sw = w.winfo_screenwidth()
            sh = w.winfo_screenheight()
            x = (sw - w.winfo_width()) // 2
            y = max(30, (sh - w.winfo_height()) // 2 - 20)
            w.geometry(f"+{x}+{y}")
            w.deiconify()
            w.focus_force()
            w.lift()
        self.after(350, finalize_window)
        self.donate_win.win = w
        for dw in (w, pad):
            dw.bind("<Button-3>", lambda e: "break")
            dw.bind("<Button-2>", lambda e: "break")

    def _check_launch_donation(self):
        count = _get_launch_count()
        if count > 0 and count % 5 == 0:
            self.on_donate()

    # === ESTAS DOS FUNCIONES DEBEN ESTAR FUERA DE on_donate ===
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
        qr_label = tk.Label(container, image=qr_photo)
        qr_label.image = qr_photo
        qr_label.pack()
        self.after(100, lambda: center_window(parent, self))
    def _show_image_window(self, parent, img_path):
        w = tk.Toplevel(parent)
        w.resizable(False, False)
        w.withdraw()
        frm = ttk.Frame(w, padding=10)
        frm.pack(fill="both", expand=True)
        img = load_image(img_path, max_width=860, max_height=560)
        if img is None:
            lbl = tk.Label(frm, text=f"No se pudo cargar la imagen:\n{img_path}", fg="red", justify="center")
            lbl.pack()
        else:
            lbl = tk.Label(frm, image=img)
            lbl.image = img
            lbl.pack()
        center_window(w, parent)
        w.deiconify()
        return w

    def _show_modern_popup(self, message):
        popup = tk.Toplevel(self)
        eng_pop = getattr(self, 'english_mode', False)
        popup.title("Notice" if eng_pop else "Aviso")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
        safe_icon(popup)
        frm = ttk.Frame(popup, padding=16)
        frm.pack(fill="both", expand=True)
        tk.Label(frm, text=message, font=("Segoe UI", 10), justify="center").pack(pady=(10, 20))
        ttk.Button(frm, text="OK" if eng_pop else "Aceptar", command=popup.destroy).pack()
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
        file_count = count_all_files_including_organized(folder)
        eng_add = getattr(self, 'english_mode', False)
        status = f"{file_count} {'files to organize' if eng_add else 'archivos para organizar'}"
        tag = "oddrow" if len(self.queue) % 2 == 0 else "evenrow"
        item_id = self.tree.insert("", "end", values=("☐", folder, status), tags=(tag,))
        if hasattr(self, '_tree_checked'):
            self._tree_checked[item_id] = False
        self.queue.append(folder_norm)
        self.folder_indexes[folder_norm] = item_id
        self._update_undo_button_state()

    def on_add_multiple_folders(self):
        if getattr(self, '_no_show_multiple_intro', False):
            self._pick_multiple_folders()
            return
        eng = getattr(self, 'english_mode', False)
        # Ventana de instrucción previa
        intro = tk.Toplevel(self)
        intro.title("Add multiple folders" if eng else "Agregar varias carpetas")
        intro.resizable(False, False)
        intro.transient(self)
        intro.grab_set()
        safe_icon(intro)
        frm = ttk.Frame(intro, padding=20)
        frm.pack(fill="both", expand=True)
        tk.Label(frm, text="How does it work?" if eng else "¿Cómo funciona?", font=("Segoe UI", 11, "bold")).pack(pady=(0,10))
        tk.Label(frm, text="Select a root folder and the program will show\nall its subfolders so you can choose which ones to add." if eng else "Selecciona una carpeta raíz y el programa mostrará\ntodas sus subcarpetas para que elijas cuáles agregar.",
                 font=("Segoe UI", 10), justify="center").pack(pady=(0,16))
        tk.Label(frm, text="Example: 'Photos' folder with '2020', 'Trips', 'Family' subfolders...\nSelect 'Photos' and pick the ones you want to organize." if eng else "Ej: carpeta 'Fotos' con subcarpetas '2020', 'Viajes', 'Familia'...\nSelecciona 'Fotos' y elige las que deseas organizar.",
                 font=("Segoe UI", 9), justify="center", foreground="#444").pack(pady=(0,16))
        no_show_intro_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="Don't show this message again" if eng else "No volver a mostrar este mensaje", variable=no_show_intro_var).pack(pady=(0, 10))
        def do_intro_ok():
            self._no_show_multiple_intro = no_show_intro_var.get()
            intro.grab_release()
            intro.destroy()
            self._pick_multiple_folders()
        def do_intro_cancel():
            intro.grab_release()
            intro.destroy()
        btn_row = ttk.Frame(frm)
        btn_row.pack()
        ttk.Button(btn_row, text="Got it" if eng else "Entendido", command=do_intro_ok).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Cancel" if eng else "Cancelar", command=do_intro_cancel).pack(side="left", padx=6)
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
        eng_pick2 = getattr(self, 'english_mode', False)
        win.title("Select folders" if eng_pick2 else "Seleccionar Carpetas")
        win.resizable(True, True)
        win.transient(self)
        win.grab_set()
        safe_icon(win)
        win.withdraw()

        ttk.Label(win, text=f"Raíz: {root_folder}", font=("Segoe UI", 9), foreground="#555").pack(anchor="w", padx=12, pady=(10,0))

        sel_bar = ttk.Frame(win)
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
        ttk.Button(sel_bar, text="Deselect all" if eng_pick else "Deseleccionar todas", command=deselect_all).pack(side="left", padx=4)
        ttk.Button(sel_bar, text="Select all" if eng_pick else "Seleccionar todas", command=select_all).pack(side="left", padx=4)

        # Tamaño adaptable: máx 15 items visibles, con scroll si hay más
        ITEM_H = 28
        MAX_VIS = 15
        n = len(candidates)
        list_h = min(n * ITEM_H + 10, MAX_VIS * ITEM_H)
        use_scroll = n > MAX_VIS

        frame_list = ttk.Frame(win)
        frame_list.pack(fill="both", expand=use_scroll, padx=12, pady=4)

        if use_scroll:
            canvas_w = tk.Canvas(frame_list, highlightthickness=0, height=list_h)
            vsb = ttk.Scrollbar(frame_list, orient="vertical", command=canvas_w.yview)
            canvas_w.configure(yscrollcommand=vsb.set)
            vsb.pack(side="right", fill="y")
            canvas_w.pack(side="left", fill="both", expand=True)
            inner = ttk.Frame(canvas_w)
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

        btns = ttk.Frame(win)
        btns.pack(pady=8)

        def do_add():
            to_add = [p for p, (v, _) in check_vars.items() if v.get()]
            if canvas_w: canvas_w.unbind_all("<MouseWheel>")
            win.grab_release()
            win.destroy()
            added = 0
            for path in to_add:
                norm = os.path.normcase(os.path.abspath(path))
                if norm not in self.queue:
                    file_count = count_all_files_including_organized(path)
                    eng_s = getattr(self, 'english_mode', False)
                    status = f"{file_count} {'files to organize' if eng_s else 'archivos para organizar'}"
                    tag = "oddrow" if len(self.queue) % 2 == 0 else "evenrow"
                    item_id = self.tree.insert("", "end", values=("☐", path, status), tags=(tag,))
                    if hasattr(self, '_tree_checked'): self._tree_checked[item_id] = False
                    self.queue.append(norm)
                    self.folder_indexes[norm] = item_id
                    added += 1
            self._update_undo_button_state()
            if added:
                self._log(f"✓ {added} {'folder(s) added' if getattr(self, 'english_mode', False) else 'carpeta(s) agregada(s)'}")

        def do_cancel():
            if canvas_w: canvas_w.unbind_all("<MouseWheel>")
            win.grab_release()
            win.destroy()
            # No agrega nada

        eng_b = getattr(self, 'english_mode', False)
        ttk.Button(btns, text="Add selected" if eng_b else "Agregar seleccionadas", command=do_add).pack(side="left", padx=8)
        ttk.Button(btns, text="Cancel" if eng_b else "Cancelar", command=do_cancel).pack(side="left", padx=8)

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
                messagebox.showinfo("Undone" if eng_und else "Desorganizada",
                                    "The organization has been undone successfully.\nAll files have been moved back to the root folder." if eng_und else "La organización ha sido deshecha correctamente.\nTodos los archivos han sido movidos de vuelta a la carpeta raíz.")
        except Exception as e:
            self.after(0, lambda: self._log(f"Error deshaciendo organización: {e}"))
            if show_message:
                eng_und2 = getattr(self, 'english_mode', False)
                messagebox.showerror("Error" if eng_und2 else "Error", f"Could not undo the organization: {e}" if eng_und2 else f"No se pudo deshacer la organización: {e}")

    def _set_status(self, msg):
        base_msg = msg
        self.status_label.config(text=base_msg)
        self.progress.config(mode="determinate")

        def animate_ellipsis(dots=0):
            if not self.is_processing:
                return
            ellipsis = "." * dots
            self.status_label.config(text=base_msg + ellipsis)
            next_dots = (dots % 3) + 1
            self.after(300, lambda: animate_ellipsis(next_dots))

        animate_ellipsis()

    def _open_overlay(self, first_text="Organizando archivos", indeterminate=False):
        if self.overlay and tk.Toplevel.winfo_exists(self.overlay):
            return
        self.overlay = tk.Toplevel(self)
        self.overlay.title("Procesando")
        self.overlay.resizable(False, False)
        self.overlay.transient(self)
        self.overlay.grab_set()
        safe_icon(self.overlay)
        frm = ttk.Frame(self.overlay, padding=12)
        frm.pack(fill="both", expand=True)
        self.overlay_text = tk.Label(frm, text=first_text, font=("Segoe UI", 10, "bold"))
        self.overlay_text.pack(pady=(4, 10))
        mode = "indeterminate" if indeterminate else "determinate"
        self.marquee = ttk.Progressbar(frm, mode=mode, maximum=100)
        self.marquee.pack(fill="x")
        if indeterminate:
            self.marquee.start(20)
        center_window(self.overlay, None)
        self.update_idletasks()

    def _update_overlay(self, msg, indeterminate=False):
        if self.overlay and tk.Toplevel.winfo_exists(self.overlay):
            self.overlay_text.config(text=msg)
            if self.marquee:
                new_mode = "indeterminate" if indeterminate else "determinate"
                if self.marquee.cget("mode") != new_mode:
                    if new_mode == "indeterminate":
                        self.marquee.stop()
                        self.marquee.config(mode="indeterminate")
                        self.marquee.start(20)
                    else:
                        self.marquee.stop()
                        self.marquee.config(mode="determinate")
            self.update_idletasks()

    def _close_overlay(self):
        if self.overlay and tk.Toplevel.winfo_exists(self.overlay):
            if self.marquee:
                self.marquee.stop()
            self.overlay.destroy()
            self.overlay = None
            self.marquee = None

    def _reset_counters(self):
        self.total_analyzed = 0
        self.total_dirs_created = 0
        self.start_time = None
        self._refresh_counters()
        self._clear_log()

    def _refresh_counters(self):
        elapsed = time.time() - self.start_time if self.start_time else 0
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        eng = getattr(self, 'english_mode', False)
        self.lbl_analyzed.configure(text=f"{'Files analyzed:' if eng else 'Archivos analizados:'} {self.total_analyzed}")
        self.lbl_dirs.configure(text=f"{'Folders created:' if eng else 'Carpetas creadas:'} {self.total_dirs_created}")
        self.lbl_time.configure(text=f"{'Elapsed time:' if eng else 'Tiempo transcurrido:'} {minutes}m {seconds}s")

    def _log(self, text):
        self.txt.configure(state="normal")
        self.txt.insert("end", text + "\n")
        self.txt.see("end")
        self.txt.configure(state="disabled")

    def _clear_log(self):
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.configure(state="disabled")
        try:
            self.lbl_cf_name.config(text="None" if getattr(self, 'english_mode', False) else "Ninguna")
        except Exception:
            pass

    def on_start(self):
        if not self.queue:
            messagebox.showinfo(APP_NAME, "Add a folder to the queue to start." if getattr(self, 'english_mode', False) else "Agrega una carpeta a la cola para iniciar.")
            return

        # Determinar qué carpetas procesar: marcadas con ☑
        checked_folders = []
        if hasattr(self, '_tree_checked'):
            for iid, checked in self._tree_checked.items():
                if checked:
                    try:
                        folder = self.tree.item(iid)["values"][1]
                        checked_folders.append(folder)
                    except Exception:
                        pass
        
        if not checked_folders:
            popup = tk.Toplevel(self)
            eng_start = getattr(self, 'english_mode', False)
            popup.title("Selection required" if eng_start else "Selección requerida")
            popup.resizable(False, False)
            popup.transient(self)
            popup.grab_set()
            safe_icon(popup)
            frm = ttk.Frame(popup, padding=20)
            frm.pack()
            tk.Label(frm, text="First select the folders you want to organize by checking the checkbox (☑)." if eng_start else "Primero selecciona las carpetas que deseas organizar marcando el checkbox (☑).", font=("Segoe UI", 10), justify="center", wraplength=280).pack(pady=(0, 16))
            ttk.Button(frm, text="Got it" if eng_start else "Entendido", command=popup.destroy).pack()
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
                    "If no date is found in any of the 3 options\n(media created, capture date or name), the file will not be moved\nto any subfolder and will remain in the root folder." if eng else
                    "Si no encuentra fecha en ninguna de las 3 opciones\n(medio creado, fecha de captura o nombre), el archivo no se moverá\na ninguna subcarpeta y quedará en la carpeta raíz.",
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
        eng = getattr(self, 'english_mode', False)
        tip.title("Notice" if eng else "Aviso")
        safe_icon(tip)
        tip.resizable(False, False)
        tip.transient(self)
        tip.grab_set()
        frm = ttk.Frame(tip, padding=14)
        frm.pack(fill="both", expand=True)
        if title:
            tk.Label(frm, text=title, font=("Segoe UI", 10, "bold", "underline"), justify="left").pack(anchor="w", pady=(0,10))
        for line in text.split('\n'):
            if line.strip():
                tk.Label(frm, text=line, justify="left", font=("Segoe UI", 9)).pack(anchor="w", pady=(2,0))
        # Solo mostrar checkbox "no volver a mostrar" si es un aviso de modo (no de reorganización)
        var = tk.BooleanVar(value=False)
        if not flag_attr.startswith("_dummy"):
            ttk.Checkbutton(frm, text="Don't show again" if eng else "No volver a mostrar", variable=var).pack(anchor="w", pady=(10,10))
        else:
            ttk.Frame(frm).pack(pady=5)
        btns = ttk.Frame(frm)
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
        ttk.Button(btns, text="Continue" if eng else "Continuar", command=do_continue).pack(side="left", padx=6)
        ttk.Button(btns, text="Cancel" if eng else "Cancelar", command=do_cancel).pack(side="left", padx=6)
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
        try:
            for folder in folders_to_process:
                folder_norm = os.path.normcase(os.path.abspath(folder))
                folder_basename = os.path.basename(folder)
                self.after(0, lambda f=folder_basename: self.lbl_cf_name.config(text=f))
                # Auto-undo si la carpeta tiene subcarpetas año/mes (organización previa)
                if has_year_subdirs(folder):
                    self.after(0, lambda fn=folder_norm: self.tree.set(self.folder_indexes.get(fn, ""), "status", "Undoing..." if getattr(self, 'english_mode', False) else "Deshaciendo..."))
                    self.after(0, lambda f=folder_basename, e5=getattr(self, 'english_mode', False): self._log(f"{'Undoing previous organization in:' if e5 else 'Deshaciendo organización previa en:'} {f}"))
                    self._undo_folder(folder)
                    self.after(0, lambda fn=folder_norm: self.tree.set(self.folder_indexes.get(fn, ""), "status", "Waiting" if getattr(self, 'english_mode', False) else "En espera"))
                    self.after(0, lambda e6=getattr(self, 'english_mode', False): self._log("Starting organization from scratch..." if e6 else "Iniciando organización desde cero..."))
                self.after(0, lambda fn=folder_norm: self.tree.set(self.folder_indexes.get(fn, ""), "status", "Organizing..." if getattr(self, 'english_mode', False) else "Organizando..."))
                self.after(0, lambda: self.progress.configure(value=0))
                self.after(0, lambda f=folder_basename, e7=getattr(self, 'english_mode', False): self._log(f"{'Organizing folder:' if e7 else 'Organizando carpeta:'} {f}"))
                self._organize_folder(folder)
                self.after(0, lambda fn=folder_norm: self.tree.set(self.folder_indexes.get(fn, ""), "status", "Organized ✓" if getattr(self, 'english_mode', False) else "Organizado ✓"))
                self.after(0, lambda: self.progress.configure(value=100))
        finally:
            if WIN32_OK:
                pythoncom.CoUninitialize()
            if hasattr(self, 'timer_id'):
                self.after_cancel(self.timer_id)
            self.after(0, self._refresh_counters)
            self.is_processing = False
            self.after(0, lambda: self.status_label.config(text=""))
            self.after(0, lambda: self.progress.config(value=0))
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
        messagebox.showinfo(APP_NAME, "Organization process completed." if getattr(self, 'english_mode', False) else "Proceso de organización finalizado.")
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
        self.after(0, lambda: self.progress.configure(value=0))
        processed = 0
        for path in file_list:
            processed += 1
            self.total_analyzed += 1
            fname = os.path.basename(path)
            dt = self._get_target_date(path, fname, mode)
            if not dt:
                self.after(0, lambda n=fname, e8=getattr(self, 'english_mode', False): self._log(f"{'No date detected:' if e8 else 'Sin fecha detectada:'} {n} {'— skipped.' if e8 else '— se omite.'}"))
                continue
            year_dir = os.path.join(folder, str(dt.year))
            eng = getattr(self, 'english_mode', False)
            if getattr(self, "var_no_month_num", None) and self.var_no_month_num.get():
                month_dir = os.path.join(year_dir, readable_month(dt.month, eng))
            else:
                month_dir = os.path.join(year_dir, f"{dt.month} {readable_month(dt.month, eng)}")
            os.makedirs(year_dir, exist_ok=True)
            self.created_dirs.add(year_dir)
            os.makedirs(month_dir, exist_ok=True)
            if month_dir not in self.created_dirs:
                self.created_dirs.add(month_dir)
                self.total_dirs_created += 1
            target = self._dedupe_name(os.path.join(month_dir, fname))
            self.moved_ops.append((target, path))
            shutil.move(path, target)
            if processed % 50 == 0:
                eng = getattr(self, 'english_mode', False)
                self.after(0, lambda n=fname, y=dt.year, m=readable_month(dt.month, eng): self._log(f"Movido: {n} → {y}/{m}"))
            if processed % max(1, total_files // 20) == 0 or processed == total_files:
                self.after(0, lambda v=int(processed/max(1,total_files)*100): self.progress.configure(value=v))
        self.after(0, lambda: self.progress.configure(value=100))
    def _dedupe_name(self, path):
        base, ext = os.path.splitext(path)
        i = 1
        while os.path.exists(path):
            path = f"{base} ({i}){ext}"
            i += 1
        return path

    def on_undo(self):
        # Solo afectar carpetas marcadas con ☑
        checked_folders = []
        if hasattr(self, '_tree_checked'):
            for iid, checked in self._tree_checked.items():
                if checked:
                    try:
                        folder = self.tree.item(iid)["values"][1]
                        checked_folders.append(folder)
                    except Exception:
                        pass
        if not checked_folders:
            # Ninguna marcada: mostrar aviso y no hacer nada
            popup = tk.Toplevel(self)
            eng_undo = getattr(self, 'english_mode', False)
            popup.title("Selection required" if eng_undo else "Selección requerida")
            popup.resizable(False, False)
            popup.transient(self)
            popup.grab_set()
            safe_icon(popup)
            frm = ttk.Frame(popup, padding=20)
            frm.pack()
            tk.Label(frm, text="First select the folders you want to undo by checking the checkbox (☑)." if eng_undo else "Primero selecciona las carpetas que deseas desorganizar marcando el checkbox (☑).",
                     font=("Segoe UI", 10), justify="center", wraplength=280).pack(pady=(0, 16))
            ttk.Button(frm, text="Got it" if eng_undo else "Entendido", command=popup.destroy).pack()
            center_window(popup, self)
            popup.deiconify()
            return
        target_folders = checked_folders
        n = len(target_folders)
        names = "\n".join(f"  • {os.path.basename(f)}" for f in target_folders)
        eng_undo2 = getattr(self, 'english_mode', False)
        confirm = self._show_confirm_dialog(
            msg=f"{'The organization of' if eng_undo2 else 'Se deshará la organización de'} {n} {'folder(s) will be undone:' if eng_undo2 else 'carpeta(s) seleccionada(s):'}\n{names}\n\n{'All files will be moved back to their root folder and empty folders will be removed.' if eng_undo2 else 'Todos los archivos se moverán a su carpeta raíz y se eliminarán las carpetas vacías.'}")
        if confirm == "cancel":
            return
        self._set_buttons_state(False)
        self.is_processing = True
        self._reset_counters()
        self.start_time = time.time()
        self.carpetas_procesadas_deshacer = 0
        self.total_carpetas_deshacer = len(target_folders)
        self.after(0, lambda: self._set_status("Undoing organization..." if getattr(self, 'english_mode', False) else "Deshaciendo organización..."))
        self.after(0, lambda: self.progress.configure(value=0))
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
                self.after(0, lambda f=os.path.basename(folder): self.lbl_cf_name.config(text=f))
                self.after(0, lambda fn=folder_norm, e2=getattr(self, 'english_mode', False): self.tree.set(self.folder_indexes.get(fn, ""), "status", "Undoing..." if e2 else "Deshaciendo..."))
                self.after(0, lambda: self.progress.configure(value=int((i+1) / total_folders * 80)))
                self._undo_organization_for_folder(folder, show_message=False)
                def _update_status_after_undo(f=folder, fn=folder_norm):
                    try:
                        cnt = count_all_files_including_organized(f)
                        e3 = getattr(self, 'english_mode', False)
                        self.tree.set(self.folder_indexes.get(fn, ""), "status", f"{cnt} {'files to organize' if e3 else 'archivos para organizar'}")
                    except Exception:
                        e3 = getattr(self, 'english_mode', False)
                        self.tree.set(self.folder_indexes.get(fn, ""), "status", "Unorganized" if e3 else "Desorganizada")
                self.after(0, _update_status_after_undo)
            self.after(0, lambda: self.progress.configure(value=90))
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
                            self.after(0, lambda v=progress: self.progress.configure(value=v))
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
            self.after(0, lambda: self.progress.configure(value=100))
            self.is_processing = False
            self.after(0, lambda: self.status_label.config(text=""))
            self.after(0, lambda: self.progress.config(value=0))
            self.after(0, lambda: self._set_buttons_state(True))
            self.after(0, self._update_undo_button_state)
            self.after(0, self._uncheck_all)
            self.after(0, lambda: messagebox.showinfo(APP_NAME, "All folders have been restored successfully!" if getattr(self, 'english_mode', False) else "¡Todo ha sido restaurado exitosamente!"))

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
        self.after(0, lambda: self.progress.configure(value=0))
        try:
            self.after(0, lambda: self._log("Restaurando archivos..."))
            for i, (new_path, old_path) in enumerate(reversed(ops_to_undo)):
                try:
                    if os.path.exists(new_path):
                        os.makedirs(os.path.dirname(old_path), exist_ok=True)
                        shutil.move(new_path, old_path)
                        if (i+1) % 50 == 0 or i == len(ops_to_undo) - 1:
                            progress = int((i+1) / max(1, len(ops_to_undo)) * 60)
                            self.after(0, lambda v=progress: self.progress.configure(value=v))
                except Exception as e:
                    self.after(0, lambda n=os.path.basename(new_path), err=e: self._log(f"Error restaurando {n}: {err}"))
            self.after(0, lambda: self._log(f"Restauración de {len(ops_to_undo)} archivos completada."))

            self.after(0, lambda: self.progress.configure(value=70))
            self.after(0, lambda: self.progress.configure(value=80))
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
                            self.after(0, lambda v=progress: self.progress.configure(value=v))
                except Exception:
                    pass
            self.moved_ops.clear()
            self.processed_roots.clear()
            self.created_dirs.clear()
            for f in self.queue:
                self.after(0, lambda root=f, e4=getattr(self, 'english_mode', False): self.tree.set(self.folder_indexes.get(root, ""), "status", "Undone" if e4 else "Deshecho"))
        finally:
            if hasattr(self, 'timer_id_undo'):
                self.after_cancel(self.timer_id_undo)
            self.after(0, self._refresh_counters)
            self.after(0, lambda: self.progress.configure(value=100))
            self.is_processing = False
            self.after(0, lambda: self.status_label.config(text=""))
            self.after(0, lambda: self.progress.config(value=0))
            self.after(0, lambda: self._set_buttons_state(True))
            self.after(0, self._update_undo_button_state)
            self.after(0, self._uncheck_all)
            self.after(0, lambda: messagebox.showinfo(APP_NAME, "All folders have been restored successfully!" if getattr(self, 'english_mode', False) else "¡Todo ha sido restaurado exitosamente!"))

    def _show_confirm_dialog(self, msg=None):
        popup = tk.Toplevel(self)
        popup.title("Confirm undo" if getattr(self, 'english_mode', False) else "Confirmar deshacer")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
        safe_icon(popup)
        eng = getattr(self, 'english_mode', False)
        frm = ttk.Frame(popup, padding=16)
        frm.pack()
        if msg is None:
            msg = ("All files in subfolders will be moved back\nto their root folder and empty folders will be removed.\n\n"
                   "This will let you reorganize them with another mode." if eng else
                   "Se moverán todos los archivos de las subcarpetas de vuelta "
                   "a su carpeta raíz y se eliminarán las carpetas vacías.\n\n"
                   "Esto te permitirá reorganizarlas con otro modo de organización.")
        tk.Label(frm, text=msg, font=("Segoe UI", 10), justify="center",
                 wraplength=380).pack(pady=(10, 20))
        result = tk.StringVar(value="cancel")

        def cont():
            result.set("undo")
            popup.destroy()

        btns = ttk.Frame(frm)
        btns.pack()
        ttk.Button(btns, text="Continue" if eng else "Continuar", command=cont).pack(side="left", padx=6)
        ttk.Button(btns, text="Cancel" if eng else "Cancelar", command=popup.destroy).pack(side="left", padx=6)
        center_window(popup, self)
        self.wait_window(popup)
        return result.get()

    def on_close(self):
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
    app = Click2FoldersApp()
    app.mainloop()
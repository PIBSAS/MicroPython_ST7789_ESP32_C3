"""
Sistema de Información para MicroPython
Obtiene SOLO los datos disponibles desde el propio MicroPython
"""

import os
import gc
import sys
import machine

# ============ CONSTANTES ============
RAM_ESTIMADA = {
    'ESP8266': 80 * 1024,
    'ESP32': 520 * 1024,
    'ESP32-S2': 320 * 1024,
    'ESP32-S3': 512 * 1024,
    'ESP32-C3': 400 * 1024,
    'ESP32-C6': 512 * 1024,
    'ESP32-H2': 320 * 1024,
}

# ============ FUNCIONES DE DETECCIÓN ============

def get_chip_type():
    """Detecta el tipo de chip"""
    try:
        uname = os.uname()
        machine_str = uname.machine.lower()
        
        if 'esp8266' in machine_str:
            return 'ESP8266'
        elif 'esp32-s3' in machine_str:
            return 'ESP32-S3'
        elif 'esp32-s2' in machine_str:
            return 'ESP32-S2'
        elif 'esp32-c3' in machine_str:
            return 'ESP32-C3'
        elif 'esp32-c6' in machine_str:
            return 'ESP32-C6'
        elif 'esp32-h2' in machine_str:
            return 'ESP32-H2'
        elif 'esp32' in machine_str:
            return 'ESP32'
        else:
            return 'Desconocido'
    except:
        return 'Desconocido'

def get_flash_size():
    """Obtiene el tamaño del flash"""
    # Método 1: esp.flash_size()
    try:
        import esp
        if hasattr(esp, 'flash_size'):
            size = esp.flash_size()
            if size and size > 0:
                return size
    except:
        pass
    
    # Método 2: machine.flash_size()
    try:
        if hasattr(machine, 'flash_size'):
            size = machine.flash_size()
            if size and size > 0:
                return size
    except:
        pass
    
    # Método 3: Estimar desde filesystem
    try:
        fs_info = os.statvfs('/')
        block_size = fs_info[0]
        total_blocks = fs_info[2]
        fs_total = total_blocks * block_size
        
        if fs_total > 0:
            # Estimar firmware (varía según chip)
            chip = get_chip_type()
            if chip == 'ESP8266':
                firmware = 1 * 1024 * 1024
            elif chip in ['ESP32-S3', 'ESP32-S2']:
                firmware = 2 * 1024 * 1024
            else:
                firmware = 1.5 * 1024 * 1024
            
            return fs_total + firmware
    except:
        pass
    
    return 0

def get_psram_size():
    """Detecta PSRAM"""
    # Método 1: esp.psram_size()
    try:
        import esp
        if hasattr(esp, 'psram_size'):
            size = esp.psram_size()
            if size and size > 0:
                return size
    except:
        pass
    
    # Método 2: esp32.psram_size()
    try:
        import esp32
        if hasattr(esp32, 'psram_size'):
            size = esp32.psram_size()
            if size and size > 0:
                return size
    except:
        pass
    
    # Método 3: machine.mem_info()
    try:
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        machine.mem_info()
        mem_output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        import re
        patterns = [
            r'PSRAM:\s*(\d+)\s*KB',
            r'SPIRAM:\s*(\d+)\s*KB',
            r'OCTAL PSRAM:\s*(\d+)\s*KB',
            r'PSRAM\s*\(.*?\):\s*(\d+)\s*KB',
            r'External RAM:\s*(\d+)\s*KB',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, mem_output, re.IGNORECASE)
            if match:
                size_kb = int(match.group(1))
                if size_kb > 0:
                    return size_kb * 1024
    except:
        pass
    
    return 0

def get_mac_address():
    """Obtiene la MAC address"""
    try:
        import ubinascii
        mac_bytes = machine.unique_id()
        mac_hex = ubinascii.hexlify(mac_bytes).decode().upper()
        mac_formatted = ':'.join(mac_hex[i:i+2] for i in range(0, 12, 2))
        return mac_hex, mac_formatted
    except:
        return None, None

def get_flash_id():
    """Obtiene el ID del flash"""
    try:
        import esp
        if hasattr(esp, 'flash_id'):
            return hex(esp.flash_id())
    except:
        pass
    return None

def get_filesystem_info():
    """Obtiene información del sistema de archivos"""
    try:
        fs_info = os.statvfs('/')
        block_size = fs_info[0]
        total_blocks = fs_info[2]
        free_blocks = fs_info[3]
        used_blocks = total_blocks - free_blocks
        
        return {
            'total': total_blocks * block_size,
            'used': used_blocks * block_size,
            'free': free_blocks * block_size,
            'usage': (used_blocks / total_blocks * 100) if total_blocks > 0 else 0
        }
    except:
        return {
            'total': 0,
            'used': 0,
            'free': 0,
            'usage': 0
        }

def get_heap_info():
    """Obtiene información del heap"""
    gc.collect()
    used = gc.mem_alloc()
    free = gc.mem_free()
    return {
        'total': used + free,
        'used': used,
        'free': free,
        'usage': (used / (used + free) * 100) if (used + free) > 0 else 0
    }

def get_stack_info():
    """Obtiene información del stack"""
    try:
        import micropython
        used = micropython.stack_use()
        total = 15360  # Valor típico para ESP32
        return {
            'total': total,
            'used': used,
            'free': total - used,
            'usage': (used / total * 100) if total > 0 else 0
        }
    except:
        return {
            'total': 0,
            'used': 0,
            'free': 0,
            'usage': 0
        }

def get_uname():
    """Obtiene información del sistema"""
    try:
        uname = os.uname()
        return {
            'sysname': uname.sysname,
            'nodename': uname.nodename,
            'release': uname.release,
            'version': uname.version,
            'machine': uname.machine
        }
    except:
        return {
            'sysname': 'Unknown',
            'nodename': 'Unknown',
            'release': 'Unknown',
            'version': 'Unknown',
            'machine': 'Unknown'
        }

# ============ FUNCIONES DE FORMATO ============

def format_bytes(bytes_value):
    """Formatea bytes a representación legible"""
    if bytes_value == 0 or bytes_value < 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB']
    unit_index = 0
    
    while bytes_value >= 1024 and unit_index < len(units) - 1:
        bytes_value /= 1024.0
        unit_index += 1
    
    return f"{bytes_value:.2f} {units[unit_index]}"

def print_bar(percentage, width=25, char='█'):
    """Imprime una barra de progreso"""
    percentage = max(0, min(100, percentage))
    filled = int(width * percentage / 100)
    bar = char * filled + '░' * (width - filled)
    return f"[{bar}] {percentage:.1f}%"

# ============ FUNCIÓN PRINCIPAL ============

def get_all_info():
    """Recopila TODA la información disponible desde MicroPython"""
    chip = get_chip_type()
    flash_total = get_flash_size()
    psram = get_psram_size()
    fs = get_filesystem_info()
    heap = get_heap_info()
    stack = get_stack_info()
    uname = get_uname()
    mac_hex, mac_formatted = get_mac_address()
    flash_id = get_flash_id()
    
    # RAM interna estimada
    ram_interna = RAM_ESTIMADA.get(chip, 0)
    
    # Calcular firmware
    bootloader = 32 * 1024
    partition_table = 8 * 1024
    firmware = flash_total - fs['total'] - bootloader - partition_table
    if firmware < 0:
        firmware = 0
    
    # PSRAM como heap
    psram_en_heap = False
    psram_size = psram
    if psram == 0 and heap['total'] > ram_interna * 1.2:
        psram_size = heap['total'] - ram_interna
        psram_en_heap = True
    
    return {
        # Sistema
        'chip_type': chip,
        'sysname': uname['sysname'],
        'version': uname['version'],
        'machine': uname['machine'],
        'platform': sys.platform,
        'python_version': sys.version,
        'micropython_version': '.'.join(map(str, sys.implementation.version)),
        
        # Chip
        'mac': mac_formatted,
        'flash_id': flash_id,
        
        # Flash
        'flash_total': flash_total,
        'bootloader': bootloader,
        'partition_table': partition_table,
        'firmware_size': firmware,
        'fs_total': fs['total'],
        'fs_used': fs['used'],
        'fs_free': fs['free'],
        'fs_usage': fs['usage'],
        
        # PSRAM
        'psram_detected': psram_size > 0,
        'psram_size': psram_size,
        'psram_as_heap': psram_en_heap,
        
        # Heap
        'ram_interna_estimada': ram_interna,
        'heap_total': heap['total'],
        'heap_used': heap['used'],
        'heap_free': heap['free'],
        'heap_usage': heap['usage'],
        
        # Stack
        'stack_total': stack['total'],
        'stack_used': stack['used'],
        'stack_free': stack['free'],
        'stack_usage': stack['usage'],
    }

def display_info():
    """Muestra toda la información disponible"""
    info = get_all_info()
    
    print("=" * 80)
    print("🔍 INFORMACIÓN DEL SISTEMA MICROPYTHON")
    print("=" * 80)
    
    # 1. Sistema
    print("\n📱 SISTEMA:")
    print(f"  Sistema        : {info['sysname']}")
    print(f"  Versión        : {info['version']}")
    print(f"  Máquina        : {info['machine']}")
    print(f"  Plataforma     : {info['platform']}")
    print(f"  MicroPython    : v{info['micropython_version']}")
    print(f"  Python         : {info['python_version']}")
    
    # 2. Chip
    print("\n🔹 CHIP:")
    print(f"  Tipo           : {info['chip_type']}")
    if info['mac']:
        print(f"  MAC Address    : {info['mac']}")
    if info['flash_id']:
        print(f"  Flash ID       : {info['flash_id']}")
    
    # 3. Flash
    print("\n💾 FLASH:")
    print(f"  Total          : {format_bytes(info['flash_total'])}")
    print(f"  ├─ Bootloader  : {format_bytes(info['bootloader'])}")
    print(f"  ├─ Partition   : {format_bytes(info['partition_table'])}")
    print(f"  ├─ Firmware    : {format_bytes(info['firmware_size'])}")
    print(f"  └─ Filesystem  : {format_bytes(info['fs_total'])}")
    print(f"     ├─ Usado    : {format_bytes(info['fs_used'])}")
    print(f"     ├─ Libre    : {format_bytes(info['fs_free'])}")
    print(f"     └─ Uso      : {print_bar(info['fs_usage'], 20)}")
    
    # 4. PSRAM
    print("\n🧠 PSRAM:")
    if info['psram_detected']:
        print(f"  ✅ Detectada   : {format_bytes(info['psram_size'])}")
        if info['psram_as_heap']:
            print(f"  Configuración : Heap principal")
    else:
        print(f"  ❌ No detectada")
        if info['ram_interna_estimada'] > 0:
            print(f"  RAM Interna    : {format_bytes(info['ram_interna_estimada'])}")
    
    # 5. Heap
    print("\n📊 HEAP:")
    print(f"  Total          : {format_bytes(info['heap_total'])}")
    print(f"  Usado          : {format_bytes(info['heap_used'])}")
    print(f"  Libre          : {format_bytes(info['heap_free'])}")
    print(f"  Uso            : {print_bar(info['heap_usage'], 20)}")
    
    # Desglose del heap
    if info['psram_detected'] and info['ram_interna_estimada'] > 0:
        ram_actual = min(info['ram_interna_estimada'], info['heap_total'])
        psram_actual = max(0, info['heap_total'] - info['ram_interna_estimada'])
        print(f"\n  Desglose Heap:")
        print(f"    RAM Interna : {format_bytes(ram_actual)}")
        print(f"    PSRAM       : {format_bytes(psram_actual)}")
    
    # 6. Stack
    if info['stack_total'] > 0:
        print("\n📚 STACK:")
        print(f"  Total          : {format_bytes(info['stack_total'])}")
        print(f"  Usado          : {format_bytes(info['stack_used'])}")
        print(f"  Libre          : {format_bytes(info['stack_free'])}")
        print(f"  Uso            : {print_bar(info['stack_usage'], 20)}")
    
    # 7. Resumen
    print("\n📈 RESUMEN:")
    print(f"  Flash + PSRAM  : {format_bytes(info['flash_total'] + info['psram_size'])}")
    print(f"  Flash          : {format_bytes(info['flash_total'])}")
    if info['psram_detected']:
        print(f"  PSRAM          : {format_bytes(info['psram_size'])}")
    
    # 8. Garbage Collector
    print("\n♻️  GARBAGE COLLECTOR:")
    gc.collect()
    print(f"  Memoria libre  : {format_bytes(gc.mem_free())}")
    print(f"  Objetos        : {gc.mem_alloc()}")
    
    print("\n" + "=" * 80)

def quick_info():
    """Versión rápida y compacta"""
    info = get_all_info()
    
    print("\n⚡ INFO RÁPIDA")
    print("-" * 50)
    print(f"Chip        : {info['chip_type']}")
    print(f"Flash       : {format_bytes(info['flash_total'])}")
    print(f"Firmware    : {format_bytes(info['firmware_size'])}")
    print(f"Filesystem  : {format_bytes(info['fs_total'])}")
    print(f"PSRAM       : {format_bytes(info['psram_size']) if info['psram_detected'] else 'No'}")
    print(f"Heap        : {format_bytes(info['heap_total'])}")
    print(f"Stack       : {format_bytes(info['stack_total'])}")
    if info['mac']:
        print(f"MAC         : {info['mac']}")
    print("-" * 50)

# ============ EJECUCIÓN ============

if __name__ == "__main__":
    display_info()
    quick_info()
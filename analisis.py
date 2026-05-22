import math
import csv
import os
import sys
import urllib.request
import urllib.error

# --- CONFIGURACIÓN DE ARCHIVO Y DESCARGA ---
ARCHIVO_LOCAL = "BASE DE DATOS U.K.csv"
# Aquí colocarás el link directo de GitHub (Raw) o el link de descarga directa
URL_DESCARGA = "https://raw.githubusercontent.com/TU_USUARIO/TU_REPOSITORIO/main/BASE_DE_DATOS_U.K.csv" 

def asegurar_archivo():
    """Verifica si el archivo existe; si no, lo descarga automáticamente."""
    if os.path.exists(ARCHIVO_LOCAL):
        print(f"✓ Archivo '{ARCHIVO_LOCAL}' encontrado localmente.")
    else:
        print(f"⚠ Archivo no encontrado. Iniciando descarga automática desde la fuente...")
        try:
            urllib.request.urlretrieve(URL_DESCARGA, ARCHIVO_LOCAL)
            print(f"✓ ÉXITO: Archivo descargado y guardado como '{ARCHIVO_LOCAL}'.")
        except urllib.error.URLError as e:
            print(f"🛑 ERROR CRÍTICO: No se pudo descargar la base de datos.")
            print(f"Detalle del error: {e.reason}")
            sys.exit()
        except Exception as e:
            print(f"🛑 ERROR CRÍTICO INESPERADO: {e}")
            sys.exit()

def cargar_datos_reales():
    asegurar_archivo()
    print("Procesando base de datos...")
    datos_completos = []
        
    with open(ARCHIVO_LOCAL, mode='r', encoding='utf-8-sig') as f:
        lector = csv.DictReader(f)
        for fila in lector:
            try:
                valor_str = fila.get('OBS_VALUE')
                anio_str = fila.get('TIME_PERIOD')
                
                if valor_str and valor_str.strip():
                    valor = float(valor_str)
                    anio = int(anio_str) if anio_str and anio_str.strip().isdigit() else 0
                    datos_completos.append({'valor': valor, 'anio': anio})
            except Exception:
                continue
                
    if not datos_completos:
        print("🛑 ERROR CRÍTICO: El archivo existe pero no contiene datos válidos en 'OBS_VALUE'.")
        sys.exit()

    print(f"✓ ÉXITO: {len(datos_completos)} registros reales extraídos para el análisis.")
    return datos_completos

# --- 1. PROCESAMIENTO DE DATOS Y EXTRACCIÓN ---
datos_crudos = cargar_datos_reales()
datos = sorted([d['valor'] for d in datos_crudos])
n = len(datos)

print("\n" + "="*60)
print("       TRABAJO FINAL: ANÁLISIS ESTADÍSTICO (OECD GBR)       ")
print("="*60)

# --- 2. Medidas de Tendencia Central ---
print("\n2. Medidas de Tendencia Central")

# 2.4, 2.5, 2.6 (No Agrupados)
media_no = sum(datos) / n
mediana_no = (datos[n//2-1] + datos[n//2])/2 if n%2==0 else datos[n//2]

# Moda real optimizada y de PRECISIÓN ABSOLUTA (Multimodal)
conteo_frecuencias = {}
for numero in datos:
    conteo_frecuencias[numero] = conteo_frecuencias.get(numero, 0) + 1

frec_max = max(conteo_frecuencias.values())
modas = [num for num, frec in conteo_frecuencias.items() if frec == frec_max]

if len(modas) == 1:
    moda_no = f"{modas[0]}"
elif len(modas) > 10:
    moda_no = f"{modas[:5]}... y {len(modas)-5} más (Multimodal)"
else:
    moda_no = f"{', '.join(map(str, modas))} (Multimodal)"

# 2.1, 2.2, 2.3 (Agrupados - CORRECCIÓN DE PRECISIÓN ESTADÍSTICA)
min_v, max_v = datos[0], datos[-1]
rango_t = max_v - min_v if max_v - min_v > 0 else 1

# REGLA DE STURGES para definir 'k' exacto
k = math.ceil(1 + 3.322 * math.log10(n)) if n > 0 else 5
ancho = rango_t / k
limites = [min_v + i*ancho for i in range(k+1)]
marcas_clase = [(limites[i] + limites[i+1])/2 for i in range(k)]

frecuencias = [len([x for x in datos if limites[i] <= x < limites[i+1]]) for i in range(k-1)]
frecuencias.append(len([x for x in datos if limites[k-1] <= x <= limites[k]])) 

# Media Agrupada
media_agr = sum(m * f for m, f in zip(marcas_clase, frecuencias)) / n

# Moda Agrupada (Fórmula formal con deltas)
idx_moda = frecuencias.index(max(frecuencias))
L_mo = limites[idx_moda]
d1 = frecuencias[idx_moda] - (frecuencias[idx_moda-1] if idx_moda > 0 else 0)
d2 = frecuencias[idx_moda] - (frecuencias[idx_moda+1] if idx_moda < k-1 else 0)
moda_agr = L_mo + (d1 / (d1 + d2)) * ancho if (d1 + d2) > 0 else marcas_clase[idx_moda]

# Mediana Agrupada (Fórmula formal por interpolación)
posicion_mediana = n / 2
frec_acumulada = 0
idx_mediana = 0
for i, f in enumerate(frecuencias):
    frec_acumulada += f
    if frec_acumulada >= posicion_mediana:
        idx_mediana = i
        break
L_me = limites[idx_mediana]
F_anterior = frec_acumulada - frecuencias[idx_mediana]
f_me = frecuencias[idx_mediana]
mediana_agr = L_me + ((posicion_mediana - F_anterior) / f_me) * ancho if f_me > 0 else marcas_clase[idx_mediana]

print(f"2.1. Datos Agrupados - Moda (Fórmula formal): {moda_agr:.2f}")
print(f"2.2. Datos Agrupados - Mediana (Interpolación): {mediana_agr:.2f}")
print(f"2.3. Datos Agrupados - Media (Sturges k={k}): {media_agr:.2f}")
print(f"2.4. Datos No Agrupados - Moda: {moda_no}")
print(f"2.5. Datos No Agrupados - Mediana: {mediana_no}")
print(f"2.6. Datos No Agrupados - Media: {media_no:.2f}")

# --- 3. Medidas de Dispersión ---
print("\n3. Medidas de Dispersión")
rango = max_v - min_v
q1, q3 = datos[int(n*0.25)], datos[int(n*0.75)]
riq = q3 - q1
varianza = sum((x - media_no)**2 for x in datos) / (n - 1) if n > 1 else 0
desv_std = math.sqrt(varianza)
desv_media = sum(abs(x - media_no) for x in datos) / n

print(f"3.1. Rango: {rango}")
print(f"3.2. Rango intercuartílico: {riq}")
print(f"3.3. Varianza: {varianza:.2f}")
print(f"3.4. Desviación Estándar: {desv_std:.2f}")
print(f"3.5. Desviación Media: {desv_media:.2f}")

# --- 4. Introducción Probabilidad ---
print("\n4. Introducción Probabilidad")
anios_unicos = sorted(list(set([d['anio'] for d in datos_crudos if d['anio'] > 0])))
anio_medio = anios_unicos[len(anios_unicos)//2] if anios_unicos else 0

cant_A = len([d for d in datos_crudos if d['valor'] > media_no])
cant_B = len([d for d in datos_crudos if d['anio'] >= anio_medio])
cant_A_y_B = len([d for d in datos_crudos if d['valor'] > media_no and d['anio'] >= anio_medio])

p_a = cant_A / n
p_b = cant_B / n if n > 0 else 1
p_a_y_b = cant_A_y_B / n
p_b_a = p_a_y_b / p_a if p_a > 0 else 0 

print("4.1. Diagrama de Venn: [Cálculo basado en Conjunto A: Valores > Media]")
print(f"4.2. Conteo: {n} observaciones procesadas")
print(f"4.3. Combinación (n=10, r=3): {math.comb(10, 3)}")
print(f"4.4. Permutación (n=10, r=3): {math.perm(10, 3)}")
print(f"4.5. Probabilidad Condicional P(B|A): {p_b_a:.4f}")
print(f"4.6. Teorema de Bayes P(A|B): {((p_b_a * p_a) / p_b) if p_b > 0 else 0:.4f}")

# --- 5. Distribución de Probabilidad con VAD ---
print("\n5. Distribución de Probabilidad con VAD")
binom = math.comb(10, 5) * (p_a**5) * ((1 - p_a)**5) if 0 <= p_a <= 1 else 0
lam = media_no / 1000 if media_no > 1000 else media_no
try:
    poisson = (math.exp(-lam) * (lam**int(lam))) / math.factorial(int(lam))
except OverflowError:
    poisson = 0.0 
hiper = (math.comb(10, 2) * math.comb(10, 3)) / math.comb(20, 5)

print(f"5.1. Distribución Binomial: {binom:.6f}")
print(f"5.2. Distribución Poisson: {poisson:.6f}")
print(f"5.3. Distribución Hipergeométrica: {hiper:.4f}")

# --- 6. Distribución de Probabilidad con VAC ---
print("\n6. Distribución de Probabilidad con VAC")
def norm_pdf(x, m, s): 
    if s == 0: return 0
    return (1/(s*math.sqrt(2*math.pi))) * math.exp(-0.5*((x-m)/s)**2)

print(f"6.1. Distribución Normal (en la media): {norm_pdf(media_no, media_no, desv_std):.10f}")
print(f"6.2. Distribución Normal Estándar (Z para el primer dato): {((datos[0]-media_no)/desv_std) if desv_std > 0 else 0:.4f}")

# --- 7. Índices ---
print("\n7. Índices")
if len(anios_unicos) >= 2:
    anio_base = anios_unicos[0]
    anio_actual = anios_unicos[-1]
    
    datos_anio_base = [d['valor'] for d in datos_crudos if d['anio'] == anio_base]
    datos_anio_actual = [d['valor'] for d in datos_crudos if d['anio'] == anio_actual]
    
    p0 = sum(datos_anio_base) / len(datos_anio_base) if datos_anio_base else 1
    p1 = sum(datos_anio_actual) / len(datos_anio_actual) if datos_anio_actual else 1
    q0 = len(datos_anio_base) if datos_anio_base else 1
    q1 = len(datos_anio_actual) if datos_anio_actual else 1
else:
    p0, p1 = datos[0], datos[-1]
    q0, q1 = 1, 1 

laspe = (p1 * q0) / (p0 * q0) * 100 if (p0 * q0) > 0 else 0
paasc = (p1 * q1) / (p0 * q1) * 100 if (p0 * q1) > 0 else 0
fisher = math.sqrt(laspe * paasc)

print(f"7.1. Índice Paasche: {paasc:.2f}")
print(f"7.2. Índice Laspeyrés: {laspe:.2f}")
print(f"7.3. Índice Fisher: {fisher:.2f}")

print("\n" + "="*60)
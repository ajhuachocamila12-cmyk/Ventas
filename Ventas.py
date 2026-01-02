"""Sistema automático de control de ventas de buzos (CLI simple)

Características:
- Registro de venta: fecha/hora, tipo (hombre/mujer/niño), color, cantidad, precio unitario
- Costos fijos por tipo: Hombre 35, Mujer 30, Niño 22
- Cálculos automáticos: total vendido, inversión recuperada, ganancia/pérdida
- Alerta cuando precio unitario < costo
- Resúmenes diarios y semanales (total vendido, ganancia acumulada, tipo más rentable)
- Persistencia en `ventas.json`

Ejecutar: python ventas_buzos.py
"""

import json
import csv
from datetime import datetime, date
from collections import defaultdict
import os

DATA_FILE = 'ventas.json'
COSTS = {'hombre': 35.0, 'mujer': 30.0, 'niño': 22.0}
VALID_TYPES = set(COSTS.keys())


def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_data(sales):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(sales, f, ensure_ascii=False, indent=2)


def parse_datetime(s):
    if s.strip().lower() in ('now', ''):
        return datetime.now()
    for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            d = datetime.strptime(s, fmt)
            if fmt == '%Y-%m-%d':
                # default time
                return datetime(d.year, d.month, d.day, 0, 0)
            return d
        except ValueError:
            continue
    raise ValueError('Formato de fecha inválido. Use "YYYY-MM-DD HH:MM" o "now"')


def compute_fields(tipo, cantidad, precio_unitario):
    costo_unit = COSTS[tipo]
    total = cantidad * precio_unitario
    inversion = cantidad * costo_unit
    ganancia = total - inversion
    alert = precio_unitario < costo_unit
    return costo_unit, round(total, 2), round(inversion, 2), round(ganancia, 2), alert


def add_sale(sales):
    try:
        s = input('Fecha y hora (YYYY-MM-DD HH:MM o "now"): ').strip()
        dt = parse_datetime(s)
    except Exception as e:
        print('Error:', e)
        return

    t = input('Tipo (hombre/mujer/niño): ').strip().lower()
    if t not in VALID_TYPES:
        print('Tipo inválido. Debe ser uno de:', ', '.join(VALID_TYPES))
        return

    color = input('Color: ').strip()
    try:
        cantidad = int(input('Cantidad vendida: ').strip())
        if cantidad <= 0:
            print('Cantidad debe ser positiva')
            return
    except ValueError:
        print('Cantidad inválida')
        return

    try:
        precio_unitario = float(input('Precio de venta unitario (Bs): ').strip())
        if precio_unitario < 0:
            print('Precio no puede ser negativo')
            return
    except ValueError:
        print('Precio inválido')
        return

    costo_unit, total, inversion, ganancia, alert = compute_fields(t, cantidad, precio_unitario)
    record = {
        'datetime': dt.strftime('%Y-%m-%d %H:%M:%S'),
        'tipo': t,
        'color': color,
        'cantidad': cantidad,
        'precio_unitario': round(precio_unitario, 2),
        'costo_unitario': costo_unit,
        'total': total,
        'inversion_recuperada': inversion,
        'ganancia': ganancia,
        'alerta_precio': alert
    }
    sales.append(record)
    save_data(sales)

    print('\nVenta registrada:')
    print(json.dumps(record, ensure_ascii=False, indent=2))
    if alert:
        print('\n⚠️  Alerta: el precio unitario es menor que el costo (posible pérdida).')


def list_sales(sales):
    if not sales:
        print('No hay ventas registradas')
        return
    for i, s in enumerate(sales, 1):
        print(f"{i}. {s['datetime']} - {s['tipo']} - {s['color']} - x{s['cantidad']} - Bs{s['precio_unitario']} -> Ganancia: Bs{s['ganancia']}")


def daily_summary(sales, dt: date):
    total_vendido = 0.0
    ganancia_acum = 0.0
    tipo_ganancias = defaultdict(float)
    for s in sales:
        d = datetime.strptime(s['datetime'], '%Y-%m-%d %H:%M:%S').date()
        if d == dt:
            total_vendido += s['total']
            ganancia_acum += s['ganancia']
            tipo_ganancias[s['tipo']] += s['ganancia']
    tipo_mas_rentable = None
    if tipo_ganancias:
        tipo_mas_rentable = max(tipo_ganancias, key=lambda k: tipo_ganancias[k])
    return round(total_vendido, 2), round(ganancia_acum, 2), tipo_mas_rentable, dict(tipo_ganancias)


def weekly_summary(sales, year, week):
    # ISO week (year, week)
    total_vendido = 0.0
    ganancia_acum = 0.0
    tipo_ganancias = defaultdict(float)
    for s in sales:
        dt = datetime.strptime(s['datetime'], '%Y-%m-%d %H:%M:%S')
        y, w, _ = dt.isocalendar()
        if y == year and w == week:
            total_vendido += s['total']
            ganancia_acum += s['ganancia']
            tipo_ganancias[s['tipo']] += s['ganancia']
    tipo_mas_rentable = None
    if tipo_ganancias:
        tipo_mas_rentable = max(tipo_ganancias, key=lambda k: tipo_ganancias[k])
    return round(total_vendido, 2), round(ganancia_acum, 2), tipo_mas_rentable, dict(tipo_ganancias)


def export_csv(sales, filename='ventas_export.csv'):
    if not sales:
        print('No hay datos para exportar')
        return
    keys = ['datetime', 'tipo', 'color', 'cantidad', 'precio_unitario', 'costo_unitario', 'total', 'inversion_recuperada', 'ganancia', 'alerta_precio']
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for s in sales:
            w.writerow({k: s.get(k, '') for k in keys})
    print(f'Exportado a {filename}')


def demo_data(sales):
    # Genera datos de ejemplo
    ejemplo = [
        {'datetime': '2025-12-29 10:15:00', 'tipo': 'hombre', 'color': 'negro', 'cantidad': 3, 'precio_unitario': 40.0},
        {'datetime': '2025-12-29 12:30:00', 'tipo': 'mujer', 'color': 'rojo', 'cantidad': 2, 'precio_unitario': 28.0},
        {'datetime': '2025-12-28 09:00:00', 'tipo': 'niño', 'color': 'azul', 'cantidad': 4, 'precio_unitario': 25.0},
        {'datetime': '2025-12-30 14:00:00', 'tipo': 'hombre', 'color': 'gris', 'cantidad': 1, 'precio_unitario': 30.0},
    ]
    for e in ejemplo:
        costo_unit, total, inversion, ganancia, alert = compute_fields(e['tipo'], e['cantidad'], e['precio_unitario'])
        e.update({'costo_unitario': costo_unit, 'total': total, 'inversion_recuperada': inversion, 'ganancia': ganancia, 'alerta_precio': alert})
        sales.append(e)
    save_data(sales)
    print('Datos de ejemplo añadidos')


def main():
    sales = load_data()
    while True:
        print('\n=== Control de Ventas de Buzos ===')
        print('1) Registrar venta')
        print('2) Resumen diario')
        print('3) Resumen semanal (ISO week)')
        print('4) Listar ventas')
        print('5) Exportar CSV')
        print('6) Añadir datos de ejemplo')
        print('0) Salir')
        o = input('> ').strip()
        if o == '1':
            add_sale(sales)
        elif o == '2':
            s = input('Fecha (YYYY-MM-DD, dejar vacío = hoy): ').strip()
            if s == '':
                d = date.today()
            else:
                try:
                    d = datetime.strptime(s, '%Y-%m-%d').date()
                except ValueError:
                    print('Fecha inválida')
                    continue
            total, ganancia, tipo_mas, by_type = daily_summary(sales, d)
            print(f'Fecha: {d} — Total vendido: Bs{total} — Ganancia acumulada: Bs{ganancia} — Tipo más rentable: {tipo_mas or "n/a"}')
            if by_type:
                print('Ganancia por tipo:', by_type)
        elif o == '3':
            s = input('Ingrese año y semana (YYYY-WW) o una fecha (YYYY-MM-DD): ').strip()
            try:
                if '-' in s and len(s.split('-')[-1]) == 2 and s.count('-') == 1:
                    y, w = s.split('-')
                    year = int(y)
                    week = int(w)
                else:
                    dt = datetime.strptime(s, '%Y-%m-%d')
                    year, week, _ = dt.isocalendar()
                total, ganancia, tipo_mas, by_type = weekly_summary(sales, year, week)
                print(f'Año {year} Semana {week} — Total vendido: Bs{total} — Ganancia acumulada: Bs{ganancia} — Tipo más rentable: {tipo_mas or "n/a"}')
                if by_type:
                    print('Ganancia por tipo:', by_type)
            except Exception as e:
                print('Entrada inválida:', e)
        elif o == '4':
            list_sales(sales)
        elif o == '5':
            fn = input('Nombre de archivo (ENTER para ventas_export.csv): ').strip() or 'ventas_export.csv'
            export_csv(sales, fn)
        elif o == '6':
            demo_data(sales)
        elif o == '0':
            print('Saliendo...')
            break
        else:
            print('Opción inválida')


if __name__ == '__main__':
    main()
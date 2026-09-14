# Idempotente: patentes argentinas válidas para ARBA (Mercosur AA 123 BB / vieja AAA 123)
# y patente de acoplado en los camiones demo, sin recargar el demo XML (que pisaría
# estados de órdenes y viajes).
# Uso:
#   docker exec -i odoo_semillero-verticalizacion sh -c 'odoo shell \
#     --db_host=postgres --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
#     -d semillero_demo --no-http' < scripts/fix_demo_plates.py

print('=== SeedSuite demo plates: start ===')

# xmlid -> (patente, patente acoplado | None)
BY_XMLID = {
    # Autos demo del módulo fleet
    'fleet.vehicle_1': ('AC 205 KF', None),
    'fleet.vehicle_2': ('AD 404 SY', None),
    'fleet.vehicle_3': ('AE 001 BW', None),
    'fleet.vehicle_4': ('AF 001 AU', None),
    'fleet.vehicle_5': ('AE 101 MR', None),
    # seed_weighing: formato viejo, ya válido; sólo acoplado
    'seed_weighing.vehicle_aef123': ('AEF 123', 'WUP 318'),
    'seed_weighing.vehicle_bcd456': ('BCD 456', 'RDX 745'),
    'seed_weighing.vehicle_cgh789': ('CGH 789', 'TLM 219'),
    'seed_weighing.vehicle_dkl012': ('DKL 012', 'SKB 563'),
    'seed_weighing.vehicle_emn345': ('EMN 345', 'VNZ 871'),
    'seed_weighing.vehicle_fpq678': ('FPQ 678', 'PHJ 134'),
    # seed_logistics
    'seed_logistics.demo_truck_1': ('AD 214 KM', 'AC 903 LP'),
    'seed_logistics.demo_truck_2': ('AE 587 JR', 'AC 118 TN'),
    'seed_logistics.demo_truck_3': ('AF 032 HS', 'AB 764 QW'),
    'seed_logistics.demo_truck_4': ('AE 941 PB', 'AD 350 FX'),
    'seed_logistics.demo_truck_disabled': ('AB 406 ZC', None),
    'seed_logistics.demo_norte_truck_1': ('AF 318 NT', 'AC 552 RN'),
    'seed_logistics.demo_norte_truck_2': ('AE 229 GD', 'AD 671 MV'),
    'seed_logistics.demo_norte_truck_3': ('AD 845 WL', 'AB 297 KC'),
    'seed_logistics.demo_norte_truck_4': ('AF 176 BR', 'AC 430 JS'),
    'seed_logistics.demo_pampa_truck_1': ('AE 663 PZ', 'AD 108 HT'),
    'seed_logistics.demo_pampa_truck_2': ('AF 504 KX', 'AC 786 NB'),
    'seed_logistics.demo_pampa_truck_3': ('AD 917 RC', 'AB 541 LM'),
    'seed_logistics.demo_sur_truck_1': ('AE 382 SV', 'AD 925 GP'),
    'seed_logistics.demo_sur_truck_2': ('AF 741 TD', 'AC 264 WK'),
    'seed_logistics.demo_sur_truck_3': ('AD 059 MJ', 'AB 812 FR'),
}
# Camiones del loader sin xmlid (load_demo_transport.py)
BY_PLATE = {
    'DEMO-T01': ('AF 611 DT', 'AD 377 KV'),
    'DEMO-T02': ('AE 802 HM', 'AC 649 PW'),
    'DEMO-T03': ('AD 473 RS', 'AB 185 TJ'),
    'DEMO-T04': ('AF 290 LG', 'AC 936 BX'),
    'DEMO-T05': ('AE 158 NF', 'AD 724 QH'),
    'DEMO-T06': ('AD 606 CZ', 'AB 453 WM'),
}
COT_PLATES = {'AA111AA': 'AD 214 KM', 'BB222BB': 'AE 587 JR', 'CC333CC': 'AF 032 HS'}

Vehicle = env['fleet.vehicle'].with_context(active_test=False)
has_trailer = 'x_trailer_plate' in Vehicle._fields


def apply(vehicle, plate, trailer):
    old = vehicle.license_plate
    vals = {'license_plate': plate, 'trailer_hook': bool(trailer)}
    if has_trailer:
        vals['x_trailer_plate'] = trailer or False
    vehicle.write(vals)
    print('camion: %-10s -> %-10s acoplado=%s' % (old, plate, trailer or '-'))


for xmlid, (plate, trailer) in BY_XMLID.items():
    vehicle = env.ref(xmlid, raise_if_not_found=False)
    if vehicle:
        apply(vehicle, plate, trailer)
for legacy, (plate, trailer) in BY_PLATE.items():
    for vehicle in Vehicle.search([('license_plate', 'in', [legacy, plate])]):
        apply(vehicle, plate, trailer)

if 'seed.cot' in env:
    for old, new in COT_PLATES.items():
        cots = env['seed.cot'].search([('vehicle_plate', '=', old)])
        cots.write({'vehicle_plate': new})
        if cots:
            print('cot: %s -> %s (%d)' % (old, new, len(cots)))

env.cr.commit()
print('=== SeedSuite demo plates: done ===')

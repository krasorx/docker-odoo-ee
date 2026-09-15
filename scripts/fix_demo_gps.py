# Idempotente: deja lista la demo de GPS en una base que YA tenía seed_logistics
# instalado. Los archivos de demo se cargan con noupdate=True, así que estos dos
# arreglos no llegan por XML a una base existente:
#   1. el pedido de transporte demo necesita orden de cosecha (campo + coordenadas),
#   2. el cron simulador quedó inactivo porque antes vivía en data/.
# Una instalación nueva no necesita este script.
# Uso:
#   docker exec -i odoo_semillero-verticalizacion sh -c 'odoo shell \
#     --db_host=postgres --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
#     -d semillero_demo --no-http' < scripts/fix_demo_gps.py

print('=== SeedSuite demo GPS: start ===')

order = env.ref('seed_logistics.demo_transport_order', raise_if_not_found=False)
harvest = env.ref('seed_field.harvest_gut01_1', raise_if_not_found=False)
if order and harvest and not order.harvest_order_id:
    order.harvest_order_id = harvest
    print('pedido %s -> cosecha %s (campo %s)' % (
        order.name, harvest.name, order.field_id.name))
elif order:
    print('pedido %s ya tiene cosecha: %s' % (order.name, order.harvest_order_id.name or '-'))

cron = env.ref('seed_logistics.cron_simulate_vehicle_positions', raise_if_not_found=False)
if cron and not cron.active:
    cron.active = True
    print('cron simulador activado')
elif cron:
    print('cron simulador ya activo')
else:
    print('cron simulador no existe (base sin datos de demo)')

Position = env['seed.vehicle.position']
if not Position.search_count([]):
    for _ in range(6):
        Position._cron_simulate_positions()
    print('posiciones sembradas: %d' % Position.search_count([]))
else:
    print('ya hay %d posiciones' % Position.search_count([]))

env.cr.commit()
print('=== SeedSuite demo GPS: done ===')

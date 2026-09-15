# Idempotente: deja usable el perfil Productor en una base que YA tenía la demo
# instalada. Los archivos de demo se cargan con noupdate=True, así que ni el
# <function> que vincula el productor con su contacto ni el grupo agregado
# después llegan por XML a una base existente.
# Una instalación nueva no necesita este script.
# Uso:
#   docker exec -i odoo_semillero-verticalizacion sh -c 'odoo shell \
#     --db_host=postgres --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
#     -d semillero_demo --no-http' < scripts/fix_demo_grower_user.py

print('=== SeedSuite demo productor: start ===')

user = env.ref('seed_dashboard.demo_user_productor_fernandez', raise_if_not_found=False)
grower = env.ref('seed_base.grower_fernandez', raise_if_not_found=False)
group = env.ref('seed_base.group_seed_grower', raise_if_not_found=False)

if not (user and grower and group):
    print('faltan registros de demo (base sin seed_dashboard/seed_base demo); nada que hacer')
else:
    if grower.partner_id != user.partner_id:
        grower.partner_id = user.partner_id
        print('productor %s -> contacto %s' % (grower.name, user.partner_id.name))
    else:
        print('productor %s ya vinculado a %s' % (grower.name, grower.partner_id.name))

    if not user.has_group('seed_base.group_seed_grower'):
        user.group_ids = [(4, group.id)]
        print('usuario %s -> grupo %s' % (user.login, group.full_name))
    else:
        print('usuario %s ya está en %s' % (user.login, group.full_name))

    visible = env['seed.grower.contract'].with_user(user).search_count([])
    print('contratos visibles para %s: %d' % (user.login, visible))

env.cr.commit()
print('=== SeedSuite demo productor: done ===')

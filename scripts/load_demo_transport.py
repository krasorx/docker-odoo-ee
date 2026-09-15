# Idempotent loader: empresas transportistas, choferes, camiones y vínculo a tickets.
# Uso:
#   docker exec -i odoo_semillero-verticalizacion odoo shell \
#     --db_host=postgres --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
#     -d odoo --no-http < scripts/load_demo_transport.py

print('=== SeedSuite demo transport: start ===')

MODULE = 'seed_demo_live'
CUIT = env.ref('l10n_ar.it_cuit')
DNI = env.ref('l10n_ar.it_dni')
IVARI = env.ref('l10n_ar.res_IVARI')
CF = env.ref('l10n_ar.res_CF')
AR = env.ref('base.ar')
BA = env['res.country.state'].search([('country_id', '=', AR.id), ('name', '=', 'Buenos Aires')], limit=1)
SF = env['res.country.state'].search([('country_id', '=', AR.id), ('name', '=', 'Santa Fe')], limit=1)


def xid(name, record):
    data = env['ir.model.data'].sudo().search([
        ('module', '=', MODULE), ('name', '=', name),
    ], limit=1)
    if data:
        if data.res_id != record.id:
            data.res_id = record.id
        return data
    return env['ir.model.data'].sudo().create({
        'module': MODULE,
        'name': name,
        'model': record._name,
        'res_id': record.id,
        'noupdate': True,
    })


def by_xid(name, model):
    data = env['ir.model.data'].sudo().search([
        ('module', '=', MODULE), ('name', '=', name),
    ], limit=1)
    if data:
        rec = env[model].browse(data.res_id)
        if rec.exists():
            return rec
    return env[model]


def get_or_create(model, domain, vals, xmlid=None):
    rec = by_xid(xmlid, model) if xmlid else env[model]
    if xmlid and rec:
        rec.write({k: v for k, v in vals.items() if k != 'parent_id' or v})
        return rec
    rec = env[model].search(domain, limit=1)
    if rec:
        rec.write({k: v for k, v in vals.items() if k not in ('parent_id',)})
    else:
        rec = env[model].create(vals)
    if xmlid:
        xid(xmlid, rec)
    return rec


# ── Marca / modelo ──────────────────────────────────────────────────────────
brand_scania = env['fleet.vehicle.model.brand'].search([('name', '=', 'Scania')], limit=1)
if not brand_scania:
    brand_scania = env['fleet.vehicle.model.brand'].create({'name': 'Scania'})

brand_mb = env['fleet.vehicle.model.brand'].search([('name', 'ilike', 'Mercedes')], limit=1)
if not brand_mb:
    brand_mb = env['fleet.vehicle.model.brand'].create({'name': 'Mercedes-Benz'})

model_r450 = env['fleet.vehicle.model'].search([
    ('brand_id', '=', brand_scania.id), ('name', 'ilike', 'R 450'),
], limit=1)
if not model_r450:
    model_r450 = env['fleet.vehicle.model'].create({
        'brand_id': brand_scania.id, 'name': 'R 450',
    })

model_actros = env['fleet.vehicle.model'].search([
    ('brand_id', '=', brand_mb.id), ('name', 'ilike', 'Actros'),
], limit=1)
if not model_actros:
    model_actros = env['fleet.vehicle.model'].create({
        'brand_id': brand_mb.id, 'name': 'Actros 2651',
    })


# ── Empresas ────────────────────────────────────────────────────────────────
COMPANIES = [
    {
        'xmlid': 'co_norte',
        'vals': {
            'name': 'Transportes del Norte SA',
            'is_company': True,
            'company_type': 'company',
            'country_id': AR.id,
            'state_id': BA.id if BA else False,
            'city': 'Pergamino',
            'street': 'Ruta 8 km 165',
            'zip': '2700',
            'phone': '+54 2477 42-1100',
            'email': 'operaciones@norte-transportes.ar',
            'website': 'https://norte-transportes.ar',
            'vat': '30715558889',
            'l10n_latam_identification_type_id': CUIT.id,
            'l10n_ar_afip_responsibility_type_id': IVARI.id,
            'comment': 'Flota granelera. Zona norte de Buenos Aires.',
        },
    },
    {
        'xmlid': 'co_pampa',
        'vals': {
            'name': 'Logística Pampa SRL',
            'is_company': True,
            'company_type': 'company',
            'country_id': AR.id,
            'state_id': BA.id if BA else False,
            'city': 'Junín',
            'street': 'Av. San Martín 2450',
            'zip': '6000',
            'phone': '+54 236 442-8800',
            'email': 'despacho@logisticapampa.ar',
            'vat': '30716667770',
            'l10n_latam_identification_type_id': CUIT.id,
            'l10n_ar_afip_responsibility_type_id': IVARI.id,
            'comment': 'Cosecha y despacho. Zona oeste bonaerense.',
        },
    },
    {
        'xmlid': 'co_sur',
        'vals': {
            'name': 'Fletes del Sur SA',
            'is_company': True,
            'company_type': 'company',
            'country_id': AR.id,
            'state_id': SF.id if SF else False,
            'city': 'Venado Tuerto',
            'street': 'Ruta 8 km 366',
            'zip': '2600',
            'phone': '+54 3462 43-2200',
            'email': 'logistica@fletesdelsur.ar',
            'vat': '30717776662',
            'l10n_latam_identification_type_id': CUIT.id,
            'l10n_ar_afip_responsibility_type_id': IVARI.id,
            'comment': 'Jaulas de mazorca y granel. Sur de Santa Fe.',
        },
    },
]

companies = {}
for spec in COMPANIES:
    rec = get_or_create(
        'res.partner',
        ['|', ('vat', '=', spec['vals']['vat']), ('name', '=', spec['vals']['name'])],
        spec['vals'],
        spec['xmlid'],
    )
    companies[spec['xmlid']] = rec
    print('empresa:', rec.name, 'id=', rec.id, 'cuit=', rec.vat)


# ── Choferes (partner + employee) ───────────────────────────────────────────
DRIVERS = [
    # xmlid, company_xmlid, name, phone, pin, existing employee name (or None), dni
    ('drv_garcia',  'co_norte', 'Carlos García',  '+54 9 2477 55-0001', '4567', 'Carlos García',  '28445112'),
    ('drv_medina',  'co_norte', 'Jorge Medina',   '+54 9 2477 55-0002', '8001', None,             '30122876'),
    ('drv_paredes', 'co_norte', 'Luis Paredes',   '+54 9 2477 55-0003', '8002', None,             '25990341'),
    ('drv_lopez',   'co_pampa', 'Jorge López',    '+54 9 236 55-0101',  '5678', 'Jorge López',    '27110445'),
    ('drv_sosa',    'co_pampa', 'Hugo Sosa',      '+54 9 236 55-0102',  '8003', None,             '31887221'),
    ('drv_ramos',   'co_pampa', 'Diego Ramos',    '+54 9 236 55-0103',  '8004', None,             '29556780'),
    ('drv_ramirez', 'co_sur',   'Héctor Ramírez', '+54 9 3462 55-0201', '6789', 'Héctor Ramírez', '24881990'),
    ('drv_diaz',    'co_sur',   'Fabián Díaz',    '+54 9 3462 55-0202', '7890', 'Fabián Díaz',    '33221008'),
    ('drv_acuna',   'co_sur',   'Pablo Acuña',    '+54 9 3462 55-0203', '8005', None,             '27664110'),
    ('drv_vega',    'co_sur',   'Néstor Vega',    '+54 9 3462 55-0204', '8006', None,             '26111234'),
]

drivers = {}  # xmlid -> {'partner', 'employee'}
for xmlid, co_xmlid, name, phone, pin, existing_emp, dni in DRIVERS:
    company = companies[co_xmlid]
    partner_vals = {
        'name': name,
        'parent_id': company.id,
        'is_company': False,
        'company_type': 'person',
        'function': 'Chofer',
        'phone': phone,
        'country_id': AR.id,
        'vat': dni,
        'l10n_latam_identification_type_id': DNI.id,
        'l10n_ar_afip_responsibility_type_id': CF.id,
    }

    Employee = env['hr.employee']
    emp = by_xid(xmlid + '_emp', 'hr.employee')
    if not emp:
        if existing_emp:
            emp = Employee.search([('name', '=', existing_emp)], limit=1)
        if not emp:
            emp = Employee.search([('name', '=', name)], limit=1)

    # Si el empleado ya tiene work_contact, usarlo (evita duplicar el partner).
    partner = False
    if emp and emp.work_contact_id:
        partner = emp.work_contact_id
        partner.write({k: v for k, v in partner_vals.items() if k != 'vat' or not partner.vat})
        xid(xmlid, partner)
    else:
        partner = get_or_create(
            'res.partner',
            [('name', '=', name), ('parent_id', '=', company.id), ('active', 'in', [True, False])],
            partner_vals,
            xmlid,
        )
        if not partner.active:
            partner.active = True

    if not emp:
        emp = Employee.create({
            'name': name,
            'pin': pin,
            'work_phone': phone,
            'work_contact_id': partner.id,
        })
        xid(xmlid + '_emp', emp)
    else:
        emp_vals = {'work_phone': phone}
        if not emp.pin:
            emp_vals['pin'] = pin
        if emp.work_contact_id != partner:
            emp_vals['work_contact_id'] = partner.id
        emp.write(emp_vals)
        xid(xmlid + '_emp', emp)

    drivers[xmlid] = {'partner': partner, 'employee': emp}
    print('chofer:', name, 'partner=', partner.id, 'employee=', emp.id, '→', company.name)


# ── Camiones ────────────────────────────────────────────────────────────────
TRUCKS = [
    # plate, model, type, capacity, driver_xmlid, xmlid (optional)
    ('AEF 123', model_r450,   'grain_truck', 30000, 'drv_garcia',  None),
    ('EMN 345', model_r450,   'cob_truck',   15000, 'drv_medina',  None),
    ('BCD 456', model_r450,   'grain_truck', 28000, 'drv_lopez',   None),
    ('FPQ 678', model_actros, 'cob_truck',   15000, 'drv_sosa',    None),
    ('CGH 789', model_actros, 'grain_truck', 30000, 'drv_ramirez', None),
    ('DKL 012', model_actros, 'grain_truck', 28000, 'drv_diaz',    None),
    ('AF 611 DT', model_r450,  'grain_truck', 30000, 'drv_paredes', None),
    ('AE 802 HM', model_r450,  'grain_truck', 30000, 'drv_garcia',  None),
    ('AD 473 RS', model_r450,  'cob_truck',   15000, 'drv_ramos',   None),
    ('AF 290 LG', model_r450,  'grain_truck', 30000, 'drv_lopez',   None),
    ('AE 158 NF', model_r450,  'grain_truck', 30000, 'drv_acuna',   None),
    ('AD 606 CZ', model_r450,  'cob_truck',   15000, 'drv_vega',    None),
    ('AF 318 NT', model_r450,   'grain_truck', 30000, 'drv_garcia',  'truck_nor001'),
    ('AE 229 GD', model_r450,   'grain_truck', 28000, 'drv_medina',  'truck_nor002'),
    ('AD 845 WL', model_r450,   'cob_truck',   15000, 'drv_paredes', 'truck_nor003'),
    ('AF 176 BR', model_r450,   'grain_truck', 30000, 'drv_garcia',  'truck_nor004'),
    ('AE 663 PZ', model_r450,   'grain_truck', 32000, 'drv_lopez',   'truck_pam001'),
    ('AF 504 KX', model_r450,   'grain_truck', 30000, 'drv_sosa',    'truck_pam002'),
    ('AD 917 RC', model_r450,   'cob_truck',   14000, 'drv_ramos',   'truck_pam003'),
    ('AE 382 SV', model_r450,   'grain_truck', 30000, 'drv_ramirez', 'truck_sur001'),
    ('AF 741 TD', model_r450,   'cob_truck',   15000, 'drv_diaz',    'truck_sur002'),
    ('AD 059 MJ', model_r450,   'grain_truck', 28000, 'drv_acuna',   'truck_sur003'),
]

# Patentes previas (no válidas para ARBA): se renombran en vez de duplicar camiones.
LEGACY_PLATES = {
    'AF 611 DT': 'DEMO-T01', 'AE 802 HM': 'DEMO-T02', 'AD 473 RS': 'DEMO-T03',
    'AF 290 LG': 'DEMO-T04', 'AE 158 NF': 'DEMO-T05', 'AD 606 CZ': 'DEMO-T06',
    'AF 318 NT': 'NOR001', 'AE 229 GD': 'NOR002', 'AD 845 WL': 'NOR003', 'AF 176 BR': 'NOR004',
    'AE 663 PZ': 'PAM001', 'AF 504 KX': 'PAM002', 'AD 917 RC': 'PAM003',
    'AE 382 SV': 'SUR001', 'AF 741 TD': 'SUR002', 'AD 059 MJ': 'SUR003',
}
TRAILERS = {
    'AEF 123': 'WUP 318', 'EMN 345': 'VNZ 871', 'BCD 456': 'RDX 745', 'FPQ 678': 'PHJ 134',
    'CGH 789': 'TLM 219', 'DKL 012': 'SKB 563',
    'AF 611 DT': 'AD 377 KV', 'AE 802 HM': 'AC 649 PW', 'AD 473 RS': 'AB 185 TJ',
    'AF 290 LG': 'AC 936 BX', 'AE 158 NF': 'AD 724 QH', 'AD 606 CZ': 'AB 453 WM',
    'AF 318 NT': 'AC 552 RN', 'AE 229 GD': 'AD 671 MV', 'AD 845 WL': 'AB 297 KC', 'AF 176 BR': 'AC 430 JS',
    'AE 663 PZ': 'AD 108 HT', 'AF 504 KX': 'AC 786 NB', 'AD 917 RC': 'AB 541 LM',
    'AE 382 SV': 'AD 925 GP', 'AF 741 TD': 'AC 264 WK', 'AD 059 MJ': 'AB 812 FR',
}
HAS_TRAILER_FIELD = 'x_trailer_plate' in env['fleet.vehicle']._fields

vehicles = {}
for plate, model, vtype, cap, drv_xmlid, xmlid in TRUCKS:
    drv = drivers[drv_xmlid]
    vals = {
        'model_id': model.id,
        'license_plate': plate,
        'driver_id': drv['partner'].id,
        'driver_employee_id': drv['employee'].id,
        'x_seed_enabled': True,
        'x_seed_vehicle_type': vtype,
        'x_seed_capacity_kg': cap,
        'trailer_hook': plate in TRAILERS,
    }
    if HAS_TRAILER_FIELD:
        vals['x_trailer_plate'] = TRAILERS.get(plate, False)
    rec = env['fleet.vehicle'].search(
        [('license_plate', 'in', [plate, LEGACY_PLATES.get(plate, plate)])], limit=1)
    if rec:
        rec.write(vals)
    else:
        rec = env['fleet.vehicle'].create(vals)
    if xmlid:
        xid(xmlid, rec)
    vehicles[plate] = rec
    print('camion:', plate, 'id=', rec.id, 'tipo=', vtype, 'chofer=', drv['partner'].name)


# ── Tickets: transportista + chofer vacío ───────────────────────────────────
my_company_id = env.company.partner_id.id
internal_ids = {1, my_company_id}

def company_of_vehicle(vehicle):
    if not vehicle:
        return False
    if vehicle.driver_id and vehicle.driver_id.parent_id:
        return vehicle.driver_id.parent_id
    return False

Ticket = env['seed.weighing.ticket']
updated_co = 0
updated_drv = 0
for ticket in Ticket.search([]):
    vals = {}
    co = company_of_vehicle(ticket.vehicle_id)
    if co and (not ticket.transport_company_id or ticket.transport_company_id.id in internal_ids):
        vals['transport_company_id'] = co.id
    if ticket.vehicle_id and ticket.vehicle_id.driver_employee_id and not ticket.driver_id:
        vals['driver_id'] = ticket.vehicle_id.driver_employee_id.id
    if vals:
        ticket.write(vals)
        if 'transport_company_id' in vals:
            updated_co += 1
        if 'driver_id' in vals:
            updated_drv += 1

# Despachos sin camión: Fletes del Sur (típico despacho a cliente)
sur = companies['co_sur']
orphans = Ticket.search([
    ('transport_company_id', '=', False),
    ('operation_type', '=', 'despacho'),
])
if orphans:
    orphans.write({'transport_company_id': sur.id})
    updated_co += len(orphans)
    print('despachos huérfanos asignados a', sur.name, ':', len(orphans))

print('tickets actualizados: empresa=', updated_co, 'chofer=', updated_drv)


# ── Asignaciones de viaje: chofer real ──────────────────────────────────────
asg_updated = 0
for asg in env['seed.truck.assignment'].search([]):
    if asg.vehicle_id and asg.vehicle_id.driver_id:
        if asg.driver_id != asg.vehicle_id.driver_id:
            asg.driver_id = asg.vehicle_id.driver_id
            asg_updated += 1
print('asignaciones actualizadas:', asg_updated)

env.cr.commit()

print('=== resumen ===')
print('empresas:', env['res.partner'].search_count([
    ('id', 'in', [c.id for c in companies.values()]),
]))
print('camiones habilitados:', env['fleet.vehicle'].search_count([('x_seed_enabled', '=', True)]))
print('tickets con transportista:', Ticket.search_count([('transport_company_id', '!=', False)]))
print('tickets sin transportista:', Ticket.search_count([('transport_company_id', '=', False)]))
print('=== SeedSuite demo transport: done ===')

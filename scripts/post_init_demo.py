# Post-init: empresa demo + lang. Se pega a `odoo shell -d semillero_demo`.
print('=== post_init_demo: start ===')

AR = env.ref('base.ar')
company = env.company
vals = {
    'name': 'Semillero Demo',
    'country_id': AR.id,
}
if 'street' in company._fields and not company.street:
    vals['street'] = 'Ruta 8 km 165'
    vals['city'] = 'Pergamino'
    ba = env['res.country.state'].search([
        ('country_id', '=', AR.id), ('name', '=', 'Buenos Aires'),
    ], limit=1)
    if ba:
        vals['state_id'] = ba.id
    vals['zip'] = '2700'
company.write(vals)
print('company:', company.name, 'country:', company.country_id.code)

admin = env.ref('base.user_admin')
es_ar = env['res.lang'].search([('code', '=', 'es_AR')], limit=1)
if es_ar:
    admin.lang = 'es_AR'
    env.company.partner_id.lang = 'es_AR'
admin.password = 'admin'
print('admin lang:', admin.lang)

# Asegurar trial EE fresco (por si el init copió algo)
exp = env['ir.config_parameter'].sudo().get_param('database.expiration_date')
print('expiration_date:', exp)

env.cr.commit()
print('=== post_init_demo: done ===')

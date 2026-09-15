# Idempotente: borra los pallets y lotes huérfanos que dejaron las regeneraciones
# de la demo de planta anteriores al arreglo de _clear_demo_data (que sólo
# limpiaba el lote húmedo prefijado y no los de secado, desgrane, fracción y PT).
# Huérfano = sin xmlid y sin ninguna orden viva que lo referencie, o sea ni de la
# demo XML ni de una cadena actual. Una base regenerada con el código actual no
# tiene ninguno.
# Uso:
#   docker exec -i odoo_semillero-verticalizacion sh -c 'odoo shell \
#     --db_host=postgres --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
#     -d semillero_demo --no-http' < scripts/fix_demo_orphan_pallets.py

print('=== SeedSuite demo huérfanos: start ===')

Pallet = env['seed.pallet'].sudo()
orphans = Pallet.search([('bagging_order_id', '=', False)])
keep = set(env['ir.model.data'].search([
    ('model', '=', 'seed.pallet'), ('res_id', 'in', orphans.ids),
]).mapped('res_id'))
junk = orphans.filtered(lambda p: p.id not in keep)

print('pallets sin orden: %d — de la demo XML: %d — a borrar: %d' % (
    len(orphans), len(keep), len(junk)))

for pallet in junk:
    name, lot = pallet.name, pallet.lot_id.name or '-'
    try:
        with env.cr.savepoint():
            pallet.unlink()
        print('  borrado %s (lote %s)' % (name, lot))
    except Exception as exc:
        print('  NO se pudo borrar %s (lote %s): %s' % (name, lot, exc))

print('pallets restantes: %d' % Pallet.search_count([]))

# Fase 2: los lotes de las cadenas viejas (secado, desgrane, fracción y PT).
Demo = env['seed.plant.demo']
REFERENCES = (
    ('seed.drying.order', 'lot_in_id'), ('seed.drying.order', 'lot_out_id'),
    ('seed.shelling.order', 'lot_in_id'), ('seed.shelling.order', 'lot_out_id'),
    ('seed.processing.order', 'lot_in_id'), ('seed.processing.fraction', 'lot_id'),
    ('seed.treatment.order', 'lot_in_id'), ('seed.treatment.order', 'lot_out_id'),
    ('seed.pallet', 'lot_id'), ('seed.weighing.ticket', 'lot_id'),
)
referenced = set()
for model, fname in REFERENCES:
    if model in env:
        referenced |= set(env[model].sudo().search(
            [(fname, '!=', False)]).mapped(fname).ids)
from_xml = set(env['ir.model.data'].search(
    [('model', '=', 'stock.lot')]).mapped('res_id'))


def is_chain_lot(lot):
    """Nombres que sólo genera la demo de planta: prefijo o <var>-<cal>-<form>."""
    import re
    return bool(
        lot.name
        and (lot.name.startswith(Demo.LOT_PREFIX)
             or re.match(r'^[A-Z0-9]+-[A-Z]+-FI\d+-', lot.name)))


candidates = env['stock.lot'].sudo().search([]).filtered(
    lambda l: l.id not in referenced and l.id not in from_xml)
junk_lots = candidates.filtered(is_chain_lot)
skipped = candidates - junk_lots

print('lotes sin referencia: %d — de cadena de demo: %d' % (
    len(candidates), len(junk_lots)))
for lot in skipped:
    print('  se conserva %s (no tiene nombre de cadena de demo)' % lot.name)
for lot in junk_lots:
    print('  borrando %s' % lot.name)
Demo._clear_demo_lots(junk_lots)
print('lotes restantes: %d' % env['stock.lot'].search_count([]))

env.cr.commit()
print('=== SeedSuite demo huérfanos: done ===')

from openerp.osv import osv
from openerp import netsvc
import datetime
from openerp.tools.translate import _


class stock_picking_out(osv.Model):
    _name = "stock.picking.out"
    _inherit = "stock.picking.out"

    def action_back_to_confirmed(self, cr, uid, ids, *args):
        """ Resets pickings back to the confirmed state
        @return: True
        """
        wf_service = netsvc.LocalService("workflow")

        # Set the line items back to confirmed
        # ------------------------------------
        todo = []
        for pick in self.browse(cr, uid, ids):
            for r in pick.move_lines:
                todo.append(r.id)
        todo = self.action_explode(cr, uid, todo)
        if len(todo):
            self.pool.get('stock.move').action_confirm(cr, uid, todo)

        # Push the workflow back to confirmed
        # -----------------------------------
        for pick in self.browse(cr, uid, ids):
            wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_confirm_assigned_back', cr)
        return True



    def action_prioritize(self, cr, uid, ids, *args):
        """ Prioritize a picking
        @return: True
        """
        if len(ids) > 1:
            raise osv.except_osv(_('Not allowed!'), _('You may only prioritize 1 delivery at a time!'))

        move_db = self.pool.get('stock.move')
        pick = self.browse(cr, uid, ids)[0]
        products = [m.product_id.id for m in pick.move_lines]
        moves = move_db.search(cr, uid, [('product_id','in',products),('state', '=', 'assigned')])
        moves = move_db.browse(cr, uid, moves)
        self.action_back_to_confirmed(cr, uid, list(set([m.picking_id.id for m in moves])))
        self.action_assign(cr, uid, ids)
        return True

    def action_maximize(self, cr, uid, ids, *args):
        """ Maximize a picking
        @return: True
        """
        if len(ids) > 1:
            raise osv.except_osv(_('Not allowed!'), _('You may only maximize 1 delivery at a time!'))

        pick = self.browse(cr, uid, ids)[0]

        # If a product appears twice in a delivery, maximizing isn't allowed
        # ------------------------------------------------------------------
        if len(pick.move_lines) != len(set([m.product_id.id for m in pick.move_lines])):
            raise osv.except_osv(_('Not allowed!'), _('You may only maximize if there are no product duplicates!'))


        # Check if required
        # -----------------
        if not [m for m in pick.move_lines if m.state != 'assigned']:
            return True

        # See if we can get to fully availably by prioritizing
        # ----------------------------------------------------
        self.action_back_to_confirmed(cr, uid, ids)
        self.action_prioritize(cr, uid, ids)
        if not [m for m in pick.move_lines if m.state != 'assigned']:
            return True


        # If there's still lines that aren't fully available,
        # split all non-available lines using serial numbers to allow for a maximum delivery
        # ----------------------------------------------------------------------------------
        lot_db = self.pool.get('stock.production.lot')
        split_db = self.pool.get('stock.move.split')

        moves = [m for m in pick.move_lines if m.state == 'confirmed']
        for move in moves:

            lot_id = lot_db.create(cr, uid, {'product_id': move.product_id.id, 'name': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
            vals = {
                'use_exist'   : True,
                'product_id'  : move.product_id.id,
                'product_uom' : move.product_id.uom_id.id,
                'qty'         : move.product_qty,
                'location_id' : move.location_id.id,
                'line_exist_ids': [[0, False, {'prodlot_id': lot_id, 'quantity': move.product_qty - move.product_id.qty_available}]],
            }
            split_id = split_db.create(cr, uid, vals, context={'active_model':'stock.move'})
            split_db.split(cr, uid, [split_id], [move.id], context={'active_model':'stock.move'})

        self.action_assign(cr, uid, ids)
        return True




















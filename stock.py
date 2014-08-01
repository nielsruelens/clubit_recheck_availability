from openerp.osv import osv
from openerp import netsvc
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
        """ Prioritize pickings
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
        """ Maximize pickings
        @return: True
        """
        return True


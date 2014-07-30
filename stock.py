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

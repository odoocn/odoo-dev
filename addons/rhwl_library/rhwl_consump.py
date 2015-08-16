# coding=utf-8

from openerp import SUPERUSER_ID,api
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
import datetime
import openerp
import logging

class rhwl_library_consump(osv.osv):
    _name = "rhwl.library.consump"

    _columns={
        "name":fields.char("Name",size=10,readonly=True),
        "date":fields.date("Date"),
        "user_id":fields.many2one("res.users","User",readonly=True),
        "location_id":fields.many2one("stock.location","Location",required=True,domain=[('usage', '=', 'internal'),("loc_barcode","=","99")],readonly=True,states={'draft':[('readonly',False)]}),
        "state":fields.selection([("draft","Draft"),("confirm","Confirm"),("done","Done"),("cancel","Cancel")],"State"),
        "note":fields.text("Note"),
        "active":fields.boolean("Active"),
        "project":fields.many2one("res.company.project","Project"),
        "is_rd":fields.boolean("R&D"),
        "line":fields.one2many("rhwl.library.consump.line","name","Detail",readonly=True,states={'draft':[('readonly',False)]})
    }

    _defaults={
        "state":'draft',
        "user_id":lambda obj,cr,uid,context=None:uid,
        "date":fields.date.today,
        "active":True,
        "is_rd":False
    }
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'rhwl.library.consump') or '/'
        return super(rhwl_library_consump,self).create(cr,uid,vals,context)

    def action_state_confirm(self,cr,uid,ids,context=None):
        if isinstance(ids,(long,int)):
            ids = [ids]
        c = self.pool.get("rhwl.library.consump.line").search_count(cr,uid,[("name.id","in",ids),("qty","<=",0)])
        if c>0:
            raise osv.except_osv(u"错误",u"明细物料耗用量必须大于0")

        self.write(cr,uid,ids,{"state":"confirm"},context=context)

    def action_state_reset(self,cr,uid,ids,context=None):
        self.write(cr,uid,ids,{"state":"draft"},context=context)

    def action_state_done(self,cr,uid,ids,context=None):
        obj = self.browse(cr,uid,ids,context=context)
        location_dest_id = self.pool.get("stock.location").search(cr,uid,[("usage","=","production")])
        wh = self.pool.get("stock.warehouse").search(cr,uid,[("partner_id","=",1)])
        picking_type = self.pool.get("stock.picking.type").search(cr,uid,[("warehouse_id","=",wh[0]),("code","=","internal")])
        val={
            "partner_id":1,
            "min_date":fields.datetime.now(),
            "origin":obj.name,
            "picking_type_id":picking_type[0],
            "move_lines":[],
            "project":obj.project.id,
            "is_rd":obj.is_rd,
        }
        for l in obj.line:
            move_val={
                "product_id":l.product_id.id
            }
            res=self.pool.get("stock.move").onchange_product_id(cr,uid,0,l.product_id.id)
            move_val.update(res["value"])
            move_val["product_uom_qty"]=l.qty
            move_val["product_uos_qty"]=l.qty
            move_val["location_id"]=obj.location_id.id
            move_val["location_dest_id"]=location_dest_id[0]
            move_id = self.pool.get("stock.move").create(cr,uid,move_val,context=context)
            val["move_lines"].append([4,move_id])


        self.pool.get("stock.picking").create(cr,uid,val,context=context)
        self.write(cr,uid,ids,{"state":"done"},context=context)

    def action_view_picking(self,cr,uid,ids,context=None):
        obj = self.browse(cr,uid,ids,context)
        picking_id = self.pool.get("stock.picking").search(cr,uid,[("origin","=",obj.name)])
        if not picking_id:
            self.action_state_done(cr,uid,ids,context=context)
            picking_id = self.pool.get("stock.picking").search(cr,uid,[("origin","=",obj.name)])

        value = {
            'domain': "[('id','in',[" + ','.join(map(str, picking_id)) + "])]",
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'stock.picking',
            'res_id': picking_id[0],
            'view_id': False,
            'context': context,
            'type': 'ir.actions.act_window',

        }
        return value

class rhwl_library_consump_line(osv.osv):
    _name = "rhwl.library.consump.line"
    _columns={
        "name":fields.many2one("rhwl.library.consump","Name"),
        "product_id":fields.many2one("product.product","Product",required=True,domain=[("cost_allocation","=",True)]),
        "brand":fields.related("product_id","brand",type="char",string=u"品牌",readonly=True),
        "default_code":fields.related("product_id","default_code",type="char",string=u"货号",readonly=True),
        "attribute":fields.related("product_id","attribute_value_ids",obj="product.attribute.value", type="many2many",string=u"规格",readonly=True),
        "uom_id":fields.related("product_id","uom_id",type="many2one",obj="product.uom",string="Unit",readonly=True),
        "qty":fields.float("Qty",digits_compute=dp.get_precision('Product Unit of Measure'),required=True,),
    }

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.brand = self.product_id.brand
            self.default_code = self.product_id.default_code
            self.attribute = self.product_id.attribute_value_ids
            self.uom_id = self.product_id.uom_id
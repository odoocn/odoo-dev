# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time

from openerp.osv import fields, osv
from openerp.tools.translate import _
import xlwt
import base64
import os
from tempfile import NamedTemporaryFile
import tempfile
import openerp
import logging
import zipfile
import subprocess
import shutil

_logger = logging.getLogger(__name__)
class export_excel(osv.osv_memory):
    _name = "sale.sample.export.excel"
    _description = "Sample Excel Report"
    _columns={
        "file":fields.binary(u"文件"),
        "name":fields.char("File Name"),
        "state":fields.selection([('draft','Draft'),('done','Done')],string="State"),
    }

    _defaults={
        "state":'draft'
    }

    def action_excel(self,cr,uid,ids,context=None):
        if not context:
            context={}
        if context.get('func_name','')=='report1':
            return self.action_excel_bx(cr,uid,ids,context=context)
        elif context.get('func_name','')=='report2':
            return self.action_excel_fy(cr,uid,ids,context=context)
        elif context.get('func_name','')=="report3":
            return self.action_excel_apply(cr,uid,ids,context=context)
        elif context.get('func_name','')=="report4":
            return self.action_excel_report4(cr,uid,ids,context=context)

    def action_excel_bx(self,cr,uid,ids,context=None):
        if not context.get("active_ids"):return
        fileobj = NamedTemporaryFile('w+',delete=True)
        xlsname =  fileobj.name
        fileobj.close()
        ids=context.get("active_ids")
        if isinstance(ids,(list,tuple)):
            ids.sort()

        w = xlwt.Workbook(encoding='utf-8')
        ws = w.add_sheet("Sheet1")

        ws.write(0,0,u"检测编号")
        ws.write(0,1,u"孕妇姓名")
        ws.write(0,2,u"手机号")
        ws.write(0,3,u"身份证号")
        ws.write(0,4,u"采血日期")

        rows=1
        for i in self.pool.get("sale.sampleone").browse(cr,uid,ids,context=context):
            ws.write(rows,0,i.name)
            ws.write(rows,1,i.yfxm)
            ws.write(rows,2,i.yftelno)
            ws.write(rows,3,i.yfzjmc_no)
            ws.write(rows,4,i.cx_date)
            rows+=1

        w.save(xlsname)
        f=open(xlsname,'rb')

        id = self.create(cr,uid,{"state":"done","file":base64.encodestring(f.read()),"name":u"保险信息单.xls"})
        f.close()
        os.remove(xlsname)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.sample.export.excel',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': id,
            'views': [(False, 'form')],
            'target': 'new',
            'name':u"导出保险信息单Excel"
        }

    def action_excel_fy(self,cr,uid,ids,context=None):
        if not context.get("active_ids"):return
        fileobj = NamedTemporaryFile('w+',delete=True)
        xlsname =  fileobj.name
        fileobj.close()
        ids=context.get("active_ids")
        if isinstance(ids,(list,tuple)):
            ids.sort()

        w = xlwt.Workbook(encoding='utf-8')
        ws = w.add_sheet("Sheet1")

        ws.write(1,0,u"中心条码")
        ws.write(1,1,u"病人姓名")
        ws.write(1,2,u"年龄")
        ws.write(1,3,u"孕周")
        ws.write(1,4,u"采样日期")
        ws.write(1,5,u"送检医院")
        ws.write(1,6,u"送检人员")
        ws.write(1,7,u"临床收费")
        ws.write(1,8,u"备注")


        rows=1
        for i in self.pool.get("sale.sampleone").browse(cr,uid,ids,context=context):
            ws.write(rows,0,i.name)
            ws.write(rows,1,i.yfxm)
            ws.write(rows,2,i.yftelno)
            ws.write(rows,3,i.yfzjmc_no)
            ws.write(rows,4,i.cx_date)
            rows+=1

        w.save(xlsname)
        f=open(xlsname,'rb')

        id = self.create(cr,uid,{"state":"done","file":base64.encodestring(f.read()),"name":u"费用结算单.xls"})
        f.close()
        os.remove(xlsname)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.sample.export.excel',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': id,
            'views': [(False, 'form')],
            'target': 'new',
            'name':u"导出费用结算单Excel"
        }

    def action_excel_apply(self,cr,uid,ids,context=None):
        if not context.get("active_ids"):return
        ids=context.get("active_ids")
        if isinstance(ids,(list,tuple)):
            ids.sort()
        if len(ids)>1:
            raise osv.except_osv("Error",u"每次只可以导出一个申请单。")
        ids=ids[0]
        obj = self.pool.get("purchase.order.apply").browse(cr,uid,ids,context=context)

        w = xlwt.Workbook(encoding='utf-8')

        ws = w.add_sheet(u"申请单")
        ws.col(0).width =2350
        ws.col(1).width =1150
        ws.col(2).width =3250
        ws.col(3).width =1820
        ws.col(4).width =3320
        ws.col(5).width =2970
        ws.col(6).width =1330
        ws.col(7).width =3250
        ws.col(8).width =5220
        ws.col(9).width =2830
        ws.col(10).width =2450
        ws.col(11).width =2900
        ws.col(12).width =3060
        ws.write_merge(0,0,0,12,u"人和未来费用申请单",style=self.get_excel_style(font_size=12,horz=xlwt.Alignment.HORZ_CENTER,blod=True))
        ws.write(1,0,u"申请部门",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(1,1,1,4,obj.dept.name,style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write(1,5,u"申请人",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(1,1,6,9,obj.user_id.name,style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(1,1,10,12,u"时间："+obj.date,style=self.get_excel_style(horz=xlwt.Alignment.HORZ_RIGHT,border=xlwt.Borders.THIN))
        ws.write(2,0,u"申请事由/费用用途",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(2,2,1,12,obj.reason,style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(3,5,1,1,u"序号",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(3,5,2,2,u"品名或事由",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(3,5,3,3,u"规格",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(3,5,4,4,u"品牌及货号",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(3,5,5,5,u"单价 （元）",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(3,5,6,6,u"数量",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(3,5,7,7,u"金额  （元）",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(3,3,8,10,u"资金申请方式",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(4,4,8,9,u"转账",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write(5,8,u"账号及单位名称",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write(5,9,u"金额（元）",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(4,5,10,10,u"现金      （元）",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(3,5,11,11,u"备注/供应商",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(3,5,12,12,u"是否支付 （财务填写）",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))

        ws.row(0).height_mismatch = True
        ws.row(0).height = 20*20
        ws.row(1).height_mismatch = True
        ws.row(1).height = 20*20
        ws.row(2).height_mismatch = True
        ws.row(2).height = 30*20

        rows=6
        total_amt=0
        pr_id = self.pool.get("purchase.requisition").search(cr,uid,[("origin","=",obj.name)])
        if pr_id:
            pr_obj = self.pool.get("purchase.requisition").browse(cr,uid,pr_id[0],context=context)
            for p in pr_obj.purchase_ids:
                if p.state=="cancel":continue
                for l in p.order_line:
                    ws.write(rows,1,rows-5,style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
                    ws.write(rows,2,l.product_id.name,style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
                    ws.write(rows,3,1 and l.product_id.attribute_value_ids.name or "",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))

                    ws.write(rows,4,u",".join([x for x in [l.product_id.brand,l.product_id.default_code] if x]),style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
                    ws.write(rows,5,l.price_unit,style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
                    ws.write(rows,6,l.product_qty,style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
                    ws.write(rows,7,round(l.price_unit*l.product_qty,2),style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
                    total_amt += round(l.price_unit*l.product_qty,2)
                    ws.row(rows).height_mismatch = True
                    ws.row(rows).height = 20*20
                    ws.write(rows,8,"",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
                    ws.write(rows,9,"",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
                    ws.write(rows,10,"",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
                    ws.write(rows,11,"",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
                    ws.write(rows,12,"",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
                    rows+=1
        ws.write_merge(3,rows-1,0,0,u"费用明细",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write(rows,0,u"总费用",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,blod=True,border=xlwt.Borders.THIN))
        ws.write_merge(rows,rows,1,6,u"大写："+self.num2chn(total_amt).decode("utf-8"),style=self.get_excel_style(border=xlwt.Borders.THIN))
        ws.write(rows,7,total_amt,style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write(rows,8,"",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write(rows,9,"",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write(rows,10,"",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write(rows,11,"",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write(rows,12,"",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.row(rows).height_mismatch = True
        ws.row(rows).height = 20*20
        rows+=1
        ws.write_merge(rows,rows,0,12,u"签字",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,blod=True,border=xlwt.Borders.THIN))
        ws.row(rows).height_mismatch = True
        ws.row(rows).height = 20*20
        rows+=1
        ws.write_merge(rows,rows,0,1,u"申请人",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(rows,rows,2,4,"",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(rows,rows,5,6,u"部门负责人",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(rows,rows,7,8,"",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write(rows,9,u"财务负责人",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(rows,rows,10,12,"",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.row(rows).height_mismatch = True
        ws.row(rows).height = 20*20
        rows+=1
        ws.write_merge(rows,rows,0,1,u"主管总监",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(rows,rows,2,4,"",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(rows,rows,5,6,u"总裁",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.write_merge(rows,rows,7,12,"",style=self.get_excel_style(horz=xlwt.Alignment.HORZ_CENTER,border=xlwt.Borders.THIN))
        ws.row(rows).height_mismatch = True
        ws.row(rows).height = 20*20
        fileobj = NamedTemporaryFile('w+',delete=True)
        xlsname =  fileobj.name
        fileobj.close()
        w.save(xlsname)
        f=open(xlsname,'rb')

        id = self.create(cr,uid,{"state":"done","file":base64.encodestring(f.read()),"name":obj.name+u"费用申请单.xls"})
        f.close()
        os.remove(xlsname)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.sample.export.excel',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': id,
            'views': [(False, 'form')],
            'target': 'new',
            'name':u"导出费用申请单Excel"
        }

    def action_excel_report4(self,cr,uid,ids,context=None):
        if not context.get("active_ids"):return
        fileobj = NamedTemporaryFile('w+',delete=True)
        xlsname =  fileobj.name
        fileobj.close()
        ids=context.get("active_ids")
        if isinstance(ids,(list,tuple)):
            ids.sort()
        payment_kind = {'hospital':u"医院代收",'proxy':u'经销商代收','pos':u'POS机收费','cash':u'现金'}

        w = xlwt.Workbook(encoding='utf-8')
        ws = w.add_sheet("Sheet1")
        ws.write(0,0,u"样本编码")
        ws.write(0,1,u"姓名")
        ws.write(0,2,u"采血日期")
        ws.write(0,3,u"采血医院")
        ws.write(0,4,u"采血医生")
        ws.write(0,5,u"是否重采血")
        ws.write(0,6,u"是否免费")
        ws.write(0,7,u"临床收费")
        ws.write(0,8,u"结算金额")
        ws.write(0,9,u"结算方式")
        rows=1
        for i in self.pool.get("sale.sampleone").browse(cr,uid,ids,context=context):
            ws.write(rows,0,i.name)
            ws.write(rows,1,i.yfxm)
            ws.write(rows,2,i.cx_date)
            ws.write(rows,3,i.cxyy.name)
            ws.write(rows,4,i.cxys.name)
            ws.write(rows,5,u"首次采血" if i.is_reused==u"0" else u"重采血")
            ws.write(rows,6,u"是" if i.is_free==u"1" else u"否")
            ws.write(rows,7,i.cxyy.hospital_price)
            ws.write(rows,8,i.cxyy.amt)
            ws.write(rows,9,payment_kind.get(i.cxyy.payment_kind.decode("utf-8")))
            rows+=1

        w.save(xlsname)
        f=open(xlsname,'rb')

        id = self.create(cr,uid,{"state":"done","file":base64.encodestring(f.read()),"name":u"样本对帐单.xls"})
        f.close()
        os.remove(xlsname)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.sample.export.excel',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': id,
            'views': [(False, 'form')],
            'target': 'new',
            'name':u"导出对帐单Excel"
        }

    def get_excel_style(self,font_size=10,horz=xlwt.Alignment.HORZ_LEFT,border=xlwt.Borders.NO_LINE,blod=False):
        #18号字，加边框，水平靠右，垂直居中
        style2 = xlwt.XFStyle()
        style2.font = xlwt.Font()
        style2.font.name=u"宋体"
        style2.font.height = 20*font_size
        style2.font.bold = blod
        style2.alignment = xlwt.Alignment()
        style2.alignment.horz = horz
        style2.alignment.vert = xlwt.Alignment.VERT_CENTER
        style2.borders = xlwt.Borders() # Add Borders to Style
        style2.borders.left = border # May be: NO_LINE, THIN, MEDIUM, DASHED, DOTTED, THICK, DOUBLE, HAIR, MEDIUM_DASHED, THIN_DASH_DOTTED, MEDIUM_DASH_DOTTED, THIN_DASH_DOT_DOTTED, MEDIUM_DASH_DOT_DOTTED, SLANTED_MEDIUM_DASH_DOTTED, or 0x00 through 0x0D.
        style2.borders.right = border
        style2.borders.top = border
        style2.borders.bottom = border
        style2.borders.left_colour = 0x40
        style2.borders.right_colour = 0x40
        style2.borders.top_colour = 0x40
        style2.borders.bottom_colour = 0x40
        style2.alignment.wrap=True
        return style2

    def IIf(self, b, s1, s2):
       if b:
            return s1
       else:
            return s2

    def num2chn(self,nin=None):
        cs =('零','壹','贰','叁','肆','伍','陆','柒','捌','玖','◇','分','角','圆','拾','佰','仟',
                '万','拾','佰','仟','亿','拾','佰','仟','万')
        st = ''; st1=''
        s = '%0.2f' % (nin)
        sln =len(s)
        if sln >15: return None
        fg = (nin<1)
        for i in range(0, sln-3):
            ns = ord(s[sln-i-4]) - ord('0')
            st=self.IIf((ns==0) and (fg or (i==8) or (i==4) or (i==0)), '', cs[ns])+ self.IIf((ns==0)and((i<>8) and (i<>4) and (i<>0) or fg  and(i==0)),'', cs[i+13])+ st
            fg = (ns==0)
        fg = False
        for i in [1,2]:
            ns = ord(s[sln-i]) - ord('0')
            st1=self.IIf(ns==0 and (i==1 or i==2 and (fg or (nin<1))), '', cs[ns]) + self.IIf((ns>0), cs[i+10], self.IIf((i==2) or fg, '', '整')) + st1
            fg = (ns==0)
        st.replace('亿万','万')
        return self.IIf( nin==0, '零', st + st1)
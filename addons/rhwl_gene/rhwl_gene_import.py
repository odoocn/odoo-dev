# -*- coding: utf-8 -*-

import threading
from openerp.osv import osv,fields
import base64
from tempfile import NamedTemporaryFile
import xlrd,os
import datetime
import logging

_logger = logging.getLogger(__name__)
class rhwl_import(osv.osv_memory):
    _name = 'rhwl.genes.import'
    _columns = {
        "file_bin":fields.binary(string=u"文件名",required=True),
    }

    def date_trun(self,val):
        if list(str(val)).count("/")==0:
            d=xlrd.xldate_as_tuple(int(val),0)
            return "%s/%s/%s"%(d[0],d[1],d[2])
        else:
            return val
    def datetime_trun(self,val):
        if list(str(val)).count("/")==0:
            d=xlrd.xldate_as_tuple(val,0)
            return "%s/%s/%s %s:%s:%s"%(d[0],d[1],d[2],d[3],d[4],d[5])
        else:
            return val

    def import_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        this = self.browse(cr, uid, ids[0])

        fileobj = NamedTemporaryFile('w+',delete=True)
        xlsname =  fileobj.name
        f=open(xlsname+'.xls','wb')
        fileobj.close()
        try:
            #fileobj.write(base64.decodestring(this.file_bin.decode('base64')))
            b=this.file_bin.decode('base64')
            f.write(b)
            f.close()

            try:
                bk = xlrd.open_workbook(xlsname+".xls")
                sh = bk.sheet_by_index(0)
            except:
               raise osv.except_osv(u"打开出错",u"请确认文件格式是否为正确的报告标准格式。")
            nrows = sh.nrows
            ncols = sh.ncols
            batch_no={}
            for i in range(2,nrows+1):
                if not sh.cell_value(i-1,0):continue
                date_col=self.date_trun(sh.cell_value(i-1,0))
                val={
                    "date":date_col,
                    "cust_name":sh.cell_value(i-1,1),
                    "sex": 'T' if sh.cell_value(i-1,2)==u"男" else 'F',
                    "name":sh.cell_value(i-1,3),
                    "identity":sh.cell_value(i-1,4),
                    "receiv_date":self.datetime_trun(sh.cell_value(i-1,5))
                }
                if batch_no.get(date_col):
                    val["batch_no"]=batch_no.get(date_col)
                else:
                    cr.execute("select max(batch_no) from rhwl_easy_genes where cust_prop='tjs'")
                    max_no="0"
                    for no in cr.fetchall():
                        max_no = no
                    max_no=str(int(max_no)+1).zfill(3)
                    batch_no[date_col]=max_no
                    val["batch_no"]=max_no
                self.pool.get("rhwl.easy.genes").create(cr,uid,val,context=context)

        finally:
            f.close()
            os.remove(xlsname+'.xls')
        v_id=self.pool.get('ir.ui.view').search(cr,uid,[('name', '=', "rhwl.easy.genes.view.tree")])

        return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                "view_id":v_id,
                'res_model': 'rhwl.easy.genes',
                "context":{'search_default_type_draft':1,'search_default_type_exceptconfirm':1},
                'view_mode': 'tree'}

    def import_report2(self, cr, uid, ids, context=None):
        """接收质检数据"""
        if context is None:
            context = {}
        this = self.browse(cr, uid, ids[0])

        fileobj = NamedTemporaryFile('w+',delete=True)
        xlsname =  fileobj.name
        f=open(xlsname+'.xls','wb')
        fileobj.close()
        try:
            #fileobj.write(base64.decodestring(this.file_bin.decode('base64')))
            b=this.file_bin.decode('base64')
            f.write(b)
            f.close()

            try:
                bk = xlrd.open_workbook(xlsname+".xls")
                sh = bk.sheet_by_index(0)
            except:
               raise osv.except_osv(u"打开出错",u"请确认文件格式是否为正确的报告标准格式。")
            nrows = sh.nrows

            for i in range(2,nrows):
                no=sh.cell_value(i,1)
                if not no:continue
                if type(no)==type(1.0):no = no.__trunc__()
                id=self.pool.get("rhwl.easy.genes").search(cr,uid,[("name","=",no)],context=context)
                self.pool.get("rhwl.easy.genes").write(cr,uid,id,{"log":[[0,0,{"note":u"导入质检数据","data":"DNA"}]]},context=context)
                obj_ids = self.pool.get("rhwl.easy.genes.check").search(cr,uid,[("genes_id.name",'=',no)],context=context)
                if obj_ids:
                    self.pool.get("rhwl.easy.genes.check").write(cr,uid,obj_ids,{"active":False})
                t1=sh.cell_value(i,3)
                t2=sh.cell_value(i,5)
                t3=sh.cell_value(i,6)
                t4=sh.cell_value(i,8)
                val={
                        "genes_id":id[0],
                        "date":self.date_trun(sh.cell_value(i,0)),
                        "dna_date":self.date_trun(sh.cell_value(i,2)),
                        "concentration":t1,
                        "lib_person":sh.cell_value(i,4),
                        "od260_280":t2,
                        "od260_230":t3,
                        "chk_person":sh.cell_value(i,7),
                        "data_loss":str(t4*100)+"%",
                        "loss_person":sh.cell_value(i,9),
                        "loss_date":self.date_trun(sh.cell_value(i,10)),
                        "active":True,
                    }
                _logger.info(val)
                self.pool.get("rhwl.easy.genes.check").create(cr,uid,val,context=context)
                if (t1<10 or t2<1.8 or t2>2 or t3<2 or t4>0.01):
                    if obj_ids:
                        self.pool.get("rhwl.easy.genes").action_state_dna(cr,uid,id,context=context)
                else:
                    self.pool.get("rhwl.easy.genes").action_state_dnaok(cr,uid,id,context=context)

        finally:
            f.close()
            os.remove(xlsname+'.xls')

        return

    def import_report3(self, cr, uid, ids, context=None):
        """接收检测点位数据"""
        if context is None:
            context = {}
        this = self.browse(cr, uid, ids[0])

        fileobj = NamedTemporaryFile('w+',delete=True)
        xlsname =  fileobj.name
        f=open(xlsname+'.xls','wb')
        fileobj.close()
        try:
            #fileobj.write(base64.decodestring(this.file_bin.decode('base64')))
            b=this.file_bin.decode('base64')
            f.write(b)
            f.close()

            try:
                bk = xlrd.open_workbook(xlsname+".xls")
                sh = bk.sheet_by_index(0)
            except:
               raise osv.except_osv(u"打开出错",u"请确认文件格式是否为正确的报告标准格式。")
            nrows = sh.nrows
            ncols = sh.ncols
            snp={}
            for i in range(1,ncols):
                v=sh.cell_value(0,i)
                if not v:continue
                snp[i]=v

            for i in range(1,nrows):
                no=sh.cell_value(i,0)
                if not no:continue
                id=self.pool.get("rhwl.easy.genes").search(cr,uid,[("name","=",no)],context=context)
                if not id:
                    raise osv.except_osv(u"错误",u"基因样本编码[%s]不存在。"%(no,))
                self.pool.get("rhwl.easy.genes").write(cr,uid,id,{"log":[[0,0,{"note":u"导入位点数据","data":"SNP"}]]},context=context)
                type_ids = self.pool.get("rhwl.easy.genes.type").search(cr,uid,[("genes_id","=",id)],context=context)
                old_type={}
                if type_ids:
                    for t in self.pool.get("rhwl.easy.genes.type").browse(cr,uid,type_ids,context=context):
                        old_type[t.snp]=t.typ
                is_ok=True #判断全部位点是否有值
                for k in snp.keys():
                    v=str(sh.cell_value(i,k)).split(".")[0]
                    if old_type.has_key(snp.get(k)):
                        if old_type[snp.get(k)]=="N/A":
                            old_type[snp.get(k)]=v
                        if v=="N/A":
                            v=old_type[snp.get(k)]
                        if old_type[snp.get(k)] != v:
                            raise osv.except_osv(u"错误",u"基因样本编码[%s]位点[%s]原来的值为[%s],现在的值为[%s],请确认原因。"%(no,snp.get(k),old_type[snp.get(k)],v))
                    val={
                        "genes_id":id[0],
                        "snp":snp.get(k),
                        "typ": v,
                    }
                    self.pool.get("rhwl.easy.genes.type").create(cr,uid,val,context=context)
                    if v=="N/A":is_ok=False
                self.pool.get("rhwl.easy.genes").action_state_ok(cr,uid,id,context=context)
                if type_ids:
                    self.pool.get("rhwl.easy.genes.type").write(cr,uid,type_ids,{"active":False},context=context)


        finally:
            f.close()
            os.remove(xlsname+'.xls')

        return

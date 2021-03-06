# -*- coding: utf-8 -*-

import threading
from openerp.osv import osv,fields
import base64
from tempfile import NamedTemporaryFile
import xlrd,os
import datetime
import logging
import rhwl_gene_check
_logger = logging.getLogger(__name__)
class rhwl_import(osv.osv_memory):
    _name = 'rhwl.genes.import'
    _columns = {
        "file_bin":fields.binary(string=u"样本信息文件名"),
        "file_bin2":fields.binary(string=u"质检结果文件"),
        "file_bin3":fields.binary(string=u"位点结果文件"),
        "is_over":fields.boolean(u"是否覆盖已转入数据?")
    }
    _defaults={
        "is_over":False
    }

    def date_trun(self,val):
        if not val:
            return fields.date.today()
        if isinstance(val,str):val=val.replace(".","/")
        if list(str(val)).count("/")==0:

            d=xlrd.xldate_as_tuple(int(val),0)
            return "%s/%s/%s"%(d[0],d[1],d[2])
        if list(str(val)).count("/")==1:
            val=val.split("/")[0]
            return val[:4]+'/'+val[4:6]+'/'+val[6:8]
        else:
            return val.replace(".","/")

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
                idt=sh.cell_value(i-1,4)
                val={
                    "date":date_col,
                    "cust_name":sh.cell_value(i-1,1).encode("utf-8").replace(".","·").replace("▪","·"),
                    "sex": 'T' if sh.cell_value(i-1,2)==u"男" else 'F',
                    "name":sh.cell_value(i-1,3),
                    "identity":idt,
                    "is_child":True if len(idt)==18 and int(idt[6:10])>=(datetime.datetime.today().year-12) and int(idt[6:10])<(datetime.datetime.today().year) else False,
                    "receiv_date":self.datetime_trun(sh.cell_value(i-1,5))
                }
                if idt and len(idt)==18:
                    try:
                        val["birthday"] = datetime.datetime.strptime(idt[6:14],"%Y%m%d").strftime("%Y/%m/%d")
                    except:
                        pass
                if batch_no.get(date_col):
                    val["batch_no"]=batch_no.get(date_col)
                else:
                    cr.execute("select max(batch_no) from rhwl_easy_genes where cust_prop='tjs'")
                    max_no="0"
                    for no in cr.fetchall():
                        max_no = no[0]
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
            b=this.file_bin2.decode('base64')
            f.write(b)
            f.close()

            try:
                bk = xlrd.open_workbook(xlsname+".xls")
                sh = bk.sheet_by_index(0)
            except:
               raise osv.except_osv(u"打开出错",u"请确认质检数据文件格式是否为正确的报告标准格式。")
            nrows = sh.nrows
            genes_ids=[]
            for i in range(2,nrows):
                no=sh.cell_value(i,1)
                if not no:continue
                if type(no)==type(1.0):no = no.__trunc__()
                id=self.pool.get("rhwl.easy.genes").search(cr,uid,[("name","=",no)],context=context)
                if not id:
                    raise osv.except_osv(u"错误",u"基因编号[%s]不存在."%(no,))
                if genes_ids.count(id[0])>0:
                    raise osv.except_osv(u"错误",u"基因编号[%s]在Excel中存在多笔。"%(no,))
                genes_ids.append(id[0])
                self.pool.get("rhwl.easy.genes").write(cr,uid,id,{"log":[[0,0,{"note":u"导入质检数据","data":"DNA"}]]},context=context)
                obj_ids = self.pool.get("rhwl.easy.genes.check").search(cr,uid,[("genes_id.name",'=',no)],context=context)
                if obj_ids:
                    self.pool.get("rhwl.easy.genes.check").write(cr,uid,obj_ids,{"active":False})
                t1=sh.cell_value(i,4)
                t2=sh.cell_value(i,5)
                t3=sh.cell_value(i,6)
                t4=sh.cell_value(i,8)
                if not t4:t4=0
                val={
                        "genes_id":id[0],
                        "date":self.date_trun(sh.cell_value(i,0)),
                        "dna_date":self.date_trun(sh.cell_value(i,2)),
                        "concentration":round(t1,2),
                        "lib_person":sh.cell_value(i,3),
                        "od260_280":round(t2,2),
                        "od260_230":round(t3,2),
                        "chk_person":sh.cell_value(i,7),
                        "data_loss":str(round(t4,4)*100)+"%",
                        "loss_person":sh.cell_value(i,9),
                        "loss_date":self.date_trun(sh.cell_value(i,10)),
                        "active":True,
                    }

                self.pool.get("rhwl.easy.genes.check").create(cr,uid,val,context=context)

                if (t4>0.01):
                    self.pool.get("rhwl.easy.genes").action_state_dna(cr,uid,id,context=context)
                else:
                    genes_obj = self.pool.get("rhwl.easy.genes").browse(cr,uid,id,context=context)
                    if genes_obj.state in ('except_confirm','confirm'):
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
        over_no=[] #记录重复转入的样本号
        fileobj = NamedTemporaryFile('w+',delete=True)
        xlsname =  fileobj.name
        f=open(xlsname+'.xls','wb')
        fileobj.close()
        try:
            #fileobj.write(base64.decodestring(this.file_bin.decode('base64')))
            b=this.file_bin3.decode('base64')
            f.write(b)
            f.close()
            try:
                bk = xlrd.open_workbook(xlsname+".xls")
                sh = bk.sheet_by_index(0)
            except:
               raise osv.except_osv(u"打开出错",u"请确认位点数据文件格式是否为正确的报告标准格式。")
            nrows = sh.nrows
            ncols = sh.ncols
            snp={}
            for i in range(1,ncols):
                v=sh.cell_value(0,i)
                if not v:continue
                if not rhwl_gene_check.snp_check.has_key(v):
                    raise osv.except_osv(u"错误",u"转入数据中的位点名称[%s]不正确。" %(v,))
                snp[i]=v

            genes_ids=[]
            for i in range(1,nrows):
                no=sh.cell_value(i,0)
                if not no:continue
                id=self.pool.get("rhwl.easy.genes").search(cr,uid,[("name","=",no)],context=context)
                if not id:
                    raise osv.except_osv(u"错误",u"基因样本编码[%s]不存在。"%(no,))
                if genes_ids.count(id[0])>0:
                    raise osv.except_osv(u"错误",u"基因编号[%s]在Excel中存在多笔。"%(no,))
                genes_ids.append(id[0])
                self.pool.get("rhwl.easy.genes").write(cr,uid,id,{"log":[[0,0,{"note":u"导入位点数据","data":"SNP"}]]},context=context)
                type_ids = self.pool.get("rhwl.easy.genes.type").search(cr,uid,[("genes_id","=",id[0])],context=context)
                old_type={}
                if type_ids:
                    over_no.append(no)
                    for t in self.pool.get("rhwl.easy.genes.type").browse(cr,uid,type_ids,context=context):
                        old_type[t.snp]=t.typ
                is_ok=True #判断全部位点是否有值
                for k in snp.keys():
                    v=str(sh.cell_value(i,k)).split(".")[0].replace("/","")
                    if old_type.has_key(snp.get(k)):
                        if old_type[snp.get(k)]=="N/A":
                            old_type[snp.get(k)]=v
                        if v=="N/A":
                            v=old_type[snp.get(k)]
                        if this.is_over==False and old_type[snp.get(k)] != v:
                            raise osv.except_osv(u"错误",u"基因样本编码[%s]位点[%s]原来的值为[%s],现在的值为[%s],请确认原因。"%(no,snp.get(k),old_type[snp.get(k)],v))
                    for s in list(v.replace("/","")):
                        if rhwl_gene_check.snp_check[snp.get(k)].count(s)==0:
                            raise osv.except_osv(u"错误",u"基因样本编码[%s]的位点[%s]数据是[%s]，不能通过检验。"%(no,snp.get(k),v))
                    if snp.get(k) in ('GSTM1','GSTT1') and len(v)!=1:
                        raise osv.except_osv(u"错误",u"基因样本编码[%s]的位点[%s]数据是[%s]，不能通过检验。"%(no,snp.get(k),v))
                    if snp.get(k) not in ('GSTM1','GSTT1') and len(v)!=2:
                        raise osv.except_osv(u"错误",u"基因样本编码[%s]的位点[%s]数据是[%s]，不能通过检验。"%(no,snp.get(k),v))

                    val={
                        "genes_id":id[0],
                        "snp":snp.get(k),
                        "typ": v.replace("/",""),
                    }
                    self.pool.get("rhwl.easy.genes.type").create(cr,uid,val,context=context)
                    if v=="N/A":is_ok=False
                self.pool.get("rhwl.easy.genes").action_state_ok(cr,uid,id,context=context)
                if type_ids:
                    self.pool.get("rhwl.easy.genes.type").write(cr,uid,type_ids,{"active":False},context=context)
            if this.is_over==False and over_no:
                raise osv.except_osv(u"错误",u"基因样本编码[%s]的位点数据有重复。"%(','.join(over_no)))

        finally:
            f.close()
            os.remove(xlsname+'.xls')

        return

    def import_report4(self,cr,uid,ids,context=None):
        self.import_report2(cr,uid,ids,context=context)
        self.import_report3(cr,uid,ids,context=context)
        return

    def import_report10(self, cr, uid, ids, context=None):
        """接收检测点位数据"""
        if context is None:
            context = {}
        this = self.browse(cr, uid, ids[0])
        over_no=[] #记录重复转入的样本号
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
               raise osv.except_osv(u"打开出错",u"请确认位点数据文件格式是否为正确的报告标准格式。")
            nrows = sh.nrows
            ncols = sh.ncols
            snp={}
            for i in range(1,ncols):
                v=sh.cell_value(0,i)
                if not v:continue
                snp[i]=v

            genes_ids=[]
            for i in range(1,nrows):
                no=sh.cell_value(i,0)
                if not no:continue
                id=self.pool.get("rhwl.easy.genes.new").search(cr,uid,[("name","=",no)],context=context)
                if not id:
                    raise osv.except_osv(u"错误",u"基因样本编码[%s]不存在。"%(no,))
                if genes_ids.count(id[0])>0:
                    raise osv.except_osv(u"错误",u"基因编号[%s]在Excel中存在多笔。"%(no,))
                genes_ids.append(id[0])
                self.pool.get("rhwl.easy.genes.new").write(cr,uid,id,{"log":[[0,0,{"note":u"导入位点数据","data":"SNP"}]]},context=context)
                type_ids = self.pool.get("rhwl.easy.genes.new.type").search(cr,uid,[("genes_id","=",id[0])],context=context)
                old_type={}
                if type_ids:
                    over_no.append(no)
                    for t in self.pool.get("rhwl.easy.genes.new.type").browse(cr,uid,type_ids,context=context):
                        old_type[t.snp]=t.typ
                is_ok=True #判断全部位点是否有值
                for k in snp.keys():
                    v=str(sh.cell_value(i,k)).split(".")[0].replace("/","")
                    if old_type.has_key(snp.get(k)):
                        if old_type[snp.get(k)]=="N/A":
                            old_type[snp.get(k)]=v
                        if v=="N/A":
                            v=old_type[snp.get(k)]
                        if this.is_over==False and old_type[snp.get(k)] != v:
                            raise osv.except_osv(u"错误",u"基因样本编码[%s]位点[%s]原来的值为[%s],现在的值为[%s],请确认原因。"%(no,snp.get(k),old_type[snp.get(k)],v))

                    val={
                        "genes_id":id[0],
                        "snp":snp.get(k),
                        "typ": v.replace("/",""),
                    }
                    self.pool.get("rhwl.easy.genes.new.type").create(cr,uid,val,context=context)
                    if v=="N/A":is_ok=False
                self.pool.get("rhwl.easy.genes.new").write(cr,uid,id,{"batch_no":"YG"+datetime.datetime.now().strftime("%y%m%d")},context=context)
                self.pool.get("rhwl.easy.genes.new").action_state_ok(cr,uid,id,context=context)
                if type_ids:
                    self.pool.get("rhwl.easy.genes.new.type").write(cr,uid,type_ids,{"active":False},context=context)
            if this.is_over==False and over_no:
                raise osv.except_osv(u"错误",u"基因样本编码[%s]的位点数据有重复。"%(','.join(over_no)))

        finally:
            f.close()
            os.remove(xlsname+'.xls')

        return
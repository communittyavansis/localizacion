# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2010 moylop260 - http://www.hesatecnica.com.com/
#    All Rights Reserved.
#    info skype: german_442 email: (german.ponce@hesatecnica.com)
############################################################################
#    Coded by: german_442 email: (german.ponce@hesatecnica.com)
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


from openerp.osv import fields, osv
import time
import dateutil
import dateutil.parser
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
import openerp
import calendar
import tempfile
from xml.dom import minidom
import os
import base64
import hashlib
import tempfile
import os
import codecs


class send_massive_invoice(osv.osv_memory):
    _name = 'send.massive.invoice'
    _description = 'Envio Masivo de Facturas y XML'
    _columns = {
            'ok': fields.boolean('Adjuntar Facturas')
            }
    _defaults = {  
        'ok': True,
        }

    def send_massive(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi invoice template message loaded by default
        '''
        #self.attachment_invoice(cr, uid, ids, context=None)
        active_ids = context and context.get('active_ids', False)
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'hesatec_attachment_cfdi_jasper_tms', 'email_template_edi_invoice_jasper')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False 
        ctx = dict(context)

        attachment_ids = []
        if active_ids:
            wizard_facturae = self.pool.get('ir.attachment.facturae.mx')
            wizard_ids = wizard_facturae.search(cr, uid, [('model_source','=','account.invoice'),('id_source','in',tuple(active_ids))])
            if wizard_ids:
                for wizard in wizard_facturae.browse(cr, uid, wizard_ids, context=None):
                    if wizard.file_xml_sign.id:
                        attachment_ids.append(wizard.file_xml_sign.id)
                    if wizard.file_pdf.id:
                        attachment_ids.append(wizard.file_pdf.id)
                    if not wizard.file_pdf.id:
                        file_xml_sign = wizard.file_xml_sign.name.split('.')[0] if wizard.file_xml_sign.name else ''
                        if file_xml_sign:
                            attachment_obj = self.pool.get('ir.attachment')
                            attachment_pdf_id = attachment_obj.search(cr, uid,[('name','=',file_xml_sign+'.pdf')])
                            if attachment_pdf_id:
                                attachment_ids.append(attachment_pdf_id[0])

            attachment_not_repeat_ids = []
            [attachment_not_repeat_ids.append(key) for key in attachment_ids if key not in attachment_not_repeat_ids]
            attachment_ids_str = str(attachment_not_repeat_ids).replace('[','').replace(']','')
            ## ESCRIBIENDO LA CADENA EN LA PRIMER FACTURA
            self.pool.get('account.invoice').write(cr, uid, active_ids,{'loaded_attachment_ids':attachment_ids_str}, context=None)

        # attachment_ids = self.pool.get('ir.attachment').search(cr, uid, [('res_model','=','account.invoice'),('res_id','=',ids[0])], context=context)
        
        ctx.update({
            'default_model': 'account.invoice',
            'default_res_id': active_ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_invoice_as_sent': True,
            'attachment_ids': [x for x in attachment_not_repeat_ids],
            'massive_send': True,
            })
        
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

send_massive_invoice()

class account_invoice(osv.osv):
    _inherit ='account.invoice'
    _columns = {
            'loaded_attachment_ids': fields.text('IDS Adjuntos para el Mail'),
    }
    def copy(self, cr, uid, id, default={}, context=None):
        if context is None:
            context = {}
        default.update({
            'loaded_attachment_ids': False,
        })
        return super(account_invoice, self).copy(cr, uid, id, default, context)

account_invoice()

class mail_compose_message(osv.TransientModel):
    _name = 'mail.compose.message'
    _inherit = 'mail.compose.message'
    _description = 'Email composition wizard'
    _columns = {
    }

    def onchange_attachments(self, cr, uid, ids, attachment_ids, model, res_id, context=None):
        res = super(mail_compose_message,self).onchange_attachments(cr, uid, ids, attachment_ids, model, res_id, context)
        if model == 'account.invoice':
            account_obj = self.pool.get('account.invoice')
            for account in account_obj.browse(cr, uid, [res_id], context=None):
                if account.loaded_attachment_ids:
                    try:
                        new_attachment_ids = account.loaded_attachment_ids.split(',')
                        res.update({"value": {"attachment_ids": [(6, 0, [int(x) for x in new_attachment_ids])]}})
                        ### DESMARCAMOS LAS FACTURAS PARA QUE SE PUEDAN ENVIAR INDIVIDUALMENTE
                        invoice_ids = account_obj.search(cr, uid, [('loaded_attachment_ids','=',account.loaded_attachment_ids)], context=context)
                        if invoice_ids:
                            account_obj.write(cr, uid, invoice_ids, {'loaded_attachment_ids':False})
                        return res
                    except:
                        return res
        return res
    # def onchange_attachments(self, cr, uid, ids, attachment_ids, model, res_id, context=None):
    #     ir_attachment_obj = self.pool.get('ir.attachment')
    #     res = super(mail_compose_message,self).onchange_attachments(cr, uid, ids, attachment_ids, model, res_id, context)
    #     if model == 'account.invoice':
    #         account_obj = self.pool.get('account.invoice')
    #         for account in account_obj.browse(cr, uid, [res_id], context):
    #             if account.loaded_attachment_ids:
    #                 # for attachment in ir_attachment_obj.browse(cr, uid, [attachment_ids[0][1]], context=context):
    #                 #     try:
    #                 #         account_invoice_ids = [attachment.res_id]
    #                 #         if not attachment.res_id:
    #                 #             attachment_replace = attachment.name.replace('.','_')
    #                 #             attachment_split = attachment_replace.split('_')
    #                 #             number = str(attachment_split[2])
    #                 #             if attachment_split[1]:
    #                 #                 account_invoice_ids = account_obj.search(cr, uid, [('number','=',number)], context=context)
    #                 #                 if account_invoice_ids:
    #                 #                     account_br = account_obj.browse(cr, uid, account_invoice_ids, context=None)[0]
    #                 #                     if account_br.loaded_attachment_ids:
    #                 try:
    #                     new_attachment_ids = account.loaded_attachment_ids.split(',')
    #                     res.update({"value": {"attachment_ids": [(6, 0, [int(x) for x in new_attachment_ids])]}})
    #                     ### DESMARCAMOS LAS FACTURAS PARA QUE SE PUEDAN ENVIAR INDIVIDUALMENTE
    #                     invoice_ids = account_obj.search(cr, uid, [('loaded_attachment_ids','=',account.loaded_attachment_ids)], context=context)
    #                     if invoice_ids:
    #                         account_obj.write(cr, uid, invoice_ids, {'loaded_attachment_ids':False})
    #                     return res
    #                 except:
    #                     return res
    #                     # except:
    #                     #     return res
    #     return res  # Los onchange retornan siempre la estructura{"value": {diccionario de valores a actualizar}}

mail_compose_message()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

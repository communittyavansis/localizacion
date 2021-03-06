# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Interconsulting S.A e Innovatecsa SAS.
#    (<http://www.interconsulting.com.co).
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
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import time
from datetime import datetime, timedelta
from openerp import netsvc
from openerp import tools
from openerp.tools.translate import _

class hr_expense_expense(osv.osv):
      _inherit = "hr.expense.expense"
      _columns = {
            'type': fields.many2one('hr.expense.type','Tipo', help="Tipo de gasto"),
            'advance_id': fields.many2one('hr.expense.advances', 'Anticipo' , required=True),

      }

      def onchange_type(self, cr, uid, ids, type, context=None):

        emp_obj = self.pool.get('hr.expense.type').browse(cr, uid, type, context=context)
        journal_id = False
        print emp_obj.journal_id.name
        if emp_obj.journal_id:
            journal_id = emp_obj.journal_id.id
        return {'value': {'journal_id': journal_id}}


class hr_payslip (osv.osv):
      _name = "hr.payslip"
      _inherit = "hr.payslip"
      _columns = {
            'advance_id': fields.many2one('hr.expense.advances', 'Anticipo' ),
      } 


class hr_expense_type(osv.osv):
      _name = "hr.expense.type"
      _columns = {
                'name': fields.char('Name',size=100),
                'code': fields.char('Code',size=20),
                'journal_id': fields.many2one('account.journal', 'Diario' ),
                'type':fields.selection([ ('anticipo', 'Anticipo'),
                                  ('tarjeta_credito', 'Tarjeta Credito'),
                                  ('rembolso_gastos', 'Reembolso Gastos'),
                                  ('rembolso_caja_menor', 'Reembolso Caja Menor'),
                                  ], 'Tipo', select=True, ),


      }
      _sql_constraints = [
                ('code_uniq', 'unique (code)', 'The code must be unique !')
      ]


class hr_expense_line(osv.osv):
      _inherit = "hr.expense.line"
      _columns = {
        'partner_id' : fields.many2one ('res.partner','Tercero', help="Tercero"),

      }

class res_company(osv.osv):
      _inherit = 'res.company'
    
      _columns = {
        'vencimiento_anticipo': fields.float('Dias vencimiento anticipo', help="Los dias sumados a la fecha fin de un anticipo para calcular la fecha de vencimiento", digits_compute=dp.get_precision('Account')),
        'giro_anticipo': fields.float('Dias pago anticipo', help="Los dias restados a la fecha inicio de un anticipo para calcular la fecha de giro", digits_compute=dp.get_precision('Account')),
        'mensaje_aviso': fields.html('Mensaje de Aviso Anticipos', help="Saldra antes de que se pueda realizar un anticipo"),
      }


class hr_job(osv.osv):
      _inherit = 'hr.job'
    
      _columns = {
        'advance_max_amount': fields.float('Monto maximo de anticipo', digits_compute=dp.get_precision('Account') ),
      }
    
class hr_employee(osv.osv):
      _inherit = 'hr.employee'
      
      _columns = {
        'advance_max_amount': fields.related('job_id','advance_max_amount',type="float", digits_compute=dp.get_precision('Account'),string="Monto maximo de anticipo",readonly=True),
      }

class account_voucher(osv.osv):
      _inherit = 'account.voucher'
    
      _columns = {

        'advance_id': fields.many2one('hr.expense.advances', 'Anticipo'),

      }


class account_move_line(osv.osv):
      _name = "account.move.line"
      _inherit = "account.move.line"
      _columns = {

        'advance_id': fields.many2one('hr.expense.advances', 'Anticipo'),

      }


class hr_payslip_advance(osv.osv):
      _name = "hr.payslip.advance"
      _description = "Anticipo Empleado"
    
      def _check_amounts(self, cr, uid, ids, context=None):
        for advance in self.browse(cr, uid, ids, context):
            if advance.amount_discount < 0 or  advance.amount_discount > advance.amount_total:
                return False
        return True
    
      _columns = {
        'advance_id': fields.many2one('hr.expense.advances', 'Anticipo', required=True, readonly=True, ondelete='cascade'),
        'payslip_id': fields.many2one('hr.payslip', 'Nomina', required=True, readonly=True, ondelete='cascade'),
        'amount_total': fields.float('Valor', digits_compute=dp.get_precision('Account'), required=True, readonly=True),
        'amount_discount': fields.float('Valor Descontado', digits_compute=dp.get_precision('Account'), required=True),
        'manual': fields.boolean('Manual'),
        # 'journal_id': fields.related('journal_id','payslip_id',type="many2one",relation="account.journal",string="Journal", readonly=True, store=True),
        'period_id': fields.related('payslip_id','payslip_period_id',type="many2one",relation="payslip.period", string="Periodo", readonly=True, store=True),
        'state': fields.related('payslip_id', 'state', type="char", string="Estado", readonly=True, store=True),
        'account_id': fields.many2one('account.account', 'Account', readonly=True),
      }
    
      _defaults = {
          'manual': False,
      }
    
      _constraints = [
        (_check_amounts, 'El valor a descontar no puede ser menor a 0 ni mayor al valor total', ['amount_discount']),
      ]
        


class payslip_period(osv.osv):
      _name = "payslip.period"
      _description = "Payslip period"
    
      def get_schedule_days(self, cr ,uid, schedule_pay, context=None):
        dias_dif = 0
        if schedule_pay=='weekly':
            dias_dif = 7
        elif schedule_pay=='bi-monthly':
            dias_dif = 15
        elif schedule_pay=='monthly':
            dias_dif = 30
        elif schedule_pay=='dualmonth':
            dias_dif = 60
        elif schedule_pay=='quarterly':
            dias_dif = 120
        elif schedule_pay=='semi-annually':
            dias_dif = 180
        elif schedule_pay=='annually':
            dias_dif = 360
            
        return dias_dif
    
      _columns = {
                'name':fields.char("Nombre" , size = 32 , required = True),
                'start_date':fields.date("Comienzo de Corte" , required = True),
                'end_date':fields.date("Fin de Corte" , required = True),							
                'start_period':fields.date("Comienzo del Periodo" , required = True),
                'end_period':fields.date("Fin del Periodo" , required = True),
                
                'schedule_pay': fields.selection([
                    ('weekly', 'Semanal'),
                    ('bi-monthly', 'Quincenal'),
                    ('monthly', 'Mensual'),
                    ('dualmonth', 'Cada 2 Meses'),
                    ('quarterly', 'Cada Cuatro meses'),
                    ('semi-annually', 'Cada 6 Meses'),
                    ('annually', 'Anual'),
                    ], 'Pago Planificado', select=True, required=True),
      }  


class hr_expense_advances(osv.osv):
      _name = "hr.expense.advances"
      _description = "Anticipos"
      _inherit = ['mail.thread']

      def get_contract(self, cr, uid, employee, date_from, date_to, context=None):
        """
        @param employee: browse record of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        contract_obj = self.pool.get('hr.contract')
        clause = []
        #a contract is valid if it ends between the given dates
        clause_1 = ['&',('date_end', '<=', date_to),('date_end','>=', date_from)]
        #OR if it starts between the given dates
        print "Estoy en el contrato"
        print clause_1
        clause_2 = ['&',('date_start', '<=', date_to),('date_start','>=', date_from)]
        #OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&',('date_start','<=', date_from),'|',('date_end', '=', False),('date_end','>=', date_to)]
        clause_final =  [('employee_id', '=', employee.id),'|','|'] + clause_1 + clause_2 + clause_3
        contract_ids = contract_obj.search(cr, uid, clause_final, context=context)
        return contract_ids


      def onchange_employee_id(self, cr, uid, ids,date_from, date_to, employee_id=False, contract_id=False, context=None):
        empolyee_obj = self.pool.get('hr.employee')
        contract_obj = self.pool.get('hr.contract')

        res = {'value':{


                      'struct_id': False,
                      }
            }



        if (not employee_id) or (not date_from) or (not date_to):
            return res

        employee_id = empolyee_obj.browse(cr, uid, employee_id, context=context)

        if not context.get('contract', False):
            #fill with the first contract of the employee
            contract_ids = self.get_contract(cr, uid, employee_id, date_from, date_to, context=context)
        else:
            if contract_id:
                #set the list of contract for which the input have to be filled
                contract_ids = [contract_id]
            else:
                #if we don't give the contract, then the input to fill should be for all current contracts of the employee
                contract_ids = self.get_contract(cr, uid, employee_id, date_from, date_to, context=context)

        if not contract_ids:
            return res
        contract_record = contract_obj.browse(cr, uid, contract_ids[0], context=context)

        res['value'].update({
                    'contract_id': contract_record and contract_record.id or False,
                    'parent_id': employee_id.parent_id.id or False
        })


        return res

      def _check_terminos(self, cr, uid, ids, context=None):
          for advance in self.browse(cr, uid, ids, context=context):
            if advance.terminos_y_condiciones != True:
                return False
          return True
        
      def _check_amount_max(self, cr, uid, ids, context=None):
          for advance in self.browse(cr, uid, ids, context=context):
              if (advance.amount*advance.tasa_cambio > advance.employee_id.advance_max_amount and advance.state=='draft'):
                 return False
          return True

      def _get_local_currency_total(self, cr, uid, ids, name, args, context=None):
          if context is None:
            context = {}
          res = {}
          for prestamo in self.browse(cr, uid, ids, context):
            res[prestamo.id] = prestamo.amount*prestamo.tasa_cambio
          return res
        
      def _check_advances(self, cr, uid, ids, context=None):
          return True




      def _expire_date(self, cr, uid, ids, name, args, context=None):
          if context is None:
              context = {}
          res = {}
          for prestamo in self.browse(cr, uid, ids, context):
            end_date = datetime.strptime(prestamo.end_date, DEFAULT_SERVER_DATE_FORMAT).date()
            expire_date = str(end_date + timedelta(days=prestamo.employee_id.user_id.company_id.vencimiento_anticipo))
            res[prestamo.id] = expire_date
          return res

   
      _columns = {
        'name': fields.char('Name',size=100),
        'employee_id': fields.many2one('hr.employee', 'Empleado', required=True, on_change="onchange_employee_id(contract_id,parent_id)" ),
        'contract_id': fields.many2one('hr.contract', 'Contrato',   ),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'user_valid': fields.many2one('res.users', 'Validation By', readonly=True, copy=False,),
        'parent_id': fields.related('employee_id','parent_id',type="many2one",relation="hr.employee",string="Director", readonly=True ,store=True),
        'currency_id': fields.many2one('res.currency', 'Moneda', required=True,  ),
        'tasa_cambio' : fields.float("Tasa Cambio", digits=(20,12), ),
        'amount': fields.float('Valor', digits_compute=dp.get_precision('Account'), required=True, ),
        'total_local': fields.function(_get_local_currency_total, type="float", string="En Moneda Local", digits_compute=dp.get_precision('Account'),  store=True),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Centro de Costo', ),
        'multicurrency': fields.boolean('Multimoneda'),
        'request_date': fields.date('Fecha solicitud',  required=True, ),
        'approve_date': fields.date('Fecha de aprobacion',  readonly=True ),
        'start_date': fields.date('Fecha de inicio', required=True, ),
        'end_date': fields.date('Fecha de fin', required=True, track_visibility='onchange'),
        'terminos_y_condiciones': fields.boolean('Acepto Terminos y Condiciones', readonly=True, states={'draft': [('readonly', False)]}),
        'mensaje_aviso': fields.html('Mensaje de Aviso Anticipos', help="Saldra antes de que se pueda realizar un anticipo", readonly=True),
        'expire_date': fields.function(_expire_date, type="date", string="Fecha de vencimiento", readonly=True, store=True),
        'state': fields.selection([
            ('draft', 'Borrador'),
            ('cancelled', 'Cancelado'),
            ('confirm', 'Pendiente de Aprobación'),
            ('accepted', 'Aprobado'),
            ('paid', 'Pagado'),
            ('done', 'Legalizado'),
            ],
            'Status', readonly=True, track_visibility='onchange', copy=False,
            help='When the advance request is created the status is \'Draft\'.\n It is confirmed by the user and request is sent to admin, the status is \'Waiting Confirmation\'.\
            \nIf the admin accepts it, the status is \'Accepted\'.\n If the accounting entries are made for the advance request, the status is \'Waiting Payment\'.'),
        'description': fields.text('Descripcion', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'expense_id': fields.many2one('hr.expense.advances', 'Legalizacion', readonly=True),
        'voucher_id': fields.many2one('account.voucher', 'Pago de anticipo', readonly=True),
        'account_move_id': fields.many2one('account.move', 'Asiento contable', copy=False),
        'account_move_line_id': fields.many2one('account.move.line', 'Linea a reconciliar', readonly=True),
        'account_move_line_refund_id': fields.many2one('account.move.line', 'Linea a reconciliar reembolso', readonly=True),
        'journal_bank_id': fields.many2one('account.journal', 'Diario Banco', readonly=True, states={'validated': [('readonly', False)]}, domain=[('type','in',['bank', 'cash']),('recaudo','=',False)]),
        'journal_advance_id': fields.many2one('account.journal', 'Diario Anticipo', readonly=True, states={'draft': [('readonly', False)]}  , required=True),
        'pay_date': fields.date('Fecha de Pago', readonly=True, states={'waiting_approval': [('readonly', False)], 'validated': [('readonly', False),('required', True)]}, store=True, track_visibility='onchange'),
        'accounting_date': fields.date('Fecha Causacion', readonly=True),
        'account_recivable_id': fields.many2one('account.account', 'Cuenta Cobro', readonly=True),
        'account_payable_id': fields.many2one('account.account', 'Cuenta Pago', readonly=True),
        'reconcile_id': fields.related('account_move_line_id','reconcile_id',type="many2one",relation="account.move.reconcile",string="Reconciliacion",readonly=True,store=True),
        'reconcile_refund_id': fields.related('account_move_line_refund_id','reconcile_id',type="many2one",relation="account.move.reconcile",string="Reconciliacion Reembolso",readonly=True,store=True),
        'reconcile_partial_id': fields.related('account_move_line_id','reconcile_partial_id',type="many2one",relation="account.move.reconcile",string="Reconciliacion Parcial",readonly=True,store=True),
        'reconcile_partial_refund_id': fields.related('account_move_line_refund_id','reconcile_partial_id',type="many2one",relation="account.move.reconcile",string="Reconciliacion Parcial Reembolso",readonly=True,store=True),
        'move_refund_id': fields.many2one('account.move', 'Comprobante Para Reembolso', readonly=True),
        'advance_max_amount': fields.related('employee_id','advance_max_amount',type="float", digits_compute=dp.get_precision('Account'), string="Monto maximo de anticipo", readonly=True, store=True),
        'move_egress_id': fields.many2one('account.move', 'Comprobante Egreso', readonly=True),
        'move_validate_id': fields.many2one('account.move', 'Comprobante Validacion', readonly=True),
        'expense_ids':fields.one2many('hr.expense.expense','advance_id','Legalizaciones', readonly=True, states={'to_pay': [('readonly', False)]}),
        'advance_payslip_ids':fields.one2many('hr.payslip.advance','advance_id','Nominas', readonly=True, ondelete='cascade'),
        }
    

    
      _constraints = [
        (_check_advances, 'El empleado tiene ya un anticipo en proceso', ['employee_id']),
        (_check_terminos, 'Tiene que aceptar los terminos y condiciones de un anticipo', ['terminos_y_condiciones']),
        (_check_amount_max, 'El monto excede el monto maximo de anticipo', ['amount','tasa_cambio']),
        ]

      _defaults = {
        'mensaje_aviso': lambda s, cr, uid, c: s.pool.get('res.users').browse(cr, uid, uid, c).company_id.mensaje_aviso,

        'request_date': datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT),
        'state': 'draft',
#        'employee_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).employee_id and self.pool.get('res.users').browse(cr, uid, uid, c).employee_id.id or False,
        'currency_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.currency_id.id,
        'tasa_cambio': 1,
      }

      def account_move_get(self, cr, uid, expense_id, context=None):
        '''
        This method prepare the creation of the account move related to the given expense.

        :param expense_id: Id of expense for which we are creating account_move.
        :return: mapping between fieldname and value of account move to create
        :rtype: dict
        '''
        journal_obj = self.pool.get('account.journal')
        expense = self.browse(cr, uid, expense_id, context=context)
        company_id = expense.company_id.id
        date = expense.approve_date
        ref = expense.name
        journal_id = False
        if expense.journal_advance_id:
            journal_id = expense.journal_advance_id.id
        else:
            journal_id = journal_obj.search(cr, uid, [('type', '=', 'purchase'), ('company_id', '=', company_id)])
            if not journal_id:
                raise osv.except_osv(_('Error!'), _("No expense journal found. Please make sure you have a journal with type 'purchase' configured."))
            journal_id = journal_id[0]
        return self.pool.get('account.move').account_move_prepare(cr, uid, journal_id, date=date, ref=ref, company_id=company_id, context=context)
    

      def advances_confirm(self, cr, uid, ids, context=None):
          print " Estoy en confirm "
          for advances in self.browse(cr, uid, ids):
              if advances.employee_id and advances.employee_id.parent_id.user_id:
                  self.message_subscribe_users(cr, uid, [advances.id], user_ids=[advances.employee_id.parent_id.user_id.id])
          return self.write(cr, uid, ids, {'state': 'confirm', 'approve_date': time.strftime('%Y-%m-%d')}, context=context)

      def advances_accept(self, cr, uid, ids, context=None):
          print " Estoy en accept "
          move_obj = self.pool.get('account.move')
          move_line_obj = self.pool.get('account.move.line')
          period_pool = self.pool.get('account.period')


          for exp in self.browse(cr, uid, ids, context=context):
            if not exp.employee_id.address_home_id:
                raise osv.except_osv(_('Error!'), _('The employee must have a home address.'))
            if not exp.employee_id.address_home_id.property_account_payable.id:
                raise osv.except_osv(_('Error!'), _('The employee must have a payable account set on his home address.'))
            if not exp.employee_id.address_home_id.property_account_receivable.id:
                raise osv.except_osv(_('Error!'), _('The employee must have a receivable account set on his home address.'))
            timenow = exp.approve_date
            search_periods = period_pool.find(cr, uid, timenow, context=context)
            period_id = search_periods[0]
 
            company_currency = exp.company_id.currency_id.id
            diff_currency_p = exp.currency_id.id <> company_currency
            
            #create the move that will contain the accounting entries
            move_id = move_obj.create(cr, uid, self.account_move_get(cr, uid, exp.id, context=context), context=context)
        
            #one account.move.line per expense line (+taxes..)
            #eml = self.move_line_get(cr, uid, exp.id, context=context)
            eml_debit ={}
            eml_credit ={}
            #create one more move line, a counterline for the total on payable account
            #total, total_currency, eml = self.compute_expense_totals(cr, uid, exp, company_currency, exp.name, eml, context=context)
            acc = exp.employee_id.address_home_id.property_account_payable.id

            journal_id = move_obj.browse(cr, uid, move_id, context).journal_id
            # post the journal entry if 'Skip 'Draft' State for Manual Entries' is checked
            if journal_id.entry_posted:
                move_obj.button_validate(cr, uid, [move_id], context)


            eml_debit={
            'date_maturity':  False,
            'partner_id': exp.employee_id.address_home_id.id,
            'name': exp.name,
            'date': exp.approve_date,
            'debit': exp.amount  ,
            'credit': 0.00,
            #'account_id': exp.employee_id.address_home_id.property_account_payable.id,
            'account_id':exp.journal_advance_id.default_debit_account_id.id,

            'analytic_lines': False,
            'amount_currency': False,
            'currency_id': company_currency,
            'tax_code_id': False,
            'tax_amount': False,
            'ref': exp.name,
            'period_id': period_id,
            'journal_id': exp.journal_advance_id.id,
            'quantity': 1.00,
            'product_id': False,
            'product_uom_id': False,
            'analytic_account_id': False,
            'advance_id': exp.id,

        }

            eml_credit={
            'date_maturity':  False,
            'partner_id': exp.employee_id.address_home_id.id,
            'name': exp.name,
            'date': exp.approve_date,
            'debit': 0.00  ,
            'credit': exp.amount,
         #   'account_id': exp.employee_id.address_home_id.property_account_receivable.id,
            'account_id':exp.journal_advance_id.default_credit_account_id.id,

            'analytic_lines': False,
            'amount_currency': False,
            'currency_id': company_currency,
            'tax_code_id': False,
            'tax_amount': False,
            'period_id': period_id,
            'journal_id': exp.journal_advance_id.id,
            'ref': exp.name,
            'quantity': 1.00,
            'product_id': False,
            'product_uom_id': False,
            'analytic_account_id': False,
            'advance_id': exp.id,
        }

            #convert eml into an osv-valid format
            lines = [(0,0,eml_debit),(0,0, eml_credit)]
            #print lines

            move_obj.write(cr, uid, [move_id], {'line_id': lines}, context=context)

#            move_line_obj.create(cr, uid, eml_debit, context=context)

#            move_line_obj.create(cr, uid, eml_credit, context=context)

            self.write(cr, uid, ids, {'account_move_id': move_id, 'state': 'accepted'}, context=context)


          return True

      def advances_canceled(self, cr, uid, ids, context=None):
          print " Estoy en canceled "
          return self.write(cr, uid, ids, {'state': 'cancelled'}, context=context)

      def unlink(self, cr, uid, ids, context=None):
          for rec in self.browse(cr, uid, ids, context=context):
              if rec.state != 'draft':
                  raise osv.except_osv(_('Warning!'),_('You can only delete draft advance!'))
          return super(hr_expense_advances, self).unlink(cr, uid, ids, context)



      def create(self, cr, uid, vals, context=None):
          sequence=self.pool.get('ir.sequence').get(cr, uid, 'name')
          vals['name']=sequence
          return super(hr_expense_advances, self).create(cr, uid, vals, context=context)

class account_move_line(osv.osv):
      _inherit = "account.move.line"

      def reconcile(self, cr, uid, ids, type='auto', writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False, context=None):
        res = super(account_move_line, self).reconcile(cr, uid, ids, type=type, writeoff_acc_id=writeoff_acc_id, writeoff_period_id=writeoff_period_id, writeoff_journal_id=writeoff_journal_id, context=context)
        #when making a full reconciliation of account move lines 'ids', we may need to recompute the state of some hr.expense
        account_move_ids = [aml.move_id.id for aml in self.browse(cr, uid, ids, context=context)]
        expense_obj = self.pool.get('hr.expense.expense')
        advance_obj = self.pool.get('hr.expense.advances')
        currency_obj = self.pool.get('res.currency')
        if account_move_ids:
            expense_ids = expense_obj.search(cr, uid, [('account_move_id', 'in', account_move_ids)], context=context)

            for expense in expense_obj.browse(cr, uid, expense_ids, context=context):
                if expense.state == 'done':
                    #making the postulate it has to be set paid, then trying to invalidate it
                    new_status_is_paid = True
                    for aml in expense.account_move_id.line_id:
                        if aml.account_id.type == 'payable' and not currency_obj.is_zero(cr, uid, expense.company_id.currency_id, aml.amount_residual):
                            new_status_is_paid = False
                    if new_status_is_paid:
                        advance_obj.write(cr, uid, [expense.advance_id.id], {'state': 'done'}, context=context)
                        expense_obj.write(cr, uid, [expense.id], {'state': 'paid'}, context=context)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

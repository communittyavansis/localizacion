# -*- coding: utf-8 -*-

import time
from openerp.report import report_sxw
from openerp import pooler

class account_voucher(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_voucher, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
                                  'time': time,
                                  'getLines': self._lines_get,
                                  })
        self.context = context
    
    def _lines_get(self, voucher):
        voucherline_obj = pooler.get_pool(self.cr.dbname).get('account.voucher.line')
        voucherlines = voucherline_obj.search(self.cr, self.uid,[('voucher_id','=',voucher.id)])
        voucherlines = voucherline_obj.browse(self.cr, self.uid, voucherlines)
        return voucherlines
    
report_sxw.report_sxw('report.account_cheque_davivienda', 'account.voucher',
                      'addons/print_receipt/reports/account_cheque_davivienda.rml',
                      parser=account_voucher)
        
        
        
        

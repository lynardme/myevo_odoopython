#!/usr/bin/env python

import web
import json
import xmlrpclib
import ast
import datetime
import time
import yaml
import pytz
import os
import ConfigParser
from dateutil.parser import parse
from tzlocal import get_localzone
from pprint import pprint

urls = (
    # '/chicken/api/master/getfarm', 'farm',
    # '/chicken/api/master/getcompany', 'company',
    # '/chicken/api/master/getscale', 'scale',
    '/chicken/api/getmasterupdate', 'master',
    '/chicken/api/order/create', 'order_create',
)

odoo_url = 'http://localhost:8069'

# dbname[token] = 'chicken'
odoo_user = 1
#db_user_pwd[token] = db_user_pwd[token]

# odoo_url = 'http://127.0.0.1:8999'
# dbname[token] = 'chicken'
# odoo_user = 1
# db_user_pwd[token] = '1234'

err401 = {"code": "401", "errorMessage": "Unauthorized"}
err400 = {"code": "400", "errorMessage": "Bad Request"}
err403 = {"code": "403", "errorMessage": "Forbidden"}
err500 = {"code": "500", "errorMessage": "Internal Server Error"}

config = ConfigParser.RawConfigParser()
config.read('/etc/odoo/pyconfig.conf')
dbname = dict(config.items('dbname'))
db_user_pwd = dict(config.items('db_user_pwd'))
config_pda = dict(config.items('pda'))
json_dir =  '/var/spool/odoo_json/'

class order_create:
    def POST(self):
        res = None
        token = web.ctx.env.get('HTTP_AUTHORIZATION')
        sock = xmlrpclib.ServerProxy('%s/xmlrpc/object' % (odoo_url))
        token = "f71628464760afe4f80c45e7376626ce"
        author = self.check_autorization(token)
        data_post = web.data()
        # data_post = ast.literal_eval(data_post)
        print "HEADER : ", token
        print "PARAMETER : ", data_post

        # Write some json file to be replayed
        try:
            #current_dir = os.path.dirname(os.path.abspath(__file__))
            load = json.loads(data_post)
            if load['pda_do_id'] and json_dir:
                file_name = json_dir + '/' + load['pda_do_id'] + ".json"
                print "writing in  : ", file_name
                with open(file_name, 'w') as outfile:
                    json.dump(load, outfile, indent=4)
        except:
            print("An exception occurred")

        # Decode the data
        data_post = yaml.load(data_post)
        author = True
        if author == True:
            check_pda = self.check_pda(token, data_post)
            if check_pda is True:
                data = {"code": "201"}
                res_check = self.checking_request_so(token, data_post)
                if 'description' not in err400:

                    to_create = res_check['to_create']

                    # check po
                    # po_recs = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'purchase.order', 'search_read', [('pda_do_id', '=', to_create['pda_do_id'])])
                    # for rec in po_recs:
                    #     print "rec --- ", rec
                    #     return {"code": "201", "description": rec['name']}
                    # get product information
                    product = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'product.template', 'search_read',
                                      [('id', '=', data_post['product_id'])],
                                      ['name', 'standard_price','taxes_id'])
                    if product:
                        price_unit = product[0]['standard_price']
                        taxes_id = product[0]['taxes_id']
                    else:
                        err403.update({'description': 'Product Id does not exist'})
                        res = err403
                        print "RESPONSE : ", res
                        return res

                    # create customer/buyers
                    if len(res_check['new_buyers_all_line']) > 0:
                        replace_buyer_id = {}
                        buyer = {}
                        for line in res_check['new_buyers_all_line']:

                            # check new buyer
                            buyer_exist = sock.execute(dbname[token], odoo_user,
                                         db_user_pwd[token], 'res.partner', 'search',
                                         [('name', '=ilike', line['name'])]
                                         )

                            if not buyer_exist:
                                # default values for company and customer
                                line.update({'company_type':'company', 'customer': True})
                                # if country_name and state_name matched, save to country_id and state_id fields
                                country = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.country', 'search',
                                    [('name', '=ilike', line['country_name'].strip())])
                                if country:
                                    line.update({'country_id': country[0]})
                                state = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.country.state', 'search',
                                    [('name','=ilike', line['state_name'].strip())])
                                if state:
                                    line.update({'state_id': state[0]})
                                buyers_id = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.partner', 'create', line)

                                replace_buyer_id.update({line['id']: buyers_id})
                            else:
                                buyer.update({line['name']: "buyer exist, nothing added"})

                        if buyer:
                            data.update({'new_buyers': buyer})

                        # replace the temp buyer id with permanent id
                        for line in res_check['all_line']:
                            if 'buyer_id' in line and line['buyer_id'] is not None and line['buyer_id'] :
                                for key, value in replace_buyer_id.iteritems():
                                    if key == line['buyer_id']:
                                        line.update({'buyer_id': replace_buyer_id[line['buyer_id']]})

                    # check valid purchase order line
                    for line in res_check['all_line']:
                        # Test there is a buyer id
                        if not line['buyer'] or line['buyer'] is  None:
                                   continue


                        buyer_name = sock.execute(dbname[token], odoo_user,
                                         db_user_pwd[token], 'res.partner', 'search',
                                         [('name', '=ilike', line['buyer'])]
                                         )
                        if buyer_name:
                            print "found same buyer name '%s' then used the existing one" % line['buyer']
                            line.update({'buyer_id': buyer_name[0]})
                        else:
                            try:
                                buyer_id = sock.execute(dbname[token], odoo_user,
                                         db_user_pwd[token], 'res.partner', 'search_read',
                                         [('id', '=', line['buyer_id'])]
                                         )
                                if buyer_id:
                                    print "buyer_id exist hence use the existing one"
                                    line.update({'buyer': buyer_id[0]['name']})
                            except:
                                err400.update({'description': 'Invalid input syntax for buyer_id, pls create new buyer info'})
                                res = err400
                                return res

                    # create po
                    po_id = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'purchase.order', 'create', to_create)
                    # update scale last sync
                    if to_create['scale_id']:
                        sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'measure.scale', 'write', to_create['scale_id'], {'last_sync': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')})
                    # get id for kg
                    kg = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'product.uom', 'search', [('name', '=', 'kg')])

                    # create po line
                    for line in res_check['all_line']:
                        if 'product' in data_post:
                            product = data_post['product'] + ' created from PDA'
                        else:
                            product = ''
                        if 'product_id' in data_post:
                            product_id = data_post['product_id']
                        else:
                            # assume to have default product with product_id = 1, if not exist will throw an error
                            product_id = 1
                        line.update(
                            {'order_id': po_id, 'product_uom': kg[0], 'name': product, 'product_id': product_id,
                             'price_unit': price_unit, 'taxes_id': [[6, False, taxes_id]]})
                        sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'purchase.order.line', 'create', line)
                    desc = str(po_id)
                    data.update({'description': desc})
                    # confirm po
                    sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'pda.api', 'action_confirm_po', po_id)
                    # actiondone picking
                    name = self.action_done_picking(token, po_id)
                    desc = str(name)
                    data.update({'description': desc})
                    res = data
                    self.last_delivery(token, data_post['farm_id'])

                    # create sale order per buyer
                    for line in res_check['all_line']:
                        create_so = {}
                        create_so_line = {}

                        # Test there is a buyer id
                        if 'buyer_id' not in line or line['buyer_id'] is  None :
                               continue

                        buyer_id = int(line['buyer_id'])
                        so_id = sock.execute(dbname[token], odoo_user,
                                             db_user_pwd[token], 'sale.order', 'search',
                                             [('partner_id', '=', buyer_id),
                                              ('purchase_id', '=', po_id)]
                                             )

                        if not so_id:
                            create_so.update({'partner_id': buyer_id,
                                              'purchase_id': po_id,
                                              'purchase_name': name,
                                              'pda_do_id': to_create
                                              ['pda_do_id']})
                            so_id = sock.execute(dbname[token], odoo_user,
                                                 db_user_pwd[token], 'sale.order',
                                                 'create', create_so)
                        else:
                            so_id = so_id[0]
                        create_so_line = line.copy()
                        if "price_unit" in create_so_line:
                            del create_so_line["price_unit"]
                        if "buyer" in create_so_line:
                            del create_so_line["buyer"]
                        if "taxes_id" in create_so_line:
                            del create_so_line["taxes_id"]
                        if "buyer_id" in create_so_line:
                            del create_so_line["buyer_id"]
                        create_so_line.update({'order_id': so_id,
                                               'product_uom_qty':
                                               create_so_line["crate_net"]})
                        sock.execute(dbname[token], odoo_user, db_user_pwd[token],
                                     'sale.order.line', 'create',
                                     create_so_line)
                        sock.execute(dbname[token], odoo_user, db_user_pwd[token],
                                     'pda.api', 'action_confirm_so', so_id)
                else:
                    res = err400
            else:
                err403.update({'description': 'PDA ID does not exist'})
                res = err403
        else:
            res = err401
        self.pda_history(token, data_post)
        print "RESPONSE : ", res

        return res

    def check_autorization(self, token):
        sock = xmlrpclib.ServerProxy('%s/xmlrpc/object' % (odoo_url))
        print '________________sock_____________', sock
        if token in dbname:
            checktoken = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.users', 'search',
                                      [('token', '=', token)])
            if len(checktoken) >= 1:
                return True
            else:
                return "Error 401 : Unauthorized"
        else:
            return "Error 401 : Unauthorized"

    def pda_history(self, token, data):
        sock = xmlrpclib.ServerProxy('%s/xmlrpc/object' % (odoo_url))
        # company
        to_history = {}
        if 'owner_id' in data:
            company = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.company', 'search',
                                   [('name', '=', data['owner_id'])])
            if company:
                com = company[0]
                to_history.update({'owner_id': com})
            else:
                to_history.update({'owner_id': 1})
        else:
            to_history.update({'owner_id': 1})
        # pda_id
        if 'pda_id' in data:
            pda = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'pda.operation', 'search',
                               [('pda_id', '=', data['pda_id'])])
            if pda:
                pda_id = pda[0]
                to_history.update({'name': pda_id})
            # else:
            #     id = sock.execute(
            #       dbname[token], odoo_user, db_user_pwd[token], 'pda.operation', 'create',{'name' : data['pda_id']})
            #     to_history.update({'name':id})
        # last_position_long
        if 'last_position_long' in data:
            to_history.update({'last_position_long': data['last_position_long']})
        # last_position_lat
        if 'last_position_latt' in data:
            to_history.update({'last_position_latt': data['last_position_latt']})
        to_history.update(
            {'access_date': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
             'info': 'order_create',
             'data': json.dumps(data)})
        sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'pda.history', 'create', to_history)

    def check_pda(self, token, data):
        sock = xmlrpclib.ServerProxy('%s/xmlrpc/object' % (odoo_url))
        res = None
        # pda_id
        if 'pda_id' in data:
            pda = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'pda.operation', 'search',
                               [('pda_id', '=', data['pda_id'])])
            if pda:
                res = True
            else:
                res = False
        else:
            res = False
        return res

    def action_done_picking(self, token, id):
        sock = xmlrpclib.ServerProxy('%s/xmlrpc/object' % (odoo_url))
        src_doc = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'purchase.order', 'search_read', [('id', '=', id)],
                               ['name'])
        if src_doc:
            src_doc = src_doc[0]['name']
        # Do not set picking to Done
        # picking = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'stock.picking', 'search',
        #                        [('origin', '=', src_doc), ('state', 'not in', ['done', 'cancel'])], {})
        # sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'stock.picking', 'action_done', picking, {})
        return src_doc

    def last_delivery(self, token, farm):
        sock = xmlrpclib.ServerProxy('%s/xmlrpc/object' % (odoo_url))
        farm_id = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.partner', 'search', [('name', '=', farm)])
        if farm_id:
            sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.partner', 'write', farm_id[0],
                         {'last_delivery': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')})

    def checking_request_so(self, token, data):
        res = {}
        to_create = {}
        create_so = True
        sock = xmlrpclib.ServerProxy('%s/xmlrpc/object' % (odoo_url))

        # condition to reset err400
        if 'description' in err400:
            del err400['description']
        else:
            pass

        # off feeding
        if 'off_feeding' in data:
            if data['off_feeding'] == 'yes' or data['off_feeding'] == 'no':
                to_create.update({'off_feeding': data['off_feeding']})
                create_so = True
            else:
                create_so = False
                err400.update({'description': 'not valid value for off_feeding, only yes or no'})
        # water_fogging
        if 'water_fogging' in data:
            if data['water_fogging'] == 'yes' or data['water_fogging'] == 'no':
                to_create.update({'water_fogging': data['water_fogging']})
                create_so = True
            else:
                err400.update({'description': 'not valid value for water_fogging, only yes or no'})
                create_so = False
        # date
        if 'date' in data:
            date_time = datetime.datetime.strptime(data['date'], "%Y-%m-%d %H:%M:%S")
            date_time = isinstance(date_time, datetime.datetime)
            if date_time is True:
                to_create.update({'confirm_date': data['date']})
                create_so = True
            else:
                err400.update({'description': 'not valid value for date time, ex. 2016-06-21 12:00:00'})
                create_so = False
        # farm_idfarm = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.partner', 'search',[('name','=',data['farm_id'])])
        if 'farm_id' in data:
            farm = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.partner', 'search',
                                [('name', '=', data['farm_id'])])
            if farm:
                to_create.update({'partner_id': farm[0]})
                create_so = True
            else:
                create_so = False
                err400.update({'description': 'not valid value for farm_id.'})
        # scale_id
        if 'scale_id' in data:
            scale = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'measure.scale', 'search',
                                 [('name', '=', data['scale_id'])])
            if scale:
                to_create.update({'scale_id': scale[0]})
                create_so = True
            else:
                create_so = False
                err400.update({'description': 'not valid value for scale_id.'})
        # pda_id
        if 'pda_id' in data:
            pda_name = data['pda_id']
            pda = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'pda.operation', 'search',
                               [('pda_id', '=', pda_name)])
            if pda:
                to_create.update({'pda_id': pda[0]})
            else:
                id = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'pda.operation', 'create', {'name': pda_name})
                to_create.update({'pda_id': id})
            create_so = True
        else:
            err400.update({'description': 'not valid value for pda_id'})
            create_so = False
        # lory_number
        if 'lory_number' in data:
            lory_name = data['lory_number']
            lory = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'lorry.number', 'search',
                                [('name', '=', lory_name)])
            if lory:
                to_create.update({'lory_number': lory[0]})
            else:
                id = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'lorry.number', 'create', {'name': lory_name})
                to_create.update({'lory_number': id})
            create_so = True
        else:
            err400.update({'description': 'not valid value for lory_number'})
            create_so = False
        # total_crates
        if 'total_crates' in data:
            if type(data['total_crates']) == int or type(data['total_crates']) == float:
                to_create.update({'total_crates': data['total_crates']})
                create_so = True
            else:
                create_so = False
                err400.update({'description': 'not valid value for total_crates, numeric only'})
        else:
            err400.update({'description': 'not valid value for total_crates'})
            create_so = False
        # total_male
        if 'total_male' in data:
            if type(data['total_male']) == int or type(data['total_male']) == float:
                to_create.update({'total_male': data['total_male']})
                create_so = True
            else:
                create_so = False
                err400.update({'description': 'not valid value for total_male, numeric only'})
        else:
            err400.update({'description': 'not valid value for total_male'})
            create_so = False
        # total_female
        if 'total_female' in data:
            if type(data['total_female']) == int or type(data['total_female']) == float:
                to_create.update({'total_female': data['total_female']})
                create_so = True
            else:
                create_so = False
                err400.update({'description': 'not valid value for total_female, numeric only'})
        else:
            err400.update({'description': 'not valid value for total_female'})
            create_so = False
        # total_apollo
        if 'total_apollo' in data:
            if type(data['total_apollo']) == int or type(data['total_apollo']) == float:
                to_create.update({'total_apollo': data['total_apollo']})
                create_so = True
            else:
                create_so = False
                err400.update({'description': 'not valid value for total_female, numeric only'})
        else:
            err400.update({'description': 'not valid value for total_apollo'})
            create_so = False
        # total_apollo
        if 'total_gross_weight' in data:
            if type(data['total_gross_weight']) == int or type(data['total_gross_weight']) == float:
                to_create.update({'total_gw': data['total_gross_weight']})
                create_so = True
            else:
                create_so = False
                err400.update({'description': 'not valid value for total_gross_weight, numeric only'})
        else:
            err400.update({'description': 'not valid value for total_gross_weight'})
            create_so = False
        # avg_crates_weight
        if 'avg_crates_weight' in data:
            if type(data['avg_crates_weight']) == int or type(data['avg_crates_weight']) == float:
                to_create.update({'avg_cr_w': data['avg_crates_weight']})
                create_so = True
            else:
                create_so = False
                err400.update({'description': 'not valid value for avg_crates_weight, numeric only'})
        else:
            err400.update({'description': 'not valid value for avg_crates_weight'})
            create_so = False
        # avg_crates_weight
        if 'total_creates_weight' in data:
            if type(data['total_creates_weight']) == int or type(data['total_creates_weight']) == float:
                to_create.update({'total_cw': data['total_creates_weight']})
                create_so = True
            else:
                create_so = False
                err400.update({'description': 'not valid value for avg_crates_weight, numeric only'})
        else:
            err400.update({'description': 'not valid value for total_creates_weight'})
            create_so = False
        # avg_crates_weight
        if 'avg_bird_weight' in data:
            if type(data['avg_bird_weight']) == int or type(data['avg_bird_weight']) == float:
                to_create.update({'avg_b_w': data['avg_bird_weight']})
                create_so = True
            else:
                create_so = False
                err400.update({'description': 'not valid value for avg_bird_weight, numeric only'})
        else:
            err400.update({'description': 'not valid value for avg_bird_weight'})
            create_so = False
        # avg_crates_weight
        if 'total_do_net_weight' in data:
            if type(data['total_do_net_weight']) == int or type(data['total_do_net_weight']) == float:
                to_create.update({'total_nw': data['total_do_net_weight']})
                create_so = True
            else:
                create_so = False
                err400.update({'description': 'not valid value for total_do_net_weight, numeric only'})
        else:
            err400.update({'description': 'not valid value for total_do_net_weight'})
            create_so = False
        # checking currency_id
        rescom = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.company', 'search_read', [], ['currency_id'])
        if rescom:
            rescom = rescom[0]
            currency_id = rescom['currency_id'][0]
            to_create.update({'currency_id': currency_id})
        else:
            currency_id = 3
            to_create.update({'currency_id': currency_id})
        ############# NEW ###############
        # pda_do_id
        if 'pda_do_id' in data:
            to_create.update({'pda_do_id': data['pda_do_id']})
            create_so = True
        else:
            err400.update({'description': 'not valid value for pda_do_id'})
            create_so = False
        # start_loading_time
        if 'start_loading_time' in data:
            try:
                start_loading_time = time.strftime('%Y-%m-%d %H:%M:%S',time.strptime(data['start_loading_time'],'%Y-%m-%d %H:%M:%S'))
            except:
                start_loading_time = time.strftime('%Y-%m-%d %H:%M:%S',time.strptime(data['start_loading_time'],'%Y-%m-%d %H:%M:%S.%f'))
            print "start_loading_time = ", start_loading_time
            to_create.update({'start_loading_time': start_loading_time})
            create_so = True
        else:
            err400.update({'description': 'not valid value for start_loading_time'})
            create_so = False
        # end_loading_time
        if 'end_loading_time' in data:
            try:
                end_loading_time = time.strftime('%Y-%m-%d %H:%M:%S',time.strptime(data['end_loading_time'],'%Y-%m-%d %H:%M:%S'))
            except:
                end_loading_time = time.strftime('%Y-%m-%d %H:%M:%S',time.strptime(data['end_loading_time'],'%Y-%m-%d %H:%M:%S.%f'))
            print "end load time = ", end_loading_time
            to_create.update({'end_loading_time': end_loading_time})
            create_so = True
        else:
            err400.update({'description': 'not valid value for end_loading_time'})
            create_so = False
        # other_comment
        if 'other_comment' in data:
            to_create.update({'other_comment': data['other_comment']})
            create_so = True
        else:
            err400.update({'description': 'not valid value for other_comment'})
            create_so = False
        # farmer_sign
        if 'farmer_sign' in data:
            to_create.update({'farmer_signature': data['farmer_sign']})
            create_so = True
        else:
            err400.update({'description': 'not valid value for farmer_sign'})
            create_so = False
        # owner_sign
        if 'owner_sign' in data:
            to_create.update({'customer_signature': data['owner_sign']})
            create_so = True
        else:
            err400.update({'description': 'not valid value for owner_sign'})
            create_so = False
        # total_cover
        if 'totalcover' in data:
            to_create.update({'totalcover': data['totalcover']})
            create_so = True
        else:
            err400.update({'description': 'not valid value for total_cover'})
            create_so = False
        # single_cover_weight
        if 'single_cover_weight' in data:
            to_create.update({'single_cover_weight': data['single_cover_weight']})
            create_so = True
        else:
            err400.update({'description': 'not valid value for single_cover_weight'})
            create_so = False

        # added 20171227
        # product
        if 'product' in data:
            to_create.update({'product': data['product']})
        # breed
        if 'breed' in data and data['breed'] is not None:
            to_create.update({'breed': data['breed']})
        # age
        if 'age' in data and data['age'] is not None:
            to_create.update({'age': data['age']})
        # farm house number
        if 'farm_house_number' in data and data['farm_house_number'] is not None:
            to_create.update({'farm_house_number': data['farm_house_number']})
        # total birds
        if 'total_nb_birds' in data:
            to_create.update({'total_nb_birds': data['total_nb_birds']})
        # batch id
        if 'batch_id' in data and data['batch_id'] is not None:
            to_create.update({'batch_id': data['batch_id']})
        # catching bill
        if 'catching_bill' in data  and data['catching_bill'] is not None:
            to_create.update({'catching_bill': data['catching_bill']})

        if 'bird_distribution_per_crate' in data:
            if len(data['bird_distribution_per_crate']) > 0:
                for key, value in data['bird_distribution_per_crate'].items():
                    if 'mix' == key:
                        mix = '{total_birds} ({avg_birds_per_crate}/{nb_crates})'.format(**value)
                        to_create.update({'birdcrate_mix': mix,
                                          'birdcrate_mix_crates': value['nb_crates'],
                                          'birdcrate_mix_total': value['total_birds'],
                                          'birdcrate_mix_avg': value['avg_birds_per_crate']
                                        })
                    if 'C' == key:
                        c = '{total_birds} ({avg_birds_per_crate}/{nb_crates})'.format(**value)
                        to_create.update({'birdcrate_c': c,
                                          'birdcrate_c_crates': value['nb_crates'],
                                          'birdcrate_c_total': value['total_birds'],
                                          'birdcrate_c_avg': value['avg_birds_per_crate']
                                        })
                    if 'B' == key:
                        b = '{total_birds} ({avg_birds_per_crate}/{nb_crates})'.format(**value)
                        to_create.update({'birdcrate_b': b,
                                          'birdcrate_b_crates': value['nb_crates'],
                                          'birdcrate_b_total': value['total_birds'],
                                          'birdcrate_b_avg': value['avg_birds_per_crate']
                                        })
                    if 'male' == key:
                        male = '{total_birds} ({avg_birds_per_crate}/{nb_crates})'.format(**value)
                        to_create.update({'birdcrate_male': male,
                                          'birdcrate_male_crates': value['nb_crates'],
                                          'birdcrate_male_total': value['total_birds'],
                                          'birdcrate_male_avg': value['avg_birds_per_crate']
                                        })
                    if 'female' == key:
                        female = '{total_birds} ({avg_birds_per_crate}/{nb_crates})'.format(**value)
                        to_create.update({'birdcrate_female': female,
                                          'birdcrate_female_crates': value['nb_crates'],
                                          'birdcrate_female_total': value['total_birds'],
                                          'birdcrate_female_avg': value['avg_birds_per_crate']
                                        })

        # update result of the function
        res.update({'create_so': create_so})
        res.update({'to_create': to_create})
        #######start checking purchase order line#######
        all_line = []

        if 'crate_loading' in data:
            if len(data['crate_loading']) > 0:
                for line in data['crate_loading']:
                    po_line = {}
                    # checking number_of_crates
                    if 'number_of_crates' in line:
                        if type(line['number_of_crates']) == int or type(line['number_of_crates']) == float:
                            po_line.update({'crates': line['number_of_crates']})
                        else:
                            err400.update({'description': 'not valid value for number_of_crates, numeric only'})
                    else:
                        err400.update({'description': 'not valid value for number_of_crates'})
                    # checking crate_weight
                    if 'crate_weight' in line:
                        if type(line['crate_weight']) == int or type(line['crate_weight']) == float:
                            po_line.update({'crates_weight': line['crate_weight']})
                        else:
                            err400.update({'description': 'not valid value for crate_weight, numeric only'})
                    else:
                        err400.update({'description': 'not valid value for crate_weight'})
                    # checking buyer
                    if 'buyer' in line:
                        po_line.update({'buyer': line['buyer']})
                    else:
                        err400.update({'description': 'not valid value for buyer'})
                    # weighing date
                    if 'weighing_date' in line:
                        date_order_local = parse(line['weighing_date'])
                        if not date_order_local.tzinfo:
                            date_order_local = get_localzone().localize(date_order_local)
                        date_order = date_order_local.astimezone(pytz.utc)
                        po_line.update({'weighing_date': date_order.strftime("%Y-%m-%d %H:%M:%S")})
                    # crate_net
                    if 'crate_net' in line:
                        if type(line['crate_net']) == int or type(line['crate_net']) == float:
                            po_line.update({'crate_net': line['crate_net'], 'product_qty': line['crate_net']})
                        else:
                            err400.update({'description': 'not valid value for crate_net, numeric only'})
                    # buyer_id  (Optional)
                    if 'buyer_id' in line and line['buyer_id'] is not None and line['buyer_id']:
                        if "temp" in line['buyer_id']:
                            po_line.update({'buyer_id': line['buyer_id']})
                        else:
                            farm = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.partner', 'search',
                                    [('id', '=', line['buyer_id'])])
                            if farm:
                                po_line.update({'buyer_id': line['buyer_id']})
                            else:
                                notfound = 'buyer_id:' + str(line['buyer_id']) + ' is not exist in ERP'
                                err400.update({'description': notfound})
                    else:
                        print "Ignore the buyer ID because its null"
                    # Logging tests
                    print "***PO LINE DATA***: %s" % str(po_line)
                    all_line.append(po_line)
            else:
                err400.update({'description': 'not valid value for crate loading, there is no crate loading'})
        res.update({'all_line': all_line})


        #######start checking new buyers#######
         ## Function
        new_buyers_all_line = []
        if 'new_buyers' in data and data['new_buyers'] is not None  and data['new_buyers']:
            if len(data['new_buyers']) > 0:
                for line in data['new_buyers']:
                    new_buyers_line = {}
                    ignore_same_buyer = False
                    if 'name' in line:
                        new_buyers_line.update({'name': line['name']})
                        if not line['name']:
                            err400.update({'description': 'not valid as new buyer name is empty'})
                        else:
                            # check new buyer
                            buyer_exist = sock.execute(dbname[token], odoo_user,
                                         db_user_pwd[token], 'res.partner', 'search',
                                         [('name', '=ilike', line['name'])]
                                         )

                            if not buyer_exist:
                                new_buyers_line.update({'name': line['name']})
                            else:
                                ignore_same_buyer = True
                    else:
                        err400.update({'description': 'not valid new buyers name'})

                    if not ignore_same_buyer:
                        if 'city' in line:
                            new_buyers_line.update({'city': line['city']})
                        else:
                            err400.update({'description': 'not valid new buyers city'})
                        if 'zip' in line:
                            new_buyers_line.update({'zip': line['zip']})
                        else:
                            err400.update({'description': 'not valid new buyers zip'})
                        if 'country_name' in line:
                            new_buyers_line.update({'country_name': line['country_name']})
                        else:
                            err400.update({'description': 'not valid new buyers country_name'})
                        if 'street' in line:
                            new_buyers_line.update({'street': line['street']})
                        else:
                            err400.update({'description': 'not valid new buyers street'})
                        if 'state_name' in line:
                            new_buyers_line.update({'state_name': line['state_name']})
                        else:
                            err400.update({'description': 'not valid new buyers state_name'})
                        if 'id' in line:
                            new_buyers_line.update({'id': line['id']})
                        else:
                            err400.update({'description': 'not valid new buyers id'})
                        # Logging tests
                        print "***NEW BUYERS DATA***: %s" % str(new_buyers_line)
                        new_buyers_all_line.append(new_buyers_line)
        res.update({'new_buyers_all_line': new_buyers_all_line})

        return res


class master:
    def check_autorization(self, token):
        sock = xmlrpclib.ServerProxy('%s/xmlrpc/object' % (odoo_url))
        print '__________________SOCK ________________', sock
        print 'master:check_autorization: Checking Token=', token
        if token in dbname:
            checktoken = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.users', 'search',
                                      [('token', '=', token)])
            if len(checktoken) >= 1:
                return True
            else:
                return "Error 401 : Unauthorized"
        else:
            return "Error 401 : Unauthorized"

    def pda_history(self, token, data):
        sock = xmlrpclib.ServerProxy('%s/xmlrpc/object' % (odoo_url))
        # company
        to_history = {}
        if 'owner_id' in data:
            company = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.company', 'search',
                                   [('name', '=', data['owner_id'])])
            if company:
                com = company[0]
                to_history.update({'owner_id': com})
            else:
                to_history.update({'owner_id': 1})
        else:
            to_history.update({'owner_id': 1})
        # pda_id
        if 'pda_id' in data:
            pda = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'pda.operation', 'search',
                               [('pda_id', '=', data['pda_id'])])
            if pda:
                pda_id = pda[0]
                to_history.update({'name': pda_id})
            #             else:
            #                 id = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'pda.operation', 'create',{'name' : data['pda_id']})
            #                 to_history.update({'name':id})
        # last_position_long
        if 'last_position_long' in data:
            to_history.update({'last_position_long': data['last_position_long']})
        # last_position_lat
        if 'last_position_latt' in data:
            to_history.update({'last_position_latt': data['last_position_latt']})
        # last_sync_with_erp
        if 'last_sync_with_erp' in data:
            date_time = datetime.datetime.strptime(str(data['last_sync_with_erp']), "%Y-%m-%d %H:%M:%S.%f")
            to_history.update({'last_sync_with_erp': data['last_sync_with_erp']})
        to_history.update(
            {'access_date': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
             'info': 'getmasterupdate',
             'data': json.dumps(data)})
        sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'pda.history', 'create', to_history)

    def check_pda(self, token, data):
        sock = xmlrpclib.ServerProxy('%s/xmlrpc/object' % (odoo_url))
        res = None
        # pda_id
        if 'pda_id' in data:
            pda = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'pda.operation', 'search',
                               [('pda_id', '=', data['pda_id'])])
            if pda:
                res = True
            else:
                res = False
        else:
            res = False
        return res

    def clean_false(self, dict):
        if type(dict) is list:
            for dictio in dict:
                self.do_clean_false(dictio)
            return dict
        else:
            return self.do_clean_false(dict)

    def do_clean_false(self, dc):
        for k in dc.iterkeys():
            if dc[k] is False:
                dc[k] = ''
            if type(dc[k]) is list:
                for k2 in dc[k]:
                    #                     print k2
                    for k3 in k2.iterkeys():
                        if k2[k3] is False:
                            k2[k3] = ''
                        print k3
                        if k3 in ['installation', 'last_sampling', 'last_sync']:
                            if k2[k3]:
                                k2[k3] = datetime.datetime.strptime(str(k2[k3]), '%Y-%m-%d %H:%M:%S').strftime(
                                    '%Y-%m-%d-%H:%M:%S')
            if type(dc[k]) is dict:
                for k2 in dc[k].iterkeys():
                    #                     print k2
                    if dc[k][k2] is False:
                        dc[k][k2] = ''
            if k in ['last_delivery', 'installation']:
                if dc[k]:
                    dc[k] = datetime.datetime.strptime(str(dc[k]), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d-%H:%M:%S')
        return dc

    def POST(self):
        res = None
        token = web.ctx.env.get('HTTP_AUTHORIZATION')
        sock = xmlrpclib.ServerProxy('%s/xmlrpc/object' % (odoo_url))
        author = self.check_autorization(token)
        data_post = web.data()
        print "HEADER : ", token
        print "PARAMETER : ", data_post
        data_post = ast.literal_eval(data_post)
        result = {}
        found_numbur_plate = False
        data = {}
        if author == True:
            check_pda = self.check_pda(token, data_post)
            if check_pda is True:
                data = {"code": "200"}
                # pda
                pda_id = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'pda.operation', 'search_read',
                                      [('pda_id', '=', data_post['pda_id'])],
                                      ['name', 'lorry_id', 'pda_id', 'installation', 'lastest_sync', 'app_version', 'full_sync'])
                full_sync = 0
                if pda_id:
                    id_pda = pda_id[0]['id']
                    name_pda = pda_id[0]['pda_id']
                    model_pda = pda_id[0]['name']
                    del pda_id[0]['pda_id']
                    del pda_id[0]['name']
                    pda_id[0].update({'name': name_pda})
                    pda_id[0].update({'model': model_pda})
                    pda_id[0].update({'min_version': config_pda['min_version']})
                    if pda_id[0]['lorry_id']:
                        pda_id[0]['lorry_id'] = pda_id[0]['lorry_id'][1]
                    if pda_id[0]['full_sync']:
                        full_sync = 1
                        sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'pda.operation', 'write',id_pda, {'full_sync': 0})
                    del pda_id[0]['full_sync']
                    result.update({"pda": self.clean_false(pda_id[0])})

                # lorry
                lorry = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'lorry.number', 'search_read',
                                     [], ['name','owner_id'])
                if lorry:
                    print "LORRY LIST"
                    pprint(lorry)
                    for lor in lorry:
                        if lor['owner_id']:
                            lor['owner_id'] = lor['owner_id'][1]  # just take the name, not the ID
                        else:
                            lor['owner_id']=""


                    print "LORRY LIST 2"
                    pprint(lorry)
                    result.update({'lorry': self.clean_false(lorry)})
                    found_numbur_plate = True
                else:
                    found_numbur_plate = False


                # farm
                farm_ids = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.partner', 'search_read',
                                        [('is_an_farm','=', True), '|', ('customer', '=', True), ('supplier', '=', True)],
                                        ['name', 'street', 'city', 'state_id', 'zip', 'country_id', 'scales', 'manager',
                                         'information_of_gst', 'last_delivery', 'branch', 'owner_id',
                                         'profile_min_crate', 'profile_max_crate'])
                for elm in farm_ids:
                    toupdatefarm = []
                    todeletefarm = []
                    scales_ids = []
                    # check m2o
                    for n, val in elm.iteritems():
                        typedata = isinstance(val, list)
                        if typedata is True:
                            if n == 'owner_id':
                                print "Ignore"
                            elif n == 'scales':
                                scales_ids = val
                                scale_obj = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'measure.scale', 'read',
                                                         scales_ids,
                                                         ['name', 'installation', 'last_sampling', 'last_sync', 'nickname', 'brand',
                                                          'scale_model', 'display_model', 'display_fw_version',
                                                          'Comm_id'])
                                del elm['scales']
                                elm.update({'scales': scale_obj})
                            else:
                                # Clean and auto resolve to remove the ID
                                toupdatefarm.append({n: val[1]})
                                todeletefarm.append(n)
                    # delete m2o
                    for pop in todeletefarm:
                        del elm[pop]
                    # update m2o
                    for push in toupdatefarm:
                        elm.update(push)


                    # checking owner of the farm
                    if elm['owner_id']:
                       print "CURRENT FARM OWNERID ELM"
                       pprint(elm["owner_id"])

                       farm_owner_id = elm['owner_id'][0]
                       if farm_owner_id:
                           print "FARM OWNER ID"
                           pprint(farm_owner_id)
                           print "-----"
                           farm_owner_details = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.partner', 'search_read',
                                                    [('id', '=', farm_owner_id)],
                                                    ['name', 'street', 'city', 'state_id', 'zip', 'country_id'])
                           if farm_owner_details:
                               # Replace by the name, and remove the ID [ '123', 'FRANCE'] become  "FRANCE"
                               if farm_owner_details[0]['country_id']:
                                       farm_owner_details[0]['country_id']=farm_owner_details[0]['country_id'][1]
                               # Replace by the name, and remove the ID [ '123', 'STATE'] become  "STATE"
                               if farm_owner_details[0]['state_id']:
                                       farm_owner_details[0]['state_id']=farm_owner_details[0]['state_id'][1]
                               elm.update({"owner": farm_owner_details[0] })
                       del elm['owner_id']

                result.update({"farm": self.clean_false(farm_ids)})

                # List of products
                product_ids = sock.execute(
                    dbname[token], odoo_user, db_user_pwd[token], 'product.template', 'search_read',
                    [('active', '=', True), ('uom_id.category_id.name', '=', 'Weight')], ['name'])
                result.update({"products": self.clean_false(product_ids)})

                # List of customers


                # buyers
                buyer_ids = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.partner', 'search_read', [('customer', '=', True)], ['name', 'street', 'city', 'state_id', 'zip', 'country_id'])
                for elm in buyer_ids:
                    toupdatebuyer = []
                    todeletebuyer = []
                    # check m2o
                    for n, val in elm.iteritems():
                        typedata = isinstance(val, list)
                        if typedata is True:
                            toupdatebuyer.append({n: val[1]})
                            todeletebuyer.append(n)
                    # delete m2o
                    for pop in todeletebuyer:
                        del elm[pop]
                    # update m2o
                    for push in toupdatebuyer:
                        elm.update(push)
                result.update({"buyers": self.clean_false(buyer_ids)})

                # company
                # company_ids = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.company', 'search_read',[],['name','street','city','state_id','zip','country_id','tax_id','crate_cover_weight'])
                company_ids = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'res.partner', 'search_read', [('supplier', '=', False), ('customer', '=', False), ('is_an_owner', '=', True)], ['name', 'street', 'city', 'state_id', 'zip', 'country_id', 'crate_cover_weight', 'header_do_report', 'mobile_header_do_report', 'xaml_template'])

                for elm in company_ids:
                    if full_sync:
                        if 'header_do_report' in elm:
                            if elm['header_do_report']:
                                data_post.update({'header_do_report': elm['header_do_report']})
                            else:
                                del elm['header_do_report']
                        if 'mobile_header_do_report' in elm:
                            if elm['mobile_header_do_report']:
                                data_post.update({'mobile_header_do_report': elm['mobile_header_do_report']})
                            else:
                                del elm['mobile_header_do_report']
                        if 'xaml_template' in elm:
                            if elm['xaml_template']:
                                data_post.update({'xaml_template': elm['xaml_template']})
                            else:
                                del elm['xaml_template']

                        logo_img = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'ir.attachment', 'search_read', [('res_model', '=', 'res.partner'), ('res_field', '=', 'image'), ('res_id', '=', elm['id'])], ['db_datas'])
                        print 'logo_img === ', logo_img

                        if 'db_datas' in logo_img[0] and logo_img[0]['db_datas']:
                            data_post.update({'logo_img': logo_img[0]['db_datas']})

                    else:
                        del elm['header_do_report']
                        del elm['mobile_header_do_report']
                        del elm['xaml_template']

                    toupdate = []
                    todelete = []
                    # check m2o
                    for n, val in elm.iteritems():
                        typedata = isinstance(val, list)
                        if typedata is True:
                            toupdate.append({n: val[1]})
                            todelete.append(n)
                    # delete m2o
                    for pop in todelete:
                        del elm[pop]
                    # update m2o
                    for push in toupdate:
                        elm.update(push)
                result.update({"company": self.clean_false(company_ids)})

                data.update({"result": result})
                data_string = json.dumps(data)
                if found_numbur_plate is True:
                    res = data_string
                else:
                    err403.update({'description': 'No Lorry has been found'})
                    res = err403
            else:
                err403.update({'description': 'PDA ID does not exist'})
                res = err403
        else:
            res = err401
        self.pda_history(token, data_post)
        if data:
            if data["code"] == "200":
                pda = data["result"]["pda"]["name"]
                pda = sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'pda.operation', 'search',
                                   [('pda_id', '=', pda)])
                sock.execute(dbname[token], odoo_user, db_user_pwd[token], 'pda.operation', 'write', pda,
                            {'lastest_sync': data_post['last_sync_with_erp'],
                             'app_version': data_post['pda_version'],
                            })
        print "RESPONSE : ", res
        return res


if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()

app = web.application(urls, globals(), autoreload=False)
application = app.wsgifunc()

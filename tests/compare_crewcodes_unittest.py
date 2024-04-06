import os
import unittest
import planon

from tests import compare_crewcodes

# *********************************************************************
# SETUP
# *********************************************************************

planon.PlanonResource.set_site(site=os.environ["PLANON_API_URL"])
planon.PlanonResource.set_header(jwt=os.environ["PLANON_API_KEY"])

# Planon API
PLANON_API_URL = os.environ["PLANON_API_URL"]
PLANON_API_KEY = os.environ["PLANON_API_KEY"]

# Dartmouth iPaaS
DARTMOUTH_API_URL = os.environ["DARTMOUTH_API_URL"]
DARTMOUTH_API_KEY = os.environ["DARTMOUTH_API_KEY"]

headers = {"Authorization": DARTMOUTH_API_KEY}
scopes = "urn:dartmouth:employees:read.sensitive"


# ****************************************************************************************************************

pln_trades = planon.Trade.find()
pln_trades_by_syscodes = {trade.Syscode: trade for trade in pln_trades}
pln_trades_by_codes = {trade.Code: trade for trade in pln_trades}

pln_laborgroups = planon.WorkingHoursTariffGroup.find()
pln_laborgroups_by_syscodes = {laborgroup.Syscode: laborgroup for laborgroup in pln_laborgroups if laborgroup.Code}
pln_laborgroups_by_codes = {laborgroup.Code: laborgroup for laborgroup in pln_laborgroups if laborgroup.Code}


# ****************************************************************************************************************
class TestCompareCodes(unittest.TestCase):
    
    def test_match_crewcodes(self):
        """       
        Test matching crew codes.
        Asserts that compare_crewcodes_test function correctly matches crew codes.
        """
     
        active_crew_code = 'HLS'      

        pln_person = {
        'd20171b': {            
            'Code': 'PER0087392',
            'LastName':'Moriarty',
            'TradeRef': 263,
            'WorkingHoursTariffGroupRef': 93
            }
        }

        excluded_crew_codes = ['ML', 'CEOPS']
        
        ipaas_trade, ipaas_labor_group, pln_trade_code, pln_laborgroup_code = compare_crewcodes.compare_crewcodes_test(active_crew_code,pln_person,pln_trades_by_syscodes,pln_laborgroups_by_syscodes, excluded_crew_codes)

        self.assertEqual(ipaas_trade, 'HLS')
        self.assertEqual(ipaas_labor_group, 'HLS')
        self.assertEqual(pln_trade_code, 'HLS')
        self.assertEqual(pln_laborgroup_code, 'HLS')


    def test_non_match_codes(self):
        """       
        Test non-matching crew codes.
        Asserts that compare_crewcodes_test function does not match with crew codes.
        """
        active_crew_code ='BAS'
        
        pln_person = {
        'd20171b': {            
            'Code': 'PER0087392',
            'LastName':'Moriarty',
            'TradeRef': 115,
            'WorkingHoursTariffGroupRef': 73
            }
        }

        excluded_crew_codes = ['ML', 'CEOPS']
            
        ipaas_trade, ipaas_labor_group, pln_trade_code, pln_laborgroup_code = compare_crewcodes.compare_crewcodes_test(active_crew_code, pln_person, pln_trades_by_syscodes, pln_laborgroups_by_syscodes, excluded_crew_codes)

        self.assertNotEqual(ipaas_trade, 'HLS')
        self.assertNotEqual(ipaas_labor_group, 'HLS')
        self.assertNotEqual(pln_trade_code, 'HLS')
        self.assertNotEqual(pln_laborgroup_code, 'HLS')


    def test_no_trade(self):
        """       
        Test when pln_person does not have a trade with TradeRef=None .
   
        """
         
        active_crew_code ='HLS'
        
        pln_person = {
        'd20171b': {            
            'Code': 'PER0087392',
            'LastName':'Moriarty',
            'TradeRef':None,
            'WorkingHoursTariffGroupRef': 93
            }
        }

        excluded_crew_codes = ['ML', 'CEOPS']

        ipaas_trade, ipaas_labor_group, pln_trade_code, pln_laborgroup_code = compare_crewcodes.compare_crewcodes_test(active_crew_code, pln_person, pln_trades_by_syscodes, pln_laborgroups_by_syscodes, excluded_crew_codes)

        self.assertEqual(ipaas_trade, 'HLS')
        self.assertEqual(ipaas_labor_group, 'HLS')
        self.assertNotEqual(pln_trade_code, 'HLS')
        self.assertEqual(pln_laborgroup_code, 'HLS')


        
    def test_no_lg(self):
        """       
        Test when pln_person does not have a trade with 'WorkingHoursTariffGroupRef': None
   
        """
         
        active_crew_code ='HLS'
        
        pln_person = {
        'd20171b': {            
            'Code': 'PER0087392',
            'LastName':'Moriarty',
            'TradeRef':263,
            'WorkingHoursTariffGroupRef': None
            }
        }

        excluded_crew_codes = ['ML', 'CEOPS']
            
        ipaas_trade, ipaas_labor_group, pln_trade_code, pln_laborgroup_code =compare_crewcodes.compare_crewcodes_test(active_crew_code, pln_person, pln_trades_by_syscodes, pln_laborgroups_by_syscodes, excluded_crew_codes)

        self.assertEqual(ipaas_trade, 'HLS')
        self.assertEqual(ipaas_labor_group, 'HLS')
        self.assertEqual(pln_trade_code, 'HLS')
        self.assertNotEqual(pln_laborgroup_code, 'HLS')


        
    def test_excluded(self):
        """
        Test behavior when crew code is excluded.

        Checks if the function behaves correctly when the active crew code is in the list of excluded crew codes.
        """        
        active_crew_code ='ML'
        
        pln_person = {
        'd20171b': {            
            'Code': 'PER0087392',
            'LastName':'Moriarty',
            'TradeRef':None,
            'WorkingHoursTariffGroupRef': 60
            }
        }

        excluded_crew_codes = ['ML', 'CEOPS']
            
        ipaas_trade, ipaas_labor_group, pln_trade_code, pln_laborgroup_code = compare_crewcodes.compare_crewcodes_test(active_crew_code, pln_person, pln_trades_by_syscodes, pln_laborgroups_by_syscodes, excluded_crew_codes)

        self.assertNotEqual(ipaas_trade, None)
        self.assertNotEqual(ipaas_labor_group, None)
        self.assertNotEqual(pln_trade_code, None)
        self.assertNotEqual(pln_laborgroup_code, None)



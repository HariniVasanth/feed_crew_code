import unittest
from ipaas import utils

# *********************************************************************
# LOGGING
# *********************************************************************

class TestGetActiveCrewCodes(unittest.TestCase)  :
    '''
    # Test case for no jobs (ex-employee Warren Belding)
    '''
    def test_empty_jobs(self):
        employee = {
            "netid": "d13523b",
            "jobs": []  # Empty jobs list
        }
        active_crew_code = utils.get_active_facilities_crew_code(employee)
        expected_crew_code = ''
        self.assertEqual(active_crew_code, expected_crew_code)

    def test_no_active_crew_codes(self):
        """
        # Test case for no crew code but with active job (f003841)
        """
        employee = {
            "netid": "f003841",
            "jobs": [
                {
                    "maintenance_crew": {
                        "crew_code": None #job with no crew code
                    },
                    "job_current_status": "Active"  
                }
            ]
        }
        
        active_crew_code = utils.get_active_facilities_crew_code(employee)
        expected_crew_code = ''
        self.assertEqual(active_crew_code, expected_crew_code)

    # Test case for single active crew code (F00207H - Billy Lyons - ACS)
    def test_single_active_crew_code(self):
        employee = {
            "netid": "f00207h",
            "jobs": [
                {
                    "maintenance_crew": {
                        "crew_code": "ACS" # job with 1 crew code
                    },
                    "job_current_status": "Active"
                }
            ]
        }
        active_crew_code = utils.get_active_facilities_crew_code(employee)
        expected_crew_code = 'ACS'
        self.assertEqual(active_crew_code, expected_crew_code)

    def test_nonunique_active_crew_codes(self):
        employee = {
            "netid": "d28941t",
            "jobs": [
                {
                    "maintenance_crew": { 
                        "crew_code": "TS"   # job with 2 crew codes
                    },
                    "job_current_status": "Active"
                },
                {
                    "maintenance_crew": {
                        "crew_code": "TS"
                    },
                    "job_current_status": "Active"
                },
                {
                    "maintenance_crew": {
                        "crew_code": "TS"
                    },
                    "job_current_status": "Active"
                }
               
               
            ]
        }        
        
        active_crew_code = utils.get_active_facilities_crew_code(employee)
        expected_crew_code = 'TS'
        self.assertEqual(active_crew_code, expected_crew_code)

    # Test case for employee with 2_unique_active_crew_codes
    def test_2_unique_active_crew_codes(self):
        employee = {
            "netid": "f000000",
            "jobs": [
                {
                    "maintenance_crew": { 
                        "crew_code": "BAS"   # job with 2 crew codes
                    },
                    "job_current_status": "Active"
                },
                {
                    "maintenance_crew": {
                        "crew_code": "BR"
                    },
                    "job_current_status": "Active"
                }
            ]
        }
             
        self.assertRaises(ValueError,utils.get_active_facilities_crew_code,employee)
    
    
    # Test case for employee with 3_unique_active_crew_codes
    def test_3_unique_active_crew_codes(self):
        employee = {
            "netid": "f000000",
            "jobs": [
                {
                    "maintenance_crew": { 
                        "crew_code": "BAS"   # job with 2 crew codes
                    },
                    "job_current_status": "Active"
                },
                {
                    "maintenance_crew": {
                        "crew_code": "BR"
                    },
                    "job_current_status": "Active"
                },
                 {
                    "maintenance_crew": {
                        "crew_code": "ACS"
                    },
                    "job_current_status": "Active"
                }
            ]
        }
             
        self.assertRaises(ValueError,utils.get_active_facilities_crew_code,employee)

    # Test case for employee with multiple nonunique crew codes
    def test_unique_crew_codes(self):
        employee = {
            "netid": "f000000",
            "jobs": [
                {
                    "maintenance_crew": { 
                        "crew_code": "BAS"   # job with 2 crew codes
                    },
                    "job_current_status": "Active"
                },
                {
                    "maintenance_crew": {
                        "crew_code": "BR"
                    },
                    "job_current_status": "Inactive"
                }
            ]
        }
        active_crew_code = utils.get_active_facilities_crew_code(employee)
        expected_crew_code = 'BAS'
        self.assertEqual(active_crew_code, expected_crew_code)

    # Test case for employee with 2 active crew codes
    def test_second_crew_code(self):
        employee = {
            "netid": "f000000",
            "jobs": [
                {
                    "maintenance_crew": { 
                        "crew_code": None   # job with 2 crew codes
                    },
                    "job_current_status": "Active"
                },
                {
                    "maintenance_crew": {
                        "crew_code": "BR"
                    },
                    "job_current_status": "Active"
                }
            ]
        }

        active_crew_code = utils.get_active_facilities_crew_code(employee)
        expected_crew_code = 'BR'
        self.assertEqual(active_crew_code, expected_crew_code)

    # Test case for employee with 3 active crew codes
    def test_third_crew_code(self):
        employee = {
            "netid": "f000000",
            "jobs": [
                {
                    "maintenance_crew": { 
                        "crew_code": None   # job with 2 crew codes
                    },
                    "job_current_status": "Active"
                },
                {
                    "maintenance_crew": {
                        "crew_code": "BR"
                    },
                    "job_current_status": "Inactive"
                },                
                 {
                    "maintenance_crew": {
                        "crew_code": "BR"
                    },
                    "job_current_status": "Active"
                }
            ]
        }

        active_crew_code = utils.get_active_facilities_crew_code(employee)
        expected_crew_code = 'BR'
        self.assertEqual(active_crew_code, expected_crew_code)


    # Test case for employee with multiple_inactive_crew_codes
    def test_multiple_inactive_crew_codes(self):
        employee = {
            "netid": "f000000",
            "jobs": [
                {
                    "maintenance_crew": { 
                        "crew_code": None   # job with 2 crew codes
                    },
                    "job_current_status": "Active"
                },
                {
                    "maintenance_crew": {
                        "crew_code": "BR"
                    },
                    "job_current_status": "Inactive"
                },                
                 {
                    "maintenance_crew": {
                        "crew_code": "BR"
                    },
                    "job_current_status": "Active"
                }
            ]
        }

        active_crew_code = utils.get_active_facilities_crew_code(employee)
        expected_crew_code = 'BR'
        self.assertEqual(active_crew_code, expected_crew_code)

if __name__ == '__main__':
    unittest.main()



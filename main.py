import os
import sys
import time
import logging
import json

import requests

import planon
from planon import Person

from ipaas import utils

# *********************************************************************
# LOGGING
# *********************************************************************

log_level = os.environ.get("LOG_LEVEL", "INFO")
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(stream=sys.stdout, level=log_level, format=log_format)

# Set the log to use GMT time zone
logging.Formatter.converter = time.gmtime

# Add milliseconds
logging.Formatter.default_msec_format = "%s.%03d"

log = logging.getLogger(__name__)

# *********************************************************************
# SETUP
# *********************************************************************

def setup():

    planon.PlanonResource.set_site(site=os.environ["PLANON_API_URL"])
    planon.PlanonResource.set_header(jwt=os.environ["PLANON_API_KEY"])

    # Planon API
    PLANON_API_URL = os.environ["PLANON_API_URL"]
    PLANON_API_KEY = os.environ["PLANON_API_KEY"]
    log.debug(f"{PLANON_API_URL}")

    # Dartmouth iPaaS
    DARTMOUTH_API_URL = os.environ["DARTMOUTH_API_URL"]
    DARTMOUTH_API_KEY = os.environ["DARTMOUTH_API_KEY"]
    log.debug(f"{DARTMOUTH_API_URL}")

    headers = {"Authorization": DARTMOUTH_API_KEY}
    scopes = "urn:dartmouth:employees:read.sensitive"   
    
    return PLANON_API_URL, PLANON_API_KEY, DARTMOUTH_API_URL, DARTMOUTH_API_KEY, headers, scopes

# ***********************************************************************
# SOURCE DARTMOUTH DATA - employees
# ***********************************************************************

def get_dart_employees(DARTMOUTH_API_URL, DARTMOUTH_API_KEY, scopes):

    dart_jwt = utils.get_jwt(url=f"{DARTMOUTH_API_URL}/api/jwt", key=DARTMOUTH_API_KEY, scopes=scopes, session=requests.Session())

    log.info("Getting Dart employees with iPass from HRMS")
    dart_employees = {dc_emp["netid"]: dc_emp for dc_emp in utils.get_resources(jwt=dart_jwt, url=f"{DARTMOUTH_API_URL}/api/employees", session=requests.Session())}
    log.info(f"Total number of dart_employees: {len(dart_employees)}")

    return dart_employees

# ********************************************************************************************************
# SOURCE EXCLUDED CREW CODES - crew codes that should not get updated in Planon but still exists for ipaas
# ********************************************************************************************************

# Load the crew codes from a separate JSON file
def load_excluded_crew_codes():
    with open('crew_codes_to_exclude.json', 'r') as f:
        excluded_crew_codes = json.load(f)
    return excluded_crew_codes

# ********************************************************************************************************
# SOURCE PLANON DATA - trades & labor groups by codes and syscodes, persons
# ********************************************************************************************************
# get_planon_data() doesn't require any parameters because it directly accesses the planon module objects. 
def get_planon_data():
    # TRADES
    log.info("Getting Planon trades")
    pln_trades = planon.Trade.find()

    pln_trades_by_syscodes = {trade.Syscode: trade for trade in pln_trades}
    log.debug(f"{pln_trades_by_syscodes.keys()=}")

    pln_trades_by_codes = {trade.Code: trade for trade in pln_trades}
    log.debug(f"{pln_trades_by_codes.keys()=}")

    log.info(f"Total number of Planon trades: {len(pln_trades_by_codes)}")

    # LABOR_GROUPS
    # TODO Update Planon configuration to require the Code field
    log.info("Getting Planon labor rates")
    pln_laborgroups = planon.WorkingHoursTariffGroup.find()

    pln_laborgroups_by_syscodes = {laborgroup.Syscode: laborgroup for laborgroup in pln_laborgroups if laborgroup.Code}
    log.debug(f"pln_laborgroup{pln_laborgroups_by_syscodes.keys()=}")

    pln_laborgroups_by_codes = {laborgroup.Code: laborgroup for laborgroup in pln_laborgroups if laborgroup.Code}
    log.debug(f"pln_laborgroup{pln_laborgroups_by_codes.keys()=}")

    log.info(f"Total number of Planon labor groups: {len(pln_laborgroups)}")

    # PERSONS
    log.info("Getting Planon persons")
    pln_persons: dict[str, Person] = {pln_person.NetID: pln_person for pln_person in planon.Person.find() if pln_person.NetID is not None}
    for pln_person in pln_persons.values():
        assert pln_person.NetID is not None, f"NetID is None for {pln_person}"

    log.info(f"Total number of planon persons for updates: {len(pln_persons)}")
    
    return pln_trades_by_syscodes, pln_trades_by_codes, pln_laborgroups_by_syscodes, pln_laborgroups_by_codes, pln_persons

# ****************************************************************************************************************
# MAIN 
# ****************************************************************************************************************

# ****************************************************************************************************************
# UPDATES  for trade and labor group that has changes for personnel records
# ****************************************************************************************************************

def main():
    PLANON_API_URL, PLANON_API_KEY, DARTMOUTH_API_URL, DARTMOUTH_API_KEY, headers, scopes = setup()
    
    dart_employees = get_dart_employees(DARTMOUTH_API_URL, DARTMOUTH_API_KEY, scopes)
    excluded_crew_codes = load_excluded_crew_codes()
    pln_trades_by_syscodes, pln_trades_by_codes, pln_laborgroups_by_syscodes, pln_laborgroups_by_codes, pln_persons = get_planon_data()

    dart_employees_inserts = {
        dc_emp["netid"]: dc_emp for dc_emp in utils.get_resources(jwt=DARTMOUTH_API_KEY, url=f"{DARTMOUTH_API_URL}/api/employees", session=requests.Session()) if dc_emp["netid"] == "f007dch"
    }
    log.info(f"Total number of dart_employees: {len(dart_employees_inserts)}")

    pln_filter_inserts = {
        "filter": {
            # "EmploymenttypeRef": {"eq": "8"},  # Personnel>Employment types> 5 = Staff   #Supervisior:Internal Coordinator-'12';Internal
            # "FreeString7": {"exists": True}, # NetID, this ensures we only get Person records that have a NetID
            "FreeString7": {"eq": "f007dch"},  # d28941t d1150d8 #f003cg4 #d10918g #f003841
            # "FreeString2": {"eq": "Active"},  # dartmouth account status
            "IsArchived": {"eq": False},
            # "FreeInteger2": {'exists':False}, # Trade
            # "WorkingHoursTariffGroupRef": {"exists": False},
            # "FirstName":{"eq": "Jason"} #remove
        }
    }
    pln_persons_inserts = {pln_emp.NetID: pln_emp for pln_emp in planon.Person.find(pln_filter_inserts)}
    log.info(f"Total number of planon_employees for INSERTS : {str(len(pln_persons_inserts))}")



    log.info("Starting trade and labor group feed to Planon for UPDATES")

    updated_netids = []
    skipped_netids = []
    failed_netids = []

    for dart_employee in dart_employees_inserts.values():
        log.debug(f"Processing {dart_employee['netid']}")

        try:
            pln_person = pln_persons_inserts[dart_employee["netid"]]

            active_crew_code = utils.get_active_facilities_crew_code(dart_employee)

            # compare crew codes on both sides 
            # ipaas side accounts for excluded crew codes such as ML, CEOPS
            # planon side accounts for getting syscode for trades and labor groups and then converts it into code equivalent - 53 converts to BAS for lg, 117 converts to BAS for trade
            ipaas_trade, ipaas_labor_group, pln_trade_code, pln_laborgroup_code = utils.compare_crewcodes(active_crew_code, pln_person, pln_trades_by_syscodes, pln_laborgroups_by_syscodes,excluded_crew_codes)
            
            # return '' for crewcodes that retun None,so it is in similar format on both sides
            ipaas_trade = '' if ipaas_trade is None else ipaas_trade
            ipaas_labor_group = '' if ipaas_labor_group is None else ipaas_labor_group

            # compare code to similar to IPaas format
            person_ipaas = {
                "trade": ipaas_trade,
                "labor_group": ipaas_labor_group
            }

            person_pln = {
                "trade": pln_trade_code if pln_trade_code  else "",
                "labor_group": pln_laborgroup_code if pln_laborgroup_code else ""
            }

            # after comparing , convert it back to trade& labor group list , so we can access syscode 
            # syscode is stored in Planon side, not code
            pln_trade = pln_trades_by_codes[active_crew_code] if active_crew_code else ""
            pln_laborgroup = pln_laborgroups_by_codes[active_crew_code] if active_crew_code else ""

            # UPDATES to trade and labor group:
            if person_ipaas != person_pln:
                log.info(f"Syncing {pln_person.NetID}")
                pln_person.WorkingHoursTariffGroupRef = pln_laborgroup.Syscode if pln_laborgroup else None
                pln_person.TradeRef = pln_trade.Syscode if pln_trade else None

                pln_person = pln_person.save()
                updated_netids.append(pln_person.NetID)
                
                log.info(f"Record {pln_person.NetID} updated with {active_crew_code}")
            else:
                log.debug(f"Record {pln_person.NetID} skipped, already has the correct trade & labor group for {active_crew_code}")
                skipped_netids.append(pln_person.NetID)

        except Exception as ex:
            log.exception(f"Failed to update {dart_employee['netid']} due to {ex}")
            failed_netids.append({"netid": dart_employee["netid"], "exception": ex})
        
    log.info(f"Total number of successful trade and labor group updates: {len(updated_netids)}")
    log.info(f"Total number of skipped employees, who have correct crew in Planon: {len(skipped_netids)}")
    log.info(f"Total number of failures : {len(failed_netids)}")

# ****************************************************************************************************************
    log.info(
        f"""Logging results\n
    # ======================= RESULTS ======================= #

    UPDATED:
    Employees updated with trade and labor group: {len(updated_netids)} {updated_netids} \n

    SKIPPED:
    Employees skipped : {len(skipped_netids)} \n

    FAILED:
    Employees failed updating: {len(failed_netids)} {failed_netids}\n

    """
    )

    # *************************************************************************************************
    # Set exit code
    # *************************************************************************************************

    # Check if any failed_netid has KeyError for trade, labor group or personnel record , if so then mark unstable build 
    for failed_netid in failed_netids:
        if isinstance(failed_netid["exception"], KeyError) :
            log.warning(f"Unstable build - {len(failed_netids)} failure due to archived trade , labor group or keyerror for a personnel record")
            sys.exit(57)  #unstable build exit code
        else:
            log.info("Updates were processed successfully, exiting")
            sys.exit(os.EX_OK)  # Set exit code indicating successful execution

# ****************************************************************************************************************
# main() allows to execute code When the file Runs as a Script, but not when its imported as a Module
if __name__ == "__main__":
    main()
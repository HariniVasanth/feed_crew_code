import logging
from typing import Any
import json

import requests
from requests.adapters import HTTPAdapter, Retry

import planon

# *********************************************************************
# LOGGING - set of log messages
# *********************************************************************

log = logging.getLogger(__name__)

# *********************************************************************
# SETUP - of API KEY,header
# retry session , if error
# *********************************************************************

PAGE_SIZE = 1000
RETRIES = 3

session = requests.Session()
session.headers["Accept"] = "application/json"

MAX_RETRY = 5
MAX_RETRY_FOR_SESSION = 5
BACK_OFF_FACTOR = 1
TIME_BETWEEN_RETRIES = 1000
ERROR_CODES = (400, 401, 405, 500, 502, 503)

### Retry mechanism for server error ### https://stackoverflow.com/questions/23267409/how-to-implement-retry-mechanism-into-python-requests-library###
# {backoff factor} * (2 ** ({number of total retries} - 1))
retry_strategy = Retry(total=25, backoff_factor=1, status_forcelist=ERROR_CODES)
session.mount("https://", HTTPAdapter(max_retries=retry_strategy))

# ********************************************************************
# SOURCE EXCLUDED CREW CODES
# ********************************************************************

# Load the crew codes from a separate JSON file
with open("crew_codes_to_exclude.json", "r") as f:
    excluded_crew_codes = json.load(f)

# *******************************************************************************
# FUNCTIONS 
# get login_jwt & get_resources
# *******************************************************************************
    
# *******************************************************************************
# get login_jwt - get auth key & assign the requests to reponse using post method
# *******************************************************************************
    
# Generate jwt
def get_jwt(
    url: str, key: str, scopes: str, session: requests.Session = session
) -> str:
    """Returns a jwt for authentication to the iPaaS APIs

    Args:
        url (str): LOGIN_URL= https://api.dartmouth.edu/api/jwt
        key (str): API_KEY

    Returns:
        _type_: str
    """
    headers = {"Authorization": key}

    if scopes:
        url = url + "?scope=" + scopes
    else:
        url = url

    response = session.post(url=url, headers=headers)

    if response.ok:
        response_json = response.json()
        jwt = response_json["jwt"]
    else:
        response_json = response.json()
        error = response_json["Failed to obtain a jwt"]
        raise Exception(error)

    return jwt

# *******************************************************************************
# get_resources
# Construct the URL for fetching resources with pagination parameters
# Send a GET request to the constructed URL with the provided headers
# Raise an HTTPError if the response status code indicates an error 
# append the list to resources
# In case, if error occurs retry
# *******************************************************************************
    
# Get_resources: access all resources
def get_resources(
    jwt: str, url: str, session: requests.Session = session
) -> list[dict[str, Any]]:
    """Feeds in URL and get response of respurces as objects"""
    """Returns all the resources from dart_api
    Args:
        jwt (str): JWT token from .env file
        url (str): URL of the API (e.g., https://api.dartmouth.edu/employees)
        session (requests.Session): Optional session for making requests
    Returns:
        List[Dict]: List of resources records
    """
    headers: dict = {
        "Authorization": "Bearer " + jwt,
        "Content-Type": "application/json",
    }
    page_number: int = 1
    resources = []

    while True:
        resources_url = f"{url}?pagesize={PAGE_SIZE}&page={page_number}" # url
        response = session.get(url=resources_url, headers=headers) # get method
        response.raise_for_status()  #raise http error      

        # Convert the response content to JSON format
        response_json = response.json()

        # used to append the data from the response to the resources list
        resources.extend(response_json)    

        log.debug(f"Records returned, so far: {len(resources)}")

        # response will always be equal PAGE_SIZE(1000), unless it is last page
        if len(response_json) < PAGE_SIZE:
            break  # Exit the loop since it's the last page
        
        page_number += 1

    dart_resources = {dc_resource["netid"]: dc_resource for dc_resource in resources}  # dictionary of Dartmouth resources with netid as the key
    log.info(f"Total number of dart_resources: {len(dart_resources)}")
    return resources

# *******************************************************************************
# get_active_facilities_crew_code
# Extracts the active crew code from the given employee data
# Parses the employee data to collect unique active crew codes
# Raises a ValueError if there are multiple unique active crew codes
# Returns the active crew code, or an empty string if none is found
# *******************************************************************************

def get_active_facilities_crew_code(employee: dict[str, Any]) -> str:
    """
    Extracts the active crew code from the given employee data.

    This function parses the employee data, which is expected to be a dictionary
    containing an 'jobs' key. Each job should be a dictionary containing a 'maintenance_crew' key,
    which in turn should contain a 'crew_code' key. The function collects all unique active crew codes
    not in the excluded_crew_codes list. If there is more than one unique active crew code, it raises a ValueError.
    If there are no active crew codes, it returns an empty string.

    Args:
        employee (dict): The employee data, structured as described above.

    Returns:
        str: The active crew code, or an empty string if there are no active crew codes.

    Raises:
        ValueError: If there are more than one unique active crew codes.
    """

    # VERIFY: employee is a dictionary
    if not isinstance(employee, dict):
        raise TypeError(
            f"Expected 'employee' to be a dictionary, but got {type(employee)}"
        )

    active_crew_codes = set()

    if employee["jobs"] is None:
        log.debug(f"employee with netid '{employee['netid']}' has no jobs")
        return ""

    for job in employee.get("jobs", []):
        if (
            "maintenance_crew" in job
            and job["maintenance_crew"]["crew_code"] is not None
            and job["maintenance_crew"]["crew_code"] not in excluded_crew_codes
            and job["job_current_status"] == "Active"
        ):
            active_crew_codes.add(job["maintenance_crew"]["crew_code"])

    if len(set(active_crew_codes)) > 1:
        raise ValueError(
            f"employee with netid '{employee['netid']}' has multiple active crew codes: {active_crew_codes}"
        )

    active_crew_code = active_crew_codes.pop() if active_crew_codes else ""

    return active_crew_code


# *******************************************************************************
# compare_crewcodes
#Extracts relevant trade and labor group codes for IPaaS and Planon comparison
# Returns IPaaS trade, labor group, Planon trade code, and Planon labor group code

# *******************************************************************************

def compare_crewcodes(
    active_crew_code: str,
    pln_person: planon.Person,
    pln_trades_by_syscodes: dict[int, planon.Trade],
    pln_laborgroups_by_syscodes: dict[int, planon.WorkingHoursTariffGroup],
    excluded_crew_codes: list[str],
):

    """
    Compare the crew codes for a person and return relevant information.

    Args:
        active_crew_code (str): The active crew code for the person.
        pln_person (planon.Person): The Planon person object.
        pln_trades_by_syscodes (dict[int, planon.Trade]): A dictionary mapping Planon trade syscodes to Trade objects.
        pln_laborgroups_by_syscodes (dict[int, planon.WorkingHoursTariffGroup]): A dictionary mapping Planon labor group syscodes to WorkingHoursTariffGroup objects.
        excluded_crew_codes (list[str]): A list of crew codes to be excluded from comparison.

    Returns:
        tuple: A tuple containing the following information:
            - ipaas_trade (str): The determined IPaaS trade code.
            - ipaas_laborgroup (str): The determined IPaaS labor group code.
            - pln_trade_code (str): The Planon trade code associated with the person.
            - pln_laborgroup_code (str): The Planon labor group code associated with the person.
    """

    ipaas_trade = (
        active_crew_code if active_crew_code not in excluded_crew_codes else ""
    )

    ipaas_laborgroup = (
        active_crew_code if active_crew_code not in excluded_crew_codes else ""
    )

    pln_person_trade = (
        pln_trades_by_syscodes.get(pln_person.TradeRef) if pln_person.TradeRef else ""
    )

    pln_person_laborgroup = (
        pln_laborgroups_by_syscodes.get(pln_person.WorkingHoursTariffGroupRef)
        if pln_person.WorkingHoursTariffGroupRef
        else ""
    )

    pln_trade_code = pln_person_trade.Code if pln_person_trade else ""
    pln_laborgroup_code = pln_person_laborgroup.Code if pln_person_laborgroup else ""

    return ipaas_trade, ipaas_laborgroup, pln_trade_code, pln_laborgroup_code



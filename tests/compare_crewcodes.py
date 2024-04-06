import planon

def compare_crewcodes_test(
    active_crew_code: str,
    pln_person: planon.Person,  
    pln_trades_by_syscodes: dict[int, planon.Trade],
    pln_laborgroups_by_syscodes: dict[int, planon.WorkingHoursTariffGroup],
    excluded_crew_codes: list[str],
):

    ipaas_trade = (
        active_crew_code if active_crew_code not in excluded_crew_codes else ""
    )

    ipaas_laborgroup = (
        active_crew_code if active_crew_code not in excluded_crew_codes else ""
            )
    
    pln_person_key = list(pln_person.keys())[0]

    trade_ref = pln_person[pln_person_key]['TradeRef']
    pln_person_trade = (
        pln_trades_by_syscodes.get(trade_ref)  # Accessing trade_ref directly here
        if trade_ref  # Checking if trade_ref exists
        else ""
    )

    laborgroup_ref = pln_person[pln_person_key ]['WorkingHoursTariffGroupRef']

    pln_person_laborgroup = (
        pln_laborgroups_by_syscodes.get(laborgroup_ref)
        if laborgroup_ref
        else ""
    )

    pln_trade_code = pln_person_trade.Code if pln_person_trade else ""
    pln_laborgroup_code = pln_person_laborgroup.Code if pln_person_laborgroup else ""

    return ipaas_trade, ipaas_laborgroup, pln_trade_code, pln_laborgroup_code


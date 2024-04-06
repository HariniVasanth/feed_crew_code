# feed_crew_code
This Python automation script will feed the crew_code from Dart API using iPaas and feed it to Planon under WorkManagement > Personnel > Trade and labor group

## Getting started
Build containers 
Main : Python main.py
Unit test :  python -m unittest tests/unittest.py

## Setup:
Get crew code from Dartmouth API and compare the value for the same person in Planon , if not the same then update
Get syscide for dartmouth crew code and insert it in Planon labor group and trade field

EMP_URL=DARTMOUTH_API_URL/api/employees
pln_persons = {pln_person.NetID: pln_person for pln_person in planon.Person.find()}



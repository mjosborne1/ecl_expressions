import os
import subprocess
import json
from urllib import parse
import requests
from fhirpathpy import evaluate
import logging

logger = logging.getLogger(__name__)

def count_valueset(vs_endpoint, valueset_url):
    """
    Count the total number of values in a ValueSet using a direct query 
    pass parameter count=1 to trick the query into expanding and including the total 
    even if it's >50K in size.
    """
    vsexp=vs_endpoint+'/ValueSet/$expand?url='
    query=vsexp+parse.quote(valueset_url,safe='')
    query = f"{query}&count=1"
    command = ['curl', '-H "Accept: application/fhir+json" ' , '--location', query]
    
    result = subprocess.run(command, capture_output=True)
    data =  json.loads(result.stdout)
    try:
        total_result = evaluate(data,"expansion.total")
    except Exception as e:
        logger.error(f'Failed to retrieve total for ValueSet: {e}')
        return -1
    
    total = -1
    if total_result:
        # Handle the case where evaluate returns a list or a single value
        if isinstance(total_result, list) and len(total_result) > 0:
            total = total_result[0]
        elif not isinstance(total_result, list):
            total = total_result
    return total

##
def run_ecl_expansion():
    return ""
import os
import subprocess
import json
from urllib import parse
import requests
from fhirpathpy import evaluate
import logging

logger = logging.getLogger(__name__)

def write_bundle_data(endpoint, token, outfile):
    """
    Write the syndicated bundles to outfile
    """
    headers = {
        'Authorization': f"{token['token_type']} {token['access_token']}",
        'Accept': 'application/fhir+json'
    }
    response = requests.get(endpoint, headers=headers)
    with open(outfile, 'wb') as f:
        f.write(response.content)


def expand_valueset(vs_endpoint, ecl_expr, count):
    """
    Expand a ValueSet using ECL expression and return both total count and first N results
    """
    vsexp=vs_endpoint+'/ValueSet/$expand?url=http://snomed.info/sct?fhir_vs=ecl/'
    query=vsexp+parse.quote(ecl_expr,safe='')
    query = f"{query}&count={count}"
    command = ['curl', '-H', 'Accept: application/fhir+json', '--location', query]
    
    result = subprocess.run(command, capture_output=True)
    
    # Log the response for debugging
    if result.returncode != 0:
        logger.error(f'Curl command failed with return code {result.returncode}')
        logger.error(f'stderr: {result.stderr.decode()}')
        return {
            'total': -1,
            'concepts': [],
            'error': f'API request failed: {result.stderr.decode()}'
        }
    
    if not result.stdout:
        logger.error('Empty response from FHIR server')
        return {
            'total': -1,
            'concepts': [],
            'error': 'Empty response from FHIR server'
        }
    
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        logger.error(f'Failed to parse JSON response: {e}')
        logger.error(f'Response content: {result.stdout.decode()[:500]}')
        return {
            'total': -1,
            'concepts': [],
            'error': f'Invalid JSON response: {str(e)}'
        }
    
    try:
        # Get total count
        total_result = evaluate(data,"expansion.total")
        total = -1
        if total_result:
            if isinstance(total_result, list) and len(total_result) > 0:
                total = total_result[0]
            elif not isinstance(total_result, list):
                total = total_result
        
        # Get the actual concept results
        concepts = []
        contains_result = evaluate(data, "expansion.contains")
        if contains_result and isinstance(contains_result, list):
            for concept in contains_result:
                code = ""
                display = ""
                
                # Extract code
                code_result = evaluate(concept, "code")
                if code_result:
                    if isinstance(code_result, list) and len(code_result) > 0:
                        code = str(code_result[0])
                    elif not isinstance(code_result, list):
                        code = str(code_result)
                
                # Extract display
                display_result = evaluate(concept, "display")
                if display_result:
                    if isinstance(display_result, list) and len(display_result) > 0:
                        display = str(display_result[0])
                    elif not isinstance(display_result, list):
                        display = str(display_result)
                
                if code:  # Only add if we have a code
                    concepts.append({
                        'code': code,
                        'display': display or code  # Use code as fallback if no display
                    })
        
        return {
            'total': total,
            'concepts': concepts
        }
        
    except Exception as e:
        logger.error(f'Failed to retrieve data for ValueSet: {e}')
        return {
            'total': -1,
            'concepts': [],
            'error': str(e)
        }


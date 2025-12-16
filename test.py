import os, shutil
import json
import urllib
import unittest
import fetcher
import glob
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_ENDPOINT = os.getenv("TX_ENDPOINT", 'https://tx.ontoserver.csiro.au/fhir')

def create_test_folder():
    homedir=os.environ['HOME']
    npm_dir = os.path.join(homedir,"tmp","ecl-test")       
    if os.path.exists(npm_dir): 
        shutil.rmtree(npm_dir)
    os.makedirs(npm_dir) 
    return npm_dir

def read_ecl_files():
    """Read all ECL files from the ecl_library directory - same logic as main.py"""
    ecl_files = []
    
    # Find all .txt files in ecl_library subdirectories
    pattern = os.path.join('ecl_library', '**', '*.txt')
    files = glob.glob(pattern, recursive=True)
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            # Extract the description (# line) and non-comment ECL expression
            lines = content.split('\n')
            description = ""
            ecl_expression = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('#'):
                    if not description:
                        description = line.lstrip('#').strip()
                elif line and not line.startswith('#'):
                    ecl_expression.append(line)
            
            if ecl_expression:
                ecl_files.append({
                    'filename': os.path.basename(file_path),
                    'path': file_path,
                    'description': description or "No description available",
                    'expression': '\n'.join(ecl_expression),
                    'category': os.path.basename(os.path.dirname(file_path))
                })
                
        except Exception as e:
            print(f'Error reading file {file_path}: {e}')
    
    return ecl_files


class TestECLLibrary(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.ecl_files = read_ecl_files()
    
    def test_ecl_library_exists(self):
        """Test that the ECL library directory exists and contains files"""
        self.assertTrue(os.path.exists('ecl_library'), "ECL library directory should exist")
        self.assertGreater(len(self.ecl_files), 0, "ECL library should contain at least one file")
    
    def test_ecl_files_have_required_fields(self):
        """Test that all ECL files have required fields"""
        for ecl_file in self.ecl_files:
            with self.subTest(filename=ecl_file['filename']):
                self.assertIn('filename', ecl_file)
                self.assertIn('description', ecl_file)
                self.assertIn('expression', ecl_file)
                self.assertIn('category', ecl_file)
                self.assertIn('path', ecl_file)
    
    def test_ecl_files_have_descriptions(self):
        """Test that ECL files have meaningful descriptions"""
        for ecl_file in self.ecl_files:
            with self.subTest(filename=ecl_file['filename']):
                self.assertNotEqual(ecl_file['description'], "", 
                                  f"File {ecl_file['filename']} should have a description")
                self.assertNotEqual(ecl_file['description'], "No description available",
                                  f"File {ecl_file['filename']} should have a meaningful description")
    
    def test_ecl_files_have_expressions(self):
        """Test that ECL files contain actual ECL expressions"""
        for ecl_file in self.ecl_files:
            with self.subTest(filename=ecl_file['filename']):
                self.assertNotEqual(ecl_file['expression'].strip(), "", 
                                  f"File {ecl_file['filename']} should have an ECL expression")
                self.assertGreater(len(ecl_file['expression'].strip()), 10,
                                 f"File {ecl_file['filename']} should have a substantial ECL expression")
    
    def test_ecl_categories_are_valid(self):
        """Test that ECL files are properly categorized"""
        categories = set(ecl_file['category'] for ecl_file in self.ecl_files)
        expected_categories = {'AMT', 'ClinicalFindings'}  # Add more as needed
        
        for category in categories:
            self.assertIn(category, expected_categories, 
                         f"Category '{category}' should be in expected categories")
    
    def test_amt_category_files(self):
        """Test specific properties of AMT category files"""
        amt_files = [f for f in self.ecl_files if f['category'] == 'AMT']
        self.assertGreater(len(amt_files), 0, "Should have at least one AMT file")
        
        for amt_file in amt_files:
            with self.subTest(filename=amt_file['filename']):
                # AMT files should contain reference sets or specific SNOMED codes
                expression = amt_file['expression']
                self.assertTrue(
                    '929360031000036100' in expression or  # TPUU reference set
                    '929360061000036106' in expression or  # MP reference set
                    'reference set' in expression.lower(),
                    f"AMT file {amt_file['filename']} should reference AMT reference sets"
                )
    
    def test_clinical_findings_files(self):
        """Test specific properties of ClinicalFindings category files"""
        cf_files = [f for f in self.ecl_files if f['category'] == 'ClinicalFindings']
        if len(cf_files) > 0:  # Only test if we have clinical findings files
            for cf_file in cf_files:
                with self.subTest(filename=cf_file['filename']):
                    expression = cf_file['expression']
                    # Clinical findings should contain SNOMED CT codes
                    self.assertTrue(
                        any(char.isdigit() for char in expression),
                        f"Clinical findings file {cf_file['filename']} should contain SNOMED CT codes"
                    )


class TestFetcher(unittest.TestCase):    

    def test_expand_valueset_with_simple_ecl(self):
        """Test that expand_valueset works with a simple ECL expression"""
        # Use a simple ECL expression that should return results
        ecl_expression = "< 404684003 |Clinical finding|"
        result = fetcher.expand_valueset(API_ENDPOINT, ecl_expression, 5)
        
        self.assertIsInstance(result, dict, "Result should be a dictionary")
        self.assertIn('total', result, "Result should contain 'total' key")
        self.assertIn('concepts', result, "Result should contain 'concepts' key")
        self.assertGreater(result['total'], 0, "Should return some clinical findings")
        self.assertIsInstance(result['concepts'], list, "Concepts should be a list")
    
    def test_expand_valueset_with_invalid_ecl(self):
        """Test that expand_valueset handles invalid ECL expressions gracefully"""
        # Use an invalid ECL expression
        ecl_expression = "invalid ecl expression"
        result = fetcher.expand_valueset(API_ENDPOINT, ecl_expression, 5)
        
        self.assertIsInstance(result, dict, "Result should be a dictionary")
        # Should either return error or empty results
        self.assertTrue(
            result['total'] == -1 or 'error' in result,
            "Invalid ECL should return error or -1 total"
        )
    
    def test_expand_valueset_concepts_structure(self):
        """Test that returned concepts have proper structure"""
        ecl_expression = "< 404684003 |Clinical finding|"
        result = fetcher.expand_valueset(API_ENDPOINT, ecl_expression, 3)
        
        if result['total'] > 0 and result['concepts']:
            for concept in result['concepts']:
                with self.subTest(concept=concept):
                    self.assertIn('code', concept, "Concept should have 'code' field")
                    self.assertIn('display', concept, "Concept should have 'display' field")
                    self.assertNotEqual(concept['code'], "", "Code should not be empty")
                    self.assertNotEqual(concept['display'], "", "Display should not be empty")
    
    def test_expand_valueset_with_library_expressions(self):
        """Test expand_valueset with actual expressions from the library"""
        ecl_files = read_ecl_files()
        
        # Test with first few expressions from the library
        for ecl_file in ecl_files[:3]:  # Test first 3 to avoid long test times
            with self.subTest(filename=ecl_file['filename']):
                result = fetcher.expand_valueset(API_ENDPOINT, ecl_file['expression'], 5)
                
                self.assertIsInstance(result, dict, f"Result for {ecl_file['filename']} should be a dictionary")
                self.assertIn('total', result, f"Result for {ecl_file['filename']} should contain 'total' key")
                
                # Allow for expressions that return no results (total=0) as this might be valid
                self.assertGreaterEqual(result['total'], 0, 
                                      f"Total for {ecl_file['filename']} should be >= 0 or -1 for errors")


class TestSearch(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures for search tests"""
        from main import app
        app.config['TESTING'] = True
        self.app = app.test_client()
    
    def test_search_endpoint_exists(self):
        """Test that the search endpoint is accessible"""
        response = self.app.get('/search_ecl?q=test')
        self.assertEqual(response.status_code, 200)
    
    def test_search_with_empty_query(self):
        """Test search with empty query returns empty results"""
        response = self.app.get('/search_ecl?q=')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 0)
    
    def test_search_with_short_query(self):
        """Test search with short query (< 2 chars) returns empty results"""
        response = self.app.get('/search_ecl?q=a')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 0)
    
    def test_search_with_valid_query(self):
        """Test search with valid query returns structured results"""
        response = self.app.get('/search_ecl?q=injection')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Should return some results for 'injection' if we have injection-related ECL files
        if len(data) > 0:
            for result in data:
                self.assertIn('filename', result)
                self.assertIn('description', result)
                self.assertIn('category', result)
                self.assertIn('expression', result)
                self.assertIn('match_score', result)
    
    def test_search_case_insensitive(self):
        """Test that search is case insensitive"""
        response1 = self.app.get('/search_ecl?q=injection')
        response2 = self.app.get('/search_ecl?q=INJECTION')
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)
        
        # Should return same results regardless of case
        self.assertEqual(len(data1), len(data2))
    
    def test_search_limits_results(self):
        """Test that search limits results to prevent overwhelming UI"""
        response = self.app.get('/search_ecl?q=a')  # Very broad search
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Should limit to 10 results maximum
        self.assertLessEqual(len(data), 10)
    
    def test_search_expression_truncation(self):
        """Test that long expressions are truncated in search results"""
        response = self.app.get('/search_ecl?q=reference')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        if len(data) > 0:
            for result in data:
                # Expression should be truncated if longer than 100 chars
                if len(result['expression']) > 100:
                    self.assertTrue(result['expression'].endswith('...'))


class TestValueSetURL(unittest.TestCase):
    """Test the ValueSet URL generation functionality"""
    
    def test_simple_ecl_encoding(self):
        """Test URL encoding of a simple ECL expression"""
        ecl = "< 404684003"
        encoded = urllib.parse.quote(ecl)
        url = f"http://snomed.info/sct?fhir_vs=ecl/{encoded}"
        
        self.assertEqual(url, "http://snomed.info/sct?fhir_vs=ecl/%3C%20404684003")
        self.assertIn("http://snomed.info/sct?fhir_vs=ecl/", url)
    
    def test_complex_ecl_encoding(self):
        """Test URL encoding of a complex ECL expression with special characters"""
        ecl = "< 404684003 |Clinical finding|: 363698007 |Finding site| = << 39057004 |Pulmonary valve structure|"
        encoded = urllib.parse.quote(ecl)
        url = f"http://snomed.info/sct?fhir_vs=ecl/{encoded}"
        
        # Verify the URL contains the correct base
        self.assertIn("http://snomed.info/sct?fhir_vs=ecl/", url)
        
        # Verify special characters are encoded
        self.assertIn("%3C", encoded)  # <
        self.assertIn("%7C", encoded)  # |
        self.assertIn("%3D", encoded)  # =
        self.assertIn("%20", encoded)  # space
        
        # Verify the URL can be decoded back to the original
        decoded_ecl = urllib.parse.unquote(encoded)
        self.assertEqual(decoded_ecl, ecl)
    
    def test_ecl_with_newlines(self):
        """Test URL encoding of ECL expression with newlines"""
        ecl = "< 404684003 |\nClinical finding\n|"
        encoded = urllib.parse.quote(ecl)
        url = f"http://snomed.info/sct?fhir_vs=ecl/{encoded}"
        
        # Verify newlines are encoded
        self.assertIn("%0A", encoded)
        
        # Verify the URL contains the correct base
        self.assertIn("http://snomed.info/sct?fhir_vs=ecl/", url)
    
    def test_ecl_url_pattern(self):
        """Test that the ValueSet URL follows the correct pattern"""
        ecl = "< 373873005"
        encoded = urllib.parse.quote(ecl)
        url = f"http://snomed.info/sct?fhir_vs=ecl/{encoded}"
        
        # Verify URL structure
        self.assertTrue(url.startswith("http://snomed.info/sct?fhir_vs=ecl/"))
        self.assertEqual(url.count("?fhir_vs=ecl/"), 1)
        self.assertEqual(url.count("http://"), 1)
    
    def test_empty_ecl(self):
        """Test handling of empty ECL expression"""
        ecl = ""
        encoded = urllib.parse.quote(ecl)
        url = f"http://snomed.info/sct?fhir_vs=ecl/{encoded}"
        
        # Even with empty ECL, the URL structure should be correct
        self.assertEqual(url, "http://snomed.info/sct?fhir_vs=ecl/")
    
    def test_ecl_with_quotes(self):
        """Test URL encoding of ECL with various quote types"""
        ecl = '< 404684003 "quoted text" and \'single quotes\''
        encoded = urllib.parse.quote(ecl)
        url = f"http://snomed.info/sct?fhir_vs=ecl/{encoded}"
        
        # Verify quotes are encoded
        self.assertIn("%22", encoded)  # "
        self.assertIn("%27", encoded)  # '
        
        # Verify the URL can be decoded back
        decoded_ecl = urllib.parse.unquote(encoded)
        self.assertEqual(decoded_ecl, ecl)


if __name__ == '__main__':
    unittest.main()
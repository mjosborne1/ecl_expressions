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


if __name__ == '__main__':
    unittest.main()
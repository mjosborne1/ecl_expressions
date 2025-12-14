# ECL Expression Tester

A Flask web application for testing SNOMED CT Expression Constraint Language (ECL) expressions against a FHIR terminology server. This tool allows you to load ECL expressions from a library of files and test them to see both the total count of matching concepts and sample results.

## Features

- 📁 **ECL Library Management**: Automatically loads ECL expressions from organized folders
- 🔍 **Interactive Testing**: Test ECL expressions with a single click
- � **Smart Search**: Typeahead search functionality to find expressions by keyword
- �📊 **Detailed Results**: Shows both total count and sampled results (first 25 concepts)
- 🏷️ **Rich Metadata**: Displays descriptions and categories for each ECL expression
- 📱 **Responsive UI**: Clean, modern web interface with filtering capabilities
- 📝 **Comprehensive Logging**: Tracks all testing activities
- ⚡ **Real-time Search**: Dynamic search with debouncing and relevance scoring

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Access to a FHIR terminology server (default: CSIRO Ontoserver)

## Installation

### 1. Clone or Download the Repository

```bash
git clone https://github.com/mjosborne1/ecl_expressions
cd ecl_expressions
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv .venv
```

### 3. Activate the Virtual Environment

**On macOS/Linux:**
```bash
source .venv/bin/activate
```

**On Windows:**
```bash
.venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

The application uses environment variables for configuration. These are already set up in the `.env` file:

```properties
# Terminology Server Endpoint
TX_ENDPOINT=https://tx.ontoserver.csiro.au/fhir

# Log file location
LOGFILENAME=./logs/ecl.log
```

You can modify these values if needed:
- **TX_ENDPOINT**: Change to use a different FHIR terminology server
- **LOGFILENAME**: Change the log file location

## ECL Library Structure

The application reads ECL expressions from the `ecl_library/` directory. Each file should:

1. **Have a `.txt` extension**
2. **Include a description** as the first line starting with `#`
3. **Contain the ECL expression** on subsequent lines (non-comment lines)

**Example file structure:**
```
ecl_library/
├── AMT/
│   ├── 01-01-TPUU-Dose-Form-Injection.txt
│   ├── 02-01-TPUU-Ingrediant-Gentamicin-Only.txt
│   └── ...
└── ClinicalFindings/
    ├── 01-FindingSite-BoneFracture.txt
    └── ...
```

**Example file content:**
```
# All TPUUs that have a manufactured dose form of injection and subtypes
^ 929360031000036100 |Trade product unit of use reference set|:
411116001 |Has manufactured dose form| = << 129011000036109 |Injection|
```

## Running it online

Open your web browser and navigate to:
```
https://ecl-tester.onrender.com
```

## Running the Application Locally

### 1. Start the Flask Application

```bash
python main.py
```

### 2. Access the Web Interface

Open your web browser and navigate to:
```
http://localhost:5001
```

### 3. Using the Application

1. **Browse ECL Expressions**: The main page displays all ECL expressions organized by category
2. **Search Expressions**: Use the search box to find expressions by keyword
   - Type at least 2 characters to start searching
   - Search works on filenames, descriptions, and expression content
   - Results are ranked by relevance score
   - Click on search results to view or test expressions
3. **Filter by Category**: Use the category buttons to show only specific types of expressions
4. **Read Descriptions**: Each expression shows its filename, description, and the actual ECL code
5. **Test Expressions**: Click "Test Expression" to run the ECL against the terminology server
6. **View Results**: See both the total count and sampled results (first 25 matching concepts)

### Search Functionality

The search feature provides:
- **Real-time search**: Results appear as you type (with 300ms debouncing)
- **Relevance scoring**: Results ranked by how well they match your search
- **Multi-field search**: Searches filenames, descriptions, and expression content
- **Quick access**: Click any result to immediately view the expression

**Search API Endpoint**:
```
GET /search_ecl?q=<search_term>
```

Returns JSON array with:
- `filename`: Expression file name
- `description`: Human-readable description
- `category`: AMT, ClinicalFindings, etc.
- `expression`: ECL expression (truncated if > 100 chars)
- `match_score`: Relevance score for ranking

## Application Structure

```
ecl_expressions/
├── main.py                 # Flask application
├── fetcher.py             # FHIR terminology server interface
├── requirements.txt       # Python dependencies
├── .env                  # Environment configuration
├── .gitignore           # Git ignore rules
├── templates/
│   └── index.html       # Web interface template
├── logs/                # Log files (gitignored)
├── ecl_library/         # ECL expression library
│   ├── AMT/            # Australian Medicines Terminology examples
│   └── ClinicalFindings/ # Clinical findings examples
└── .venv/              # Virtual environment (gitignored)
```

## Dependencies

The application requires the following Python packages:

- **Flask**: Web framework
- **python-dotenv**: Environment variable management
- **requests**: HTTP client for API calls
- **fhirpathpy**: FHIR path expression evaluation

## Logging

The application logs all activities to `./logs/ecl.log`, including:
- Application startup/shutdown
- ECL expression testing requests
- Results and any errors
- HTTP request logs

## Troubleshooting

### Port Already in Use
If port 5001 is already in use, you can change it in `main.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5002)  # Change port number
```

### Virtual Environment Issues
Make sure your virtual environment is activated before running the application:
```bash
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows
```

### Missing Dependencies
If you get import errors, reinstall dependencies:
```bash
pip install -r requirements.txt
```

### FHIR Server Connection Issues
Check that the terminology server endpoint in `.env` is accessible:
```bash
curl -H "Accept: application/fhir+json" https://tx.ontoserver.csiro.au/fhir/metadata
```

## Adding New ECL Expressions

1. Create a new `.txt` file in the appropriate `ecl_library/` subdirectory
2. Add a description as the first line starting with `#`
3. Add your ECL expression on the following lines
4. Refresh the web page - new expressions will appear automatically

## Testing

### Run All Tests
```bash
python test.py
```

The test suite includes:
- ECL library structure validation (8 tests)
- FHIR server integration testing (3 tests)  
- Search functionality testing (8 tests)

### Test Search Functionality
```bash
# Quick search functionality test
python test_search.py

# Extended search testing with various terms
python extended_search_test.py
```

### Individual Test Categories
- **Library Tests**: Validate ECL file structure and content
- **Fetcher Tests**: Test FHIR server connectivity and responses
- **Search Tests**: Verify search API endpoints and functionality

## Development

To run in development mode with auto-reload:
```bash
export FLASK_ENV=development  # Linux/macOS
# or
set FLASK_ENV=development     # Windows

python main.py
```

## License

See the `LICENSE` file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your ECL expressions to the `ecl_library/` directory
4. Test your changes
5. Submit a pull request

## Support

For issues or questions:
- Check the logs in `./logs/ecl.log`
- Verify your ECL syntax using the SNOMED CT Expression Constraint Language specification
- Ensure the terminology server is accessible

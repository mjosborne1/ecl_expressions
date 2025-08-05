import subprocess
import argparse
import fetcher

from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import json
import re
import logging
import os, shutil

homedir=os.environ['HOME']
api_endpoint=os.getenv("TX_ENDPOINT")
logfile_name=os.getenv("LOGFILENAME")

logger = logging.getLogger(__name__)
logging.basicConfig(filename=logfile_name, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger.info('Logs started')




logger.info('Completed')
logger.info('Logs finished')
   
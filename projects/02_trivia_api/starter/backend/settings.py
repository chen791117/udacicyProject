from dotenv import load_dotenv
import os 
load_dotenv() 
DB_NAME = os.environ.get("DB_NAME") 
DB_USER=os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

DBTEST_NAME = os.environ.get("DBTEST_NAME") 
DBTEST_USER=os.environ.get("DBTEST_USER")
DBTEST_PASSWORD = os.environ.get("DBTEST_PASSWORD")
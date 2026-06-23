#scripts/backup_database.py
#
# NOTE: This script runs `mongodump` as a local subprocess. It is intended
# for running on YOUR OWN MACHINE against your database (whether that's a
# local MongoDB or your Atlas cluster) -- it will not work on Streamlit
# Community Cloud, since that environment doesn't have the `mongodump`
# binary installed and isn't meant for running standalone scripts.
from database import mongo_manager
from datetime import datetime
import subprocess
import os

def backup_database():
    """Create a MongoDB backup. Run this locally, not on Streamlit Cloud."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    try:
        # Use mongodump for proper backup. Reuses the same connection string
        # resolution as the rest of the app (Streamlit secrets / env var),
        # so this backs up whichever database (local or Atlas) the app
        # itself is configured to use.
        result = subprocess.run([
            "mongodump",
            "--uri", mongo_manager.connection_string + "password_manager"
            if mongo_manager.connection_string.endswith("/")
            else mongo_manager.connection_string,
            "--out", backup_dir
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Backup created: {backup_dir}")
            return True
        else:
            print(f"❌ Backup failed: {result.stderr}")
            return False
           
    except Exception as e:
        print(f"❌ Backup error: {str(e)}")

        return False



import pandas as pd
import requests
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_data():
    urls = [
        "https://raw.githubusercontent.com/mwitiderrick/insurancedata/master/insurance_claims.csv",
        "https://raw.githubusercontent.com/TarekMostafa886/Insurance-Fraud-Detection/main/insurance_claims.csv",
        "https://raw.githubusercontent.com/manikanta-setty/Insurance-Fraud-Detection/master/insurance_claims.csv",
        "https://raw.githubusercontent.com/shreyashkawalkar/Insurance-Fraud-Detection/master/insurance_claims.csv"
    ]
    target_path = "data/real_world_claims.csv"
    
    if not os.path.exists("data"):
        os.makedirs("data")
        
    if os.path.exists(target_path):
        logger.info(f"File already exists at {target_path}")
        return
        
    for url in urls:
        logger.info(f"Attempting to download dataset from {url}...")
        try:
            df = pd.read_csv(url)
            df.replace('?', pd.NA, inplace=True)
            df.to_csv(target_path, index=False)
            logger.info(f"Successfully downloaded and saved to {target_path}")
            return
        except Exception as e:
            logger.error(f"Failed to download from {url}: {e}")
    
    logger.error("All download attempts failed.")

if __name__ == "__main__":
    download_data()

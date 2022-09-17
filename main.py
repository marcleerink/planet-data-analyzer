import geopandas as gpd
from data_api import do_search
import os
from datetime import datetime, timedelta

api_key = os.environ["PL_API_KEY"]
end_date = datetime.utcnow()
start_date = datetime.utcnow() - timedelta(days=7)
item_types = "PSScene"
asset_types = ["analytic_8b_sr_udm2"]
cc = 0.1

# For each AOI, construct search + determine best item(s)
data_df = do_search(api_key, item_types, start_date, end_date, cc)
print(data_df)
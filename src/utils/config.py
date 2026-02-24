USE_SIMULATED_DATA = False

SIMULATED_DATA_PATH = "data/simulated/demand_with_shocks.csv"
REAL_DATA_PATH = "data/raw/real_retail_demand.csv"


def get_data_path():
    return SIMULATED_DATA_PATH if USE_SIMULATED_DATA else REAL_DATA_PATH

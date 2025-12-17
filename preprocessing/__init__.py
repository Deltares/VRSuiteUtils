from pathlib import Path
generic_data = Path(__file__).parent.joinpath("generic_data")
external_bins = Path(__file__).parent.joinpath("externals")
hydraring_bin_dir = external_bins.joinpath("HydraRing-23.1.1")
dikernel_bin_dir = external_bins.joinpath("DiKErnel")
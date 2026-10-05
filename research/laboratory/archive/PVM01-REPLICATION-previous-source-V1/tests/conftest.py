"""The entire regression suite obeys the current recording-access exclusion."""
from nextai_autoresearch.data_access import install_data_access_guard

install_data_access_guard()

# Import all admin classes to register them
from .admin import *

# Import custom admin sites
from .admin_sites import (
    treasury_admin_site,
    operation_admin_site, 
    readonly_admin_site_1,
    readonly_admin_site_2
)

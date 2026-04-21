"""Dashboard pages module - imports all page renderers"""

from . import fleet_overview
from . import equipment_detail
from . import maintenance_schedule
from . import alert_feed
from . import kpi_dashboard

__all__ = ['fleet_overview', 'equipment_detail', 'maintenance_schedule', 'alert_feed', 'kpi_dashboard']

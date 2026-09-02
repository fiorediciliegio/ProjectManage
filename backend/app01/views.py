"""Backward-compatible facade for API views.

The implementation is split under ``app01.views_modules`` by business domain.
``Projectmanagement.urls`` still imports ``app01.views`` so existing route wiring
stays stable during the refactor.
"""

from app01.views_modules.common import *
from app01.views_modules.project_views import *
from app01.views_modules.person_views import *
from app01.views_modules.cost_views import *
from app01.views_modules.quality_views import *
from app01.views_modules.safety_views import *
from app01.views_modules.file_views import *
from app01.views_modules.rag_views import *

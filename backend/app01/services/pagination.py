from django.conf import settings
from django.core.paginator import Paginator


def _positive_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def get_pagination_params(request, default_page_size=None, max_page_size=None):
    default_page_size = default_page_size or getattr(settings, "API_DEFAULT_PAGE_SIZE", 50)
    max_page_size = max_page_size or getattr(settings, "API_MAX_PAGE_SIZE", 100)

    params = getattr(request, "query_params", request.GET)
    page = _positive_int(params.get("page"), 1)
    requested_page_size = _positive_int(params.get("page_size"), default_page_size)
    page_size = min(requested_page_size, max_page_size)
    return page, page_size


def paginate_queryset(queryset, request, default_page_size=None, max_page_size=None):
    page, page_size = get_pagination_params(
        request,
        default_page_size=default_page_size,
        max_page_size=max_page_size,
    )
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    pagination = {
        "page": page_obj.number,
        "page_size": page_size,
        "total": paginator.count,
        "total_pages": paginator.num_pages,
        "has_next": page_obj.has_next(),
        "has_previous": page_obj.has_previous(),
    }
    return page_obj.object_list, pagination


def pagination_cache_parts(request, default_page_size=None, max_page_size=None):
    page, page_size = get_pagination_params(
        request,
        default_page_size=default_page_size,
        max_page_size=max_page_size,
    )
    return f"page:{page}", f"page_size:{page_size}"

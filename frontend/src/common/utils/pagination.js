export const DEFAULT_PAGE_SIZE = 10;

export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

export const emptyPagination = (page = 0, pageSize = DEFAULT_PAGE_SIZE) => ({
  page: page + 1,
  page_size: pageSize,
  total: 0,
  total_pages: 0,
  has_next: false,
  has_previous: false,
});

export const normalizePagination = (pagination, page = 0, pageSize = DEFAULT_PAGE_SIZE, fallbackTotal = 0) => ({
  page: Number(pagination?.page || page + 1),
  page_size: Number(pagination?.page_size || pageSize),
  total: Number(pagination?.total ?? fallbackTotal),
  total_pages: Number(pagination?.total_pages || 0),
  has_next: Boolean(pagination?.has_next),
  has_previous: Boolean(pagination?.has_previous),
});

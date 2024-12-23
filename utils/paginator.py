from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class AppPageNumberPagination(PageNumberPagination):
    page_size = 10  # default page size
    max_page_size = 1000 #max page size
    page_query_param = '_page'
    page_size_query_param = '_limit'  # ?_page=xx&_limit=xx
    page_query_description = "获取记录的页码"
    page_size_query_description = "每一页的最大记录数"

    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'totalCount': self.page.paginator.count,
            'currentPageNum': self.page.number,
            'hasNextPage': self.page.has_next(),
            'hasPreviousPage': self.page.has_previous(),
            'results': data,
        })

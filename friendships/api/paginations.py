from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class FriendshipPagination(PageNumberPagination):
    # /api/friendships/1/followers/?page=3&size=10

    # default page size (url param does not contain)
    page_size = 20

    # default page_size_query_param is None, i.e. client not allowed to specify
    page_size_query_param = 'size'
    # max page_size allowed for client side
    max_page_size = 20

    def get_paginated_response(self, data):
        return Response({
            'total_results': self.page.paginator.count,  # num of data
            'total_pages': self.page.paginator.num_pages,
            'page_number': self.page.number,
            'has_next_page': self.page.has_next(),
            'results': data,
        })

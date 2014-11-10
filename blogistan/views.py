from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from .models import Post


@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    try:
        posts = Post.get_list(update_counters=True)
    except DBAPIError as ex:
        return Response(
            'Internal Server Error: {}'.format(ex),
            content_type='text/plain',
            status_int=500,
        )

    return {'posts': posts, 'project': 'Blogistan'}


from zone import zone
from ZincError import *

from django.contrib.auth.decorators import login_required as django_login_required

def login_required(f):
   def page_func(self, request, *args, **kwargs):
       @django_login_required
       def inner(request):
           return f(self, request, *args, **kwargs)
       return inner(request)
   return page_func


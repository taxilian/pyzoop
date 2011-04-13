from django.contrib.auth.decorators import login_required as django_login_required
from django.http import Http404

def login_required(f):
   def page_func(self, request, *args, **kwargs):
       @django_login_required
       def inner(request):
           return f(self, request, *args, **kwargs)
       return inner(request)
   return page_func


class urlVars(object):
    """ This decorator should only be used on initPages """
    def __init__(self, vars=tuple(), include=tuple(), exclude=tuple("index")):
        self.vars = vars
        self.include = include
        self.exclude = exclude

    def __call__(self, f):
        vars, include, exclude = self.vars, self.include, self.exclude
        def initPages(self, request, pathList):
            print pathList
            if not pathList or (exclude and pathList and pathList[0] in exclude) or (include and pathList[0] not in include):
                return f(self, request, pathList)
            if len(pathList) >= vars:
                raise Http404
            if not hasattr(request, "zone"):
                pass
                request.zone = {}
            for v in vars:
                pass
                request.zone[v] = pathList.pop(0)
            print request.zone
            print pathList
            return f(self, request, pathList)
        return initPages


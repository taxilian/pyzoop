from django.contrib.auth.decorators import login_required as django_login_required
from django.http import Http404
from django.utils import simplejson

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
            if not pathList or (exclude and pathList and pathList[0] in exclude) or (include and pathList[0] not in include):
                return f(self, request, pathList)
            if len(pathList) >= vars:
                raise Http404
            if not hasattr(request, "zone"):
                pass
                request.zoneVar = {}
            for v in vars:
                pass
                request.zoneVar[v] = pathList.pop(0)
            return f(self, request, pathList)
        return initPages

class extractVar(object):
    def __init__(self, count=1):
        self.count = count

    def __call__(self, f):
        count = self.count
        def page_handler(self, request, pathList):
            if count > len(pathList):
                raise Http404
            pathList = pathList[:]
            pathArgs = pathList[1:count+1]
            pathList[1:count+1] = []
            return f(self, request, pathList, *pathArgs)
        return page_handler

def AcceptsJSON(f):
    def page_handler(self, request, pathList):
        json_doc = simplejson.loads(request.raw_post_data)
        return f(self, request, pathList, json_doc)
    return page_handler

from abc import ABCMeta, abstractmethod
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.conf import settings
from django.http import Http404
from ZincError import *

class zone(object):
    __metaclass__ = ABCMeta
    """
    Base class for PyZoop Zones
    """
    def __init__(self, **childZones):
        # initialize any zones that were provided
        for name, obj in childZones.iteritems():
            setattr(self, "zone_%s" % name, obj)
        self.__templateVars = {}

    @property
    def templateVars(self): return self.__templateVars

    def handleRequest(self, request, path):
        if hasattr(request, "user"): self.__templateVars["user"] = request.user
        self.__templateVars["get"] = request.GET
        self.__templateVars["post"] = request.POST
        self.__templateVars["BASE_URL"] = settings.BASE_URL
        self.__templateVars["MEDIA_URL"] = settings.MEDIA_URL
        self.__templateVars["request"] = request
        if len(path) > 0:
            pathList = path.split("/")
        else:
            pathList = ["index"]

        r = self.initZone(request, path)
        if isinstance(r, HttpResponse):
            return r

        # pass the request to a subzone, if applicable
        if hasattr(self, "zone_%s" % pathList[0]):
            try:
                subZone = getattr(self, "zone_%s" % pathList[0])
                r = self.beforeSubZone(subZone, request, pathList)
                if isinstance(r, HttpResponse):
                    return r
                resp = subZone.handleRequest(request, "/".join(pathList[1:]))
                r = self.afterSubZone(subZone, resp, request, pathList)
                return r if isinstance(r, HttpResponse) else resp
            except ZincError as e:
                if settings.DEBUG:
                    raise e
                else:
                    if hasattr(self, "error"):
                        return self.error(e)
                    else:
                        return HttpResponse("An unhandled error occurred: %s" % e)

        #give initPages the chance to change the pathList if desired
        r = self.initPages(request, pathList)
        if isinstance(r, HttpResponse):
            return r

        # handle POST requests
        if request.method == "POST":
            if hasattr(self, "post_%s" % pathList[0]):
                member = getattr(self, "post_%s" % pathList[0])
            elif hasattr(self, "post_default"):
                member = self.post_default
            elif hasattr(self, "page_%s" % pathList[0]):
                member = getattr(self, "page_%s" % pathList[0])
            else:
                member = self.page_default

        elif pathList and hasattr(self, "page_%s" % pathList[0]):
            member = getattr(self, "page_%s" % pathList[0])
        else:
            member = self.page_default

        try:
            resp = member(request, pathList)
            resp2 = self.closePages(request, pathList, resp)
            if resp2:
                return resp2
            else:
                return resp
        except ZincError as e:
            if settings.DEBUG:
                raise e
            else:
                if hasattr(self, "error"):
                    return self.error(e)
                else:
                    return HttpResponse("An unhandled error occurred: %s" % e)

    @abstractmethod
    def initZone(self, request, pathList):
        pass

    def beforeSubZone(self, request, pathList, subZone):
        pass

    def afterSubZone(self, request, pathList, subZone, response):
        pass

    @abstractmethod
    def initPages(self, request, pathList):
        pass

    def closePages(self, request, pathList, response):
        pass

    def page_default(self, request, pathList):
        raise Http404

    def render_to_response(self, template, vmap=None):
        vmap = vmap or {}
        self.templateVars.update(vmap)
        return render_to_response(template, self.templateVars)

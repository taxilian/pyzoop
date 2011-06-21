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
        """
        handleRequest is called to route the request to the correct page or subzone

        path should contain all additional PATH_INFO after the "root", not including
        an initial /
        """
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
        """
        This is called when a request on this zone is made, even
        if the request is routed to a subzone
        If a HttpResponse is returned processing will end without any
        additional routing being done

        This is particularly useful for enforcing permissions or authentication
        """
        pass

    def beforeSubZone(self, request, pathList, subZone):
        """
        This is called right before the request is routed to a subzone.
        If a HttpResponse is returned processing will end without any
        additional routing being done

        This is particularly useful for enforcing permissions or authentication
        """
        pass

    def afterSubZone(self, request, pathList, subZone, response):
        """
        This is called right after the request is handled by a subzone.
        If a HttpResponse is returned it will be used insetad of the
        response returned by the subzone
        """
        pass

    @abstractmethod
    def initPages(self, request, pathList):
        """
        This is called right before the request is routed to a page (or post handler)
        on the current zone. It is not called when a request is routed to a subzone.
        If a HttpResponse is returned processing will end without any
        additional routing being done or any pages being called.

        This is particularly useful for enforcing permissions or authentication
        """
        pass

    def closePages(self, request, pathList, response):
        pass

    def page_default(self, request, pathList):
        raise Http404

    def render_to_response(self, template, vmap=None):
        vmap = vmap or {}
        self.templateVars.update(vmap)
        return render_to_response(template, self.templateVars)

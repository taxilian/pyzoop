from django.http import HttpResponse
from django.conf import settings
from ZincError import *

class zone(object):
    """
    Base class for PyZinc Zones
    """
    def __init__(self, **childZones):
        # initialize any zones that were provided
        for name, obj in childZones.iteritems():
            setattr(self, "zone_%s" % name, obj)

    def handleRequest(self, request, path):
        if len(path) > 0:
            pathList = path.split("/")
        else:
            pathList = ["index"]

        self.initZone(request, path)

        # pass the request to a subzone, if applicable
        if hasattr(self, "zone_%s" % pathList[0]):
            try:
                subZone = getattr(self, "zone_%s" % pathList[0])
                self.beforeSubZone(subZone, request, pathList)
                resp = subZone.handleRequest(request, "/".join(pathList[1:]))
                self.afterSubZone(subZone, resp, request, pathList)
                return resp
            except ZincError as e:
                if settings.DEBUG:
                    raise e
                else:
                    if hasattr(self, "error"):
                        return self.error(e)
                    else:
                        return HttpResponse("And unhandled error occured: %s" % e)

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

        elif hasattr(self, "page_%s" % pathList[0]):
            member = getattr(self, "page_%s" % pathList[0])
        else:
            member = self.page_default

        try:
            self.initPages(member, request, pathList)
            resp = member(request, pathList)
            resp2 = self.closePages(member, request, pathList, resp)
            if resp2 != None:
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
                    return HttpResponse("And unhandled error occured: %s" % e)

    def initZone(self, request, pathList):
        pass

    def beforeSubZone(self, subZone, request, pathList):
        pass

    def afterSubZone(self, subZone, resp, request, pathList):
        pass

    def initPages(self, page, request, pathList):
        pass

    def closePages(self, page, request, pathList, response):
        pass

    def page_default(self, request, pathList):
        raise ZincError("page_default not implemented by zone!")

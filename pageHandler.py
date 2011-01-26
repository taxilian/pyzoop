
def pageHandler(zone, request, path):
    if len(path) > 0:
        pathList = path.split("/")
    else:
        pathList = ["index"]

    if not hasattr(zone, "page_%s" % pathList[0]):
        pathList.insert(0, "index")

    zone.initPages(request, pathList)
    member = getattr(zone, "page_%s" % pathList[0])
    resp = member(request, pathList[1:])
    zone.closePages(request, pathList)
    return resp

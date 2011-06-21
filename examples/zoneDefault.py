from ..models import *
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import redirect
from pyzoop import zone
from pyzoop import ReturnsJSON, extractVar
from hamstudy.sendmail import sendmail
from hamstudy.zones.zoneBrowsePool import zoneBrowsePool
from hamstudy.zones.zoneStudyTest import zoneStudyTest
from hamstudy.zones.zoneStudy import zoneStudy
from hamstudy.zones.zoneQEdit import zoneQEdit
from hamstudy.zones.zoneEditor import zoneEditor
from hamstudy.zones.zoneStats import zoneStats

class zoneDefault(zone):
    def __init__(self):
        super(zoneDefault,self).__init__(browsepool=zoneBrowsePool(), studytest=zoneStudyTest(), qedit=zoneQEdit(), editor=zoneEditor(),stats=zoneStats(),study=zoneStudy())

    def initZone(self, request, pathList):
        pass

    def initPages(self, request, path):
        pass

    def error(self, message = ""):
        return {"result": False, "message": message}
    def success(self, message = "Success!"):
        return {"result": True, "message": message}

    def page_index(self, request, pathList):
        return self.page_default(request, ["index"])

    def page_projectList(self, request, pathList):
        return self.render_to_response("projectList.html", )

    def page_default(self, request, pathList):
        url = "/".join(pathList)

        page = VersionedPage.getPage(url)

        if not page:
            raise Http404()

        return self.render_to_response("default.html", {"page": page, "title": page.name, "nojs": True})

    @ReturnsJSON
    def page_isLoggedIn(self, request, pathList):
        if request.user:
            return {"result": True, "user": request.user._id.split("_")[1]}
        else:
            return {"result": False}

    def page_doLogin(self, request, pathList):
        return self.render_to_response("default/doLogin.html", {})

    def post_doLogin(self, request, pathList):
        return redirect(request.POST.get("destUrl", "/"))

    def page_doLogout(self, request, pathList):
        del request.session["auth"]
        return redirect("/")

    def page_login(self, request, pathList):
        if "user" in request.GET and "password" in request.GET:
            username, password = request.GET["user"], request.GET["password"]
            user = User.authenticate(username, password)
            request.session["auth"] = (username, password)
            request.user = user
        return self.page_isLoggedIn(request, pathList)

    def page_register(self, request, pathList):
        return self.render_to_response("default/register.html", {})

    @ReturnsJSON
    def post_register(self, request, pathList):
        cUrl = request.build_absolute_uri(reverse("hamstudy", kwargs={"path": "confirm"}));
        url = cUrl + "/confirm?username=%s&code=%s" ;

        from hamstudy.email_messages import registerMessage as msg

        fList = ("user", "email", "call", "password", "check", "first", "last")
        user, email, call, password, check, first, last = (request.POST.get(var, None) for var in fList)
        if len(user) < 4 or len(password) < 6 or check != "true" or len(first) < 1 or len(last) < 2:
            return self.error("Invalid field data")
        try:
            user = User.create(user)
        except Exception, e:
            return self.error(str(e))

        user.email = email
        user.call = call
        user.first = first
        user.last = last
        user.password = User.getPassword(password)
        user.authToken = User.generateToken("")

        url = url % (user.username, user.authToken)
        subject, msg = msg[0], msg[1] % (url, cUrl, user.authToken)
        try:
            user.save()
        except:
            return self.error("Could not save user")
        try:
            sendmail((user.email,), subject, msg)
        except:
            return self.error("Could not send email")
        return self.success()

    def page_confirm(self, request, pathList):
        return self.render_to_response("default/confirm.html", {})

    @ReturnsJSON
    def post_confirm(self, request, pathList):
        username, code = (request.POST.get(var, None) for var in ("username", "code"))

        from hamstudy.email_messages import welcomeMessage as msg

        try:
            user = User.get(User.getId(username))
        except Exception, e:
            return self.error("Invalid username or confirmation code")
        if user.authToken.upper() == code.upper():
            user.validated = True
            user.authToken = User.generateToken("")

            subject, msg = msg[0], msg[1] % request.build_absolute_uri(reverse("hamstudy", kwargs={"path": "doLogin"}));

            try:
                user.save()
            except:
                return self.error("Could not save user")
            try:
                sendmail((user.email,), subject, msg)
            except:
                return self.error("Could not send email")
            return self.success()

        return self.error("Invalid username or confirmation code")

    @extractVar(2)
    def page_questionDesc(self, request, pathList, elem, q):
        pool = QuestionPool.getPoolName(elem)
        ret = QuestionPool.getQuestionWithDesc(pool, q)
        return self.render_to_response("default/questionDesc.html", {"question": ret, "element": elem})

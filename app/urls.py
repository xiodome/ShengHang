# app/urls.py
from django.urls import path
from app.views import userManagement as user
from app.views import singerAndMusic as miusic


from django.http import HttpResponse

def home(request):
    return HttpResponse("ShengHang backend is running successfully.")



urlpatterns = [
    path("", home),
    # 用户管理模块
    path("user/register/", user.register),
    path("user/login/", user.login),
    path("user/logout/", user.logout),
    path("user/delete_account/", user.delete_account),
    path("user/change_password/", user.change_password),
    path("user/update_profile/", user.update_profile),
    path("user/follow_user/", user.follow_user),
    path("user/follow_singer/", user.follow_singer),
    path("user/<int:uid>/get_followers/", user.get_followers),
    path("user/<int:uid>/get_followings/", user.get_followings),
    path("user/<int:uid>/get_followsingers/", user.get_followsingers),
    path("user/<int:uid>/get_user_info/", user.get_user_info),

    # 歌手与音乐管理模块
    path("Administrator/singer/admin_add_singer/", miusic.admin_add_singer),
    path("Administrator/singer/admin_delete_singer/", miusic.admin_delete_singer),
    path("singer/list_singers/", miusic.list_singers),
    path("Administrator/singer/admin_add_album/", miusic.admin_add_album),
    path("Administrator/singer/admin_delete_album/", miusic.admin_delete_album),
    path("album/album_detail/", miusic.album_detail),

]


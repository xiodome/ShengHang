# app/urls.py
from django.urls import path
from app.views import userManagement as user
from app.views import singerAndMusic as miusic
from app.views import favoriteAndSonglist as favorite


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
    path("user/profile/", user.profile),
    path("user/update_profile/", user.update_profile),
    path("user/follow_user/", user.follow_user),
    path("user/follow_singer/", user.follow_singer),
    path("user/<int:uid>/get_followers/", user.get_followers),
    path("user/<int:uid>/get_followings/", user.get_followings),
    path("user/<int:uid>/get_followsingers/", user.get_followsingers),
    path("user/get_user_info/", user.get_user_info),
    path("Administrator/profile/", user.admin_profile),

    # 歌手与音乐管理模块
    path("Administrator/singer/admin_add_singer/", miusic.admin_add_singer),
    path("Administrator/singer/admin_delete_singer/", miusic.admin_delete_singer),
    path("singer/list_singers/", miusic.list_singers),
    path("singer/profile/<int:singer_id>/", miusic.singer_profile),
    path("Administrator/album/admin_add_album/", miusic.admin_add_album),
    path("Administrator/album/admin_delete_album/", miusic.admin_delete_album),
    path("album/album_detail/", miusic.album_detail),
    path("album/profile/<int:album_id>/", miusic.album_profile),
    path("Administrator/song/admin_add_song/", miusic.admin_add_song),
    path("Administrator/song/admin_delete_song/", miusic.admin_delete_song),
    path("song/song_detail/", miusic.song_detail),
    path("song/profile/<int:song_id>/", miusic.song_profile),

    # 收藏与歌单模块
    path("songlist/list_songlists/", favorite.list_songlists),
    path("songlist/create_songlist/", favorite.create_songlist),
    path("songlist/edit_songlist/<int:songlist_id>/", favorite.edit_songlist),
    path("songlist/profile/<int:songlist_id>/", favorite.songlist_profile),
    path("songlist/delete_songlist/<int:songlist_id>/", favorite.delete_songlist),
    path("songlist/<int:songlist_id>/add_song/", favorite.songlist_add_song),
    path("songlist/<int:songlist_id>/delete_song/<int:song_id>/", favorite.songlist_delete_song),
    path("songlist/sort_songlist/<int:songlist_id>/", favorite.sort_songlist),




]


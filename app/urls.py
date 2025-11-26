# app/urls.py
from django.urls import path
from app.views import userManagement as user
from app.views import singerAndMusic as miusic
from app.views import songlistAndFavorite as songlist
from app.views import comment as comment
from app.views import playHistory as ph

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

    # 收藏与歌单模块
    path("songlist/add_songlist/", songlist.add_songlist),
    path("songlist/delete_songlist/", songlist.delete_songlist),
    path("songlist/update_songlist/", songlist.update_songlist),
    path("songlist/add_song_to_songlist/", songlist.add_song_to_songlist),
    path("songlist/delete_song_from_songlist", songlist.delete_song_from_songlist),
    path("songlist/get_songlist_list", songlist.get_songlist_list),
    path("songlist/get_songlist_detail", songlist.get_songlist_detail),
    path("favorite/manage_favorite", songlist.manage_favorite),
    path("favorite/get_favorite_list", songlist.get_favorite_list),
    path("favorite/get_my_favorite_songs_stats", songlist.get_my_favorite_songs_stats),
    path("favorite/get_platform_top_favorites", songlist.get_platform_top_favorites),

    # 评论与互动模块
    path("comment/publish_comment", comment.publish_comment),
    path("comment/delete_comment", comment.delete_comment),
    path("comment/action_comment", comment.action_comment),
    path("comment/get_comments_by_target", comment.get_comments_by_target),
    path("comment/get_comment_detail", comment.get_comment_detail),
    path("comment/get_my_comments", comment.get_my_comments),
    path("comment/get_comment_stats", comment.get_comment_stats),

    # 播放记录模块
    path("playHistory/record_play", ph.record_play),
    path("playHistory/get_total_play_stats", ph.get_total_play_stats),
    path("playHistory/get_my_play_history", ph.get_my_play_history),
    path("playHistory/get_play_report", ph.get_play_report),
    path("playHistory/get_user_top_charts", ph.get_user_top_charts),

]


# app/urls.py
from django.urls import path
from app.views import user
from app.views import music
from app.views import songlist
from app.views import comment
from app.views import history

from django.http import HttpResponse

def home(request):
    return HttpResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>ShengHang Music Platform</title>
        </head>
        <body>
            <h1>ShengHang 音乐平台</h1>
            <p>后端服务运行正常</p>
            <h2>快速导航</h2>
            <ul>
                <li><a href="/user/login/">用户登录</a></li>
                <li><a href="/user/register/">用户注册</a></li>
                <li><a href="/music/">音乐中心</a></li>
            </ul>
        </body>
        </html>
    """)



urlpatterns = [
    path("", home),
    
    # ================================
    # 用户管理模块 (User Module)
    # ================================
    path("user/register/", user.register),
    path("user/login/", user.login),
    path("user/logout/", user.logout),
    path("user/delete_account/", user.delete_account),
    path("user/change_password/", user.change_password),
    path("user/profile/<int:owner_id>/", user.profile),
    path("user/update_profile/", user.update_profile),
    path("user/follow_user/", user.follow_user),
    path("user/unfollow_user/", user.unfollow_user),
    path("user/follow_singer/", user.follow_singer),
    path("user/unfollow_singer/", user.unfollow_singer),
    path("user/<int:uid>/get_followers/", user.get_followers),
    path("user/<int:uid>/get_followings/", user.get_followings),
    path("user/<int:uid>/get_followsingers/", user.get_followsingers),
    path("user/get_user_info/", user.get_user_info),
    path("Administrator/profile/", user.admin_profile),

    # ================================
    # 音乐管理模块 (Music Module)
    # ================================
    path("music/", music.music),
    path("Administrator/singer/admin_add_singer/", music.admin_add_singer),
    path("Administrator/singer/admin_delete_singer/", music.admin_delete_singer),
    path("singer/search_singer/", music.search_singer),
    path("singer/profile/<int:singer_id>/", music.singer_profile),
    path("Administrator/album/admin_add_album/", music.admin_add_album),
    path("Administrator/album/admin_delete_album/", music.admin_delete_album),
    path("album/search_album/", music.search_album),
    path("album/profile/<int:album_id>/", music.album_profile),
    path("Administrator/song/admin_add_song/", music.admin_add_song),
    path("Administrator/song/admin_delete_song/", music.admin_delete_song),
    path("song/search_song/", music.search_song),
    path("song/profile/<int:song_id>/", music.song_profile),

    # ================================
    # 歌单与收藏模块 (Songlist Module)
    # ================================
    # Songlist operations - HTML界面
    path("songlist/list_songlists/", songlist.list_songlists),
    path("songlist/create_songlist/", songlist.create_songlist),
    path("songlist/edit_songlist/<int:songlist_id>/", songlist.edit_songlist),
    path("songlist/profile/<int:songlist_id>/", songlist.songlist_profile),
    path("songlist/delete_songlist/<int:songlist_id>/", songlist.delete_songlist),
    path("songlist/<int:songlist_id>/add_song/", songlist.songlist_add_song),
    path("songlist/<int:songlist_id>/delete_song/<int:song_id>/", songlist.songlist_delete_song),
    path("songlist/sort_songlist/<int:songlist_id>/", songlist.sort_songlist),
    path("songlist/search_songlist/", songlist.search_songlist),
    path("songlist/like_songlist/<songlist_id>/", songlist.like_songlist),

    # Songlist operations - API接口
    path("songlist/add_songlist/", songlist.add_songlist),
    path("songlist/delete_songlist/", songlist.delete_songlist),
    path("songlist/update_songlist/", songlist.update_songlist),
    path("songlist/add_song_to_songlist/", songlist.add_song_to_songlist),
    path("songlist/delete_song_from_songlist", songlist.delete_song_from_songlist),
    path("songlist/get_songlist_list", songlist.get_songlist_list),
    path("songlist/get_songlist_detail", songlist.get_songlist_detail),

    # Favorite operations - HTML界面
    path("favorite/list_favorite/", songlist.list_favorite),
    path("favorite/add_favorite/", songlist.add_favorite),
    path("favorite/delete_favorite/", songlist.delete_favorite),

    # Favorite operations - API接口
    path("favorite/manage_favorite", songlist.manage_favorite),
    path("favorite/get_favorite_list", songlist.get_favorite_list),
    path("favorite/get_my_favorite_songs_stats", songlist.get_my_favorite_songs_stats),
    path("favorite/get_platform_top_favorites", songlist.get_platform_top_favorites),

    # ================================
    # 评论与互动模块 (Comment Module)
    # ================================
    # Comment operations - HTML界面
    path("comment/list_comment/", comment.list_comment),
    path("comment/add_comment/", comment.add_comment),
    path("comment/delete_comment/", comment.delete_comment),
    path("comment/like_comment/<int:comment_id>/", comment.like_comment),

    # Comment operations - API接口
    path("comment/publish_comment", comment.publish_comment),
    path("comment/action_comment", comment.action_comment),
    path("comment/get_comments_by_target", comment.get_comments_by_target),
    path("comment/get_comment_detail", comment.get_comment_detail),
    path("comment/get_my_comments", comment.get_my_comments),
    path("comment/get_comment_stats", comment.get_comment_stats),

    # ================================
    # 播放记录模块 (History Module)
    # ================================
    path("playHistory/record_play", history.record_play),
    path("playHistory/get_total_play_stats", history.get_total_play_stats),
    path("playHistory/get_my_play_history", history.get_my_play_history),
    path("playHistory/get_play_report", history.get_play_report),
    path("playHistory/get_user_top_charts", history.get_user_top_charts),
]


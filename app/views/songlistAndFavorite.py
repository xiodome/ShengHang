import json

from django.db import connection
from django.views.decorators.csrf import csrf_exempt
import json
from .tools import *

from app.views import json_cn

'''
- 向歌单添加/移除歌曲
- 查看歌单列表（支持筛选）
- 查看歌单详情（包括歌单总时长）
- 排序与筛选歌单内容（按时间、播放次数、添加事件等排序）
- 收藏/取消收藏歌曲、专辑、歌单
- 查看与管理收藏列表（支持筛选查看）（设置收藏可见性）
- 收藏的歌曲作为一个默认的歌单（统计总时长）
- 展示平台中收藏次数最多的歌曲/专辑/歌单
'''

# 检查权限
def check_user_auth(user_id, songlist_id):
    if user_id == 1:
        return True

    sql_get_user_songlists = """
          SELECT *
          FROM Songlist
          WHERE songlist_id = %s 
            AND user_id = %s
          """

    with connection.cursor() as cursor:
        cursor.execute(sql_get_user_songlists, [songlist_id, user_id])
        row = cursor.fetchone()

    # 如果 row 不是 None，说明查到了记录，即你是创建者
    return row is not None

# 创建歌单
def add_songlist(request):
    #  验证 Request 方式
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    #  获取数据
    data = json.loads(request.body)

    #  验证数据
    #  必须要有 名称 用户id
    if "song_title" in data:
        songlist_title = data.get("songlist_title")
    else:
        return json_cn({"error": "未检测到歌单名称"}, 400)

    if "user_id" in data:
        user_id = data.get("user_id")
    else:
        return json_cn({"error": "未检测到用户ID"}, 400)

    description = data.get("description", None)
    cover_url = data.get("cover_url", '/images/default_songlist_cover.jpg')
    is_public = data.get("is_public", True)

    #  SQL语句编写
    sql_add_songlist = """
        INSERT INTO songlist(songlist_title, user_id, description, cover_url, is_public)
        VALUES(%s, %s, %s, %s, %s)
    """

    #  执行SQL语句
    with connection.cursor() as cursor:
        cursor.execute(sql_add_songlist, [
            songlist_title, user_id, description, cover_url, is_public
            ])

    return json_cn({"message": "歌单已添加"})


# 删除歌单
def delete_songlist(request):
    #  验证 Request 方式
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    #  获取数据
    data = json.loads(request.body)

    #  验证数据
    #  必须要有 用户id 与 歌单id
    if "songlist_id" in data:
        songlist_id = data.get("songlist_id")
    else:
        return json_cn({"error": "未检测到歌单ID"}, 400)

    if not check_user_auth(current_user_id, songlist_id):
        return json_cn({"error": "无权修改此歌单（并非创建者）"}, 403)

    #  SQL语句编写
    sql_delete_songlist = """
                       DELETE FROM Songlist 
                       WHERE songlist_id = %s AND user_id = %s
                       """

    sql_delete_songlist_song = """
                       DELETE FROM Songlist_Song 
                       WHERE songlist_id = %s
                       """

    #  执行SQL语句
    with connection.cursor() as cursor:
        cursor.execute(sql_delete_songlist_song, [
            songlist_id
        ])
        cursor.execute(sql_delete_songlist, [
            songlist_id, current_user_id
        ])

    return json_cn({"message": "歌单已删除"})

# 修改歌单 包括 songlist_title description is_public
def update_songlist(request):
    #  验证 Request 方式
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)

    #  获取数据
    data = json.loads(request.body)

    #  验证数据
    #  必须要有 用户id 与 歌单id
    if "songlist_id" in data:
        songlist_id = data.get("songlist_id")
    else:
        return json_cn({"error": "未检测到歌单ID"}, 400)

    if not check_user_auth(current_user_id, songlist_id):
        return json_cn({"error": "无权修改此歌单（并非创建者）"}, 403)

    if "songlist_title" in data:
        songlist_title = data.get("songlist_title")
        sql_update_songlist_title = """
                              UPDATE Songlist
                              SET songlist_title = %s 
                              WHERE songlist_id = %s 
                                AND user_id = %s 
                              """
        with connection.cursor() as cursor:
            cursor.execute(sql_update_songlist_title, [
                songlist_title, songlist_id, current_user_id
            ])

    if "description" in data:
        description = data.get("description")
        sql_update_songlist_description = """
                              UPDATE Songlist
                              SET description = %s 
                              WHERE songlist_id = %s 
                                AND user_id = %s 
                              """
        with connection.cursor() as cursor:
            cursor.execute(sql_update_songlist_description, [
                description, songlist_id, current_user_id
            ])

    if "is_public" in data:
        is_public = data.get("is_public")
        sql_update_songlist_public = """
                              UPDATE Songlist
                              SET is_public = %s 
                              WHERE songlist_id = %s 
                                AND user_id = %s 
                              """
        with connection.cursor() as cursor:
            cursor.execute(sql_update_songlist_public, [
                is_public, songlist_id, current_user_id
            ])

    return json_cn({"message": "歌单修改已完成"})

def add_song_to_songlist(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)

    data = json.loads(request.body)
    if "songlist_id" in data:
        songlist_id = data.get("songlist_id")
    else :
        return json_cn({"error": "未检测到歌单ID"}, 400)

    if "song_id" in data:
        song_id = data.get("song_id")
    else :
        return json_cn({"error": "未检测到歌曲ID"}, 400)

    if not check_user_auth(current_user_id, songlist_id):
        return json_cn({"error": "无权修改此歌单（并非创建者）"}, 403)

    #  SQL语句编写
    sql_add_song_to_songlist = """
                       INSERT INTO Songlist_Song(songlist_id, song_id)
                        VALUES(%s, %s)
                       """

    #  执行SQL语句
    with connection.cursor() as cursor:
        cursor.execute(sql_add_song_to_songlist, [
            songlist_id, song_id
        ])

    return json_cn({"message": "添加歌曲进歌单成功"})

# 移除歌单中的歌曲
def delete_song_from_songlist(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    data = json.loads(request.body)

    if "songlist_id" in data:
        songlist_id = data.get("songlist_id")
    else:
        return json_cn({"error": "未检测到歌单ID"}, 400)

    if "song_id" in data:
        song_id = data.get("song_id")
    else:
        return json_cn({"error": "未检测到歌曲ID"}, 400)

    # 权限检查
    if not check_user_auth(current_user_id, songlist_id):
        return json_cn({"error": "无权修改此歌单（并非创建者）"}, 403)

    # SQL: 删除关联记录
    sql_delete_song_from_songlist = """
                 DELETE \
                 FROM Songlist_Song
                 WHERE songlist_id = %s \
                   AND song_id = %s \
                 """

    with connection.cursor() as cursor:
        cursor.execute(sql_delete_song_from_songlist, [songlist_id, song_id])

    return json_cn({"message": "歌曲已从歌单移除"})


# 查看歌单列表（支持筛选：按用户、按关键词）
def get_songlist_list(request):
    if request.method != "GET":
        return json_cn({"error": "GET required"}, 400)

    data = json.loads(request.body)

    # 筛选参数
    filter_user_id = data.GET.get("filter_user_id", None)  # 筛选某用户的歌单
    keyword = data.GET.get("keyword", None)  # 搜索标题

    sql = """
          SELECT songlist_id, songlist_title, user_id, cover_url, like_count, is_public, create_time
          FROM Songlist
          WHERE 1 = 1 \
          """
    params = []

    if filter_user_id:
        sql += " AND user_id = %s"
        params.append(filter_user_id)

    # 如果不是查自己的，通常只显示公开的（根据业务逻辑调整）
    current_user = get_user_id(request)
    if filter_user_id and str(filter_user_id) != str(current_user):
        sql += " AND is_public = 1"

    if keyword:
        sql += " AND songlist_title LIKE %s"
        params.append(f"%{keyword}%")

    sql += " ORDER BY create_time DESC"

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        result = dictfetchall(cursor)

    return json_cn({"songlists": result})


# 查看歌单详情与内容（含总时长、排序）
# - 包括歌单元数据、总时长计算
# - 包括歌曲列表，支持按：添加时间(add_time)、播放次数(play_count)、歌曲时长(duration) 排序
def get_songlist_detail(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    data = json.loads(request.body)

    if "songlist_id" in data:
        songlist_id = data.get("songlist_id")
    else:
        return json_cn({"error": "未检测到歌单ID"}, 400)

    # 排序方式: 'add_time_desc', 'add_time_asc', 'play_count', 'duration'
    sort_by = data.get("sort_by", "add_time_desc")

    # 1. 获取歌单基本信息
    sql_info = """
               SELECT songlist_id, songlist_title, user_id, description, cover_url, like_count, create_time
               FROM Songlist
               WHERE songlist_id = %s \
               """

    # 2. 计算歌单总时长 (秒)
    sql_total_duration = """
                         SELECT SUM(s.duration) as total_duration
                         FROM Song s
                                  JOIN Songlist_Song ss ON s.song_id = ss.song_id
                         WHERE ss.songlist_id = %s \
                         """

    # 3. 获取歌曲列表 (关联 Song 表和 Songlist_Song 表)
    sql_songs = """
                SELECT s.song_id, s.song_title, s.duration, s.play_count, s.file_url, ss.add_time
                FROM Song s
                         JOIN Songlist_Song ss ON s.song_id = ss.song_id
                WHERE ss.songlist_id = %s \
                """

    # 处理排序
    if sort_by == 'play_count':
        sql_songs += " ORDER BY s.play_count DESC"
    elif sort_by == 'duration':
        sql_songs += " ORDER BY s.duration DESC"
    elif sort_by == 'add_time_asc':
        sql_songs += " ORDER BY ss.add_time ASC"
    else:  # 默认按添加时间倒序
        sql_songs += " ORDER BY ss.add_time DESC"

    # 执行查询
    with connection.cursor() as cursor:
        # 查信息
        cursor.execute(sql_info, [songlist_id])
        info = dictfetchall(cursor)
        if not info:
            return json_cn({"error": "歌单不存在"}, 404)
        songlist_info = info[0]

        # 查时长
        cursor.execute(sql_total_duration, [songlist_id])
        duration_row = cursor.fetchone()
        total_duration = duration_row[0] if duration_row[0] else 0
        songlist_info['total_duration'] = total_duration

        # 查歌曲
        cursor.execute(sql_songs, [songlist_id])
        songs = dictfetchall(cursor)

    return json_cn({
        "info": songlist_info,
        "songs": songs
    })


# 收藏/取消收藏 (歌曲、专辑、歌单)
def manage_favorite(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    data = json.loads(request.body)

    # action: 'add' (收藏), 'remove' (取消收藏)
    action = data.get("action")
    # target_type: 'song', 'album', 'songlist'
    target_type = data.get("target_type")
    target_id = data.get("target_id")

    if not all([action, target_type, target_id]):
        return json_cn({"error": "参数不完整"}, 400)

    if target_type not in ['song', 'album', 'songlist']:
        return json_cn({"error": "无效的收藏类型"}, 400)

    # 收藏逻辑
    if action == "add":
        # 1. 查重
        sql_check = "SELECT favorite_id FROM Favorite WHERE user_id=%s AND target_type=%s AND target_id=%s"
        with connection.cursor() as cursor:
            cursor.execute(sql_check, [current_user_id, target_type, target_id])
            if cursor.fetchone():
                return json_cn({"error": "已收藏，请勿重复操作"}, 400)

            # 2. 插入
            sql_insert = "INSERT INTO Favorite (user_id, target_type, target_id) VALUES (%s, %s, %s)"
            cursor.execute(sql_insert, [current_user_id, target_type, target_id])

        return json_cn({"message": "收藏成功"})

    # 取消收藏逻辑
    elif action == "remove":
        sql_delete = "DELETE FROM Favorite WHERE user_id=%s AND target_type=%s AND target_id=%s"
        with connection.cursor() as cursor:
            cursor.execute(sql_delete, [current_user_id, target_type, target_id])
        return json_cn({"message": "已取消收藏"})

    return json_cn({"error": "无效操作"}, 400)

# 查看收藏列表 (支持筛选查看)
def get_favorite_list(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    data = json.loads(request.body)

    # target_type: 必须指定查哪种类型的收藏，例如 'song'
    if "target_type" in data :
        target_type = data.get("target_type")
    else:
        json_cn({"error": "没有指定查询类型"}, 400)

    # 根据类型关联不同的表来获取名称
    if target_type == 'song':
        sql = """
              SELECT f.favorite_id, f.favorite_time, f.target_id, s.song_title as name, s.file_url
              FROM Favorite f
                       JOIN Song s ON f.target_id = s.song_id
              WHERE f.user_id = %s \
                AND f.target_type = 'song'
              ORDER BY f.favorite_time DESC \
              """
    elif target_type == 'album':
        sql = """
              SELECT f.favorite_id, f.favorite_time, f.target_id, a.album_title as name, a.cover_url
              FROM Favorite f
                       JOIN Album a ON f.target_id = a.album_id
              WHERE f.user_id = %s \
                AND f.target_type = 'album'
              ORDER BY f.favorite_time DESC \
              """
    elif target_type == 'songlist':
        sql = """
              SELECT f.favorite_id, f.favorite_time, f.target_id, sl.songlist_title as name, sl.cover_url
              FROM Favorite f
                       JOIN Songlist sl ON f.target_id = sl.songlist_id
              WHERE f.user_id = %s \
                AND f.target_type = 'songlist'
              ORDER BY f.favorite_time DESC \
              """
    else:
        return json_cn({"error": "未知的target_type"}, 400)

    with connection.cursor() as cursor:
        cursor.execute(sql, [current_user_id])
        result = dictfetchall(cursor)

    return json_cn({"favorites": result, "type": target_type})


# "我收藏的歌曲" (默认歌单模式，统计总时长)
def get_my_favorite_songs_stats(request):
    """
    将用户收藏的歌曲视为一个“默认歌单”，返回列表和总时长
    """
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)

    # 1. 计算收藏歌曲总时长
    sql_duration = """
                   SELECT SUM(s.duration)
                   FROM Favorite f
                            JOIN Song s ON f.target_id = s.song_id
                   WHERE f.user_id = %s \
                     AND f.target_type = 'song' \
                   """

    # 2. 获取歌曲列表
    sql_list = """
               SELECT s.song_id, s.song_title, s.duration, s.play_count, f.favorite_time
               FROM Favorite f
                        JOIN Song s ON f.target_id = s.song_id
               WHERE f.user_id = %s \
                 AND f.target_type = 'song'
               ORDER BY f.favorite_time DESC \
               """

    with connection.cursor() as cursor:
        # 此时长
        cursor.execute(sql_duration, [current_user_id])
        duration_row = cursor.fetchone()
        total_duration = duration_row[0] if duration_row and duration_row[0] else 0

        # 歌曲列表
        cursor.execute(sql_list, [current_user_id])
        songs = dictfetchall(cursor)

    return json_cn({
        "list_name": "我收藏的歌曲",
        "total_duration": total_duration,
        "count": len(songs),
        "songs": songs
    })

# 平台排行：展示收藏次数最多的 歌曲/专辑/歌单
def get_platform_top_favorites(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    data = json.loads(request.body)
    # type: 'song', 'album', 'songlist'
    target_type = data.get("target_type", "song")
    limit = data.get("limit", 10)  # 默认取前10

    if target_type == 'song':
        sql = """
              SELECT f.target_id, COUNT(*) as fav_count, s.song_title as name
              FROM Favorite f
                       JOIN Song s ON f.target_id = s.song_id
              WHERE f.target_type = 'song'
              GROUP BY f.target_id, s.song_title
              ORDER BY fav_count DESC
                  LIMIT %s \
              """
    elif target_type == 'album':
        sql = """
              SELECT f.target_id, COUNT(*) as fav_count, a.album_title as name
              FROM Favorite f
                       JOIN Album a ON f.target_id = a.album_id
              WHERE f.target_type = 'album'
              GROUP BY f.target_id, a.album_title
              ORDER BY fav_count DESC
                  LIMIT %s \
              """
    elif target_type == 'songlist':
        sql = """
              SELECT f.target_id, COUNT(*) as fav_count, sl.songlist_title as name
              FROM Favorite f
                       JOIN Songlist sl ON f.target_id = sl.songlist_id
              WHERE f.target_type = 'songlist'
              GROUP BY f.target_id, sl.songlist_title
              ORDER BY fav_count DESC
                  LIMIT %s \
              """
    else:
        return json_cn({"error": "类型错误"}, 400)

    with connection.cursor() as cursor:
        cursor.execute(sql, [limit])
        result = dictfetchall(cursor)

    return json_cn({"ranking": result, "type": target_type})
# 评论与互动模块 (Comment and Interaction Module)
# Consolidated from comment.py and commentAndInteraction.py

import json
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .tools import *


# ================================
# Comment Management (API)
# ================================

# 发布评论 / 回复评论 (API)
@csrf_exempt
def publish_comment(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    data = json.loads(request.body)

    # 必填参数
    target_type = data.get("target_type")  # song, album, songlist
    target_id = data.get("target_id")
    content = data.get("content")

    # 选填参数 (如果是回复别人的评论，则填 parent_id)
    parent_id = data.get("parent_id", None)

    if not all([target_type, target_id, content]):
        return json_cn({"error": "参数缺失: target_type, target_id, content"}, 400)

    if target_type not in ['song', 'album', 'songlist']:
        return json_cn({"error": "无效的评论目标类型"}, 400)

    # 简单的敏感词过滤逻辑可以在这里加...
    status = '正常'

    sql = """
          INSERT INTO Comment (user_id, target_type, target_id, content, parent_id, status, like_count, comment_time)
          VALUES (%s, %s, %s, %s, %s, %s, 0, NOW())
          """

    with connection.cursor() as cursor:
        cursor.execute(sql, [current_user_id, target_type, target_id, content, parent_id, status])

    return json_cn({"message": "评论发布成功"})


# 发布评论 (HTML界面)
@csrf_exempt
def add_comment(request):
    if "user_id" not in request.session:
        return HttpResponse("""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>请先登录</title></head>
            <body>
                <h2>请先登录再进行评论</h2>
                <p><a href="/user/login/">返回登录</a></p>
            </body>
            </html>
        """, status=403)

    user_id = request.session["user_id"]

    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        target_type = data["target_type"]   # song/album/songlist
        target_id = int(data["target_id"])
        content = data["content"].strip()
        parent_id = data.get("parent_id")  # 允许为None

        if target_type not in ["song", "album", "songlist"]:
            return HttpResponse(f"""
                <!DOCTYPE html>
                <html>
                <head><meta charset="UTF-8"><title>错误</title></head>
                <body>
                    <h2>非法评论对象</h2>
                    <p><a href="/{target_type}/profile/{target_id}/">返回详情页</a></p>
                </body>
                </html>
            """)   

        if not content:
            return HttpResponse(f"""
                <!DOCTYPE html>
                <html>
                <head><meta charset="UTF-8"><title>错误</title></head>
                <body>
                    <h2>评论内容不能为空</h2>
                    <p><a href="/{target_type}/profile/{target_id}/">返回详情页</a></p>
                </body>
                </html>
            """)

        sql = """
            INSERT INTO Comment(user_id, target_type, target_id, content, parent_id, status)
            VALUES (%s, %s, %s, %s, %s, '正常');
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, [user_id, target_type, target_id, content, parent_id])

        return HttpResponse(f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>评论成功</title></head>
            <body>
                <h2>评论成功</h2>
                <p><a href="/{target_type}/profile/{target_id}/">返回详情页</a></p>
            </body>
            </html>
        """)
        
    return json_cn({"error": "POST required"}, 400)


# 删除评论 (支持删除自己的，以及歌单创建者删除自己歌单下的评论)
@csrf_exempt
def delete_comment(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    data = json.loads(request.body) if request.body else request.POST

    comment_id = data.get("comment_id")

    if not comment_id:
        return json_cn({"error": "未检测到评论ID"}, 400)

    # 1. 检查评论是否存在以及归属信息
    sql_check = """
                SELECT user_id, target_type, target_id
                FROM Comment
                WHERE comment_id = %s
                """
    with connection.cursor() as cursor:
        cursor.execute(sql_check, [comment_id])
        row = cursor.fetchone()

    if not row:
        return json_cn({"error": "评论不存在"}, 404)

    comment_owner_id, target_type, target_id = row

    can_delete = False

    # 情况A: 自己删自己的评论
    if str(comment_owner_id) == str(current_user_id):
        can_delete = True

    # 情况B: 管理自己创建的歌单下的评论
    # 如果这条评论是写在某个歌单下的(target_type='songlist')
    # 且这个歌单是当前用户创建的，那么他有权删除
    elif target_type == 'songlist':
        sql_check_songlist_owner = "SELECT 1 FROM Songlist WHERE songlist_id=%s AND user_id=%s"
        with connection.cursor() as cursor:
            cursor.execute(sql_check_songlist_owner, [target_id, current_user_id])
            if cursor.fetchone():
                can_delete = True

    if not can_delete:
        return json_cn({"error": "无权删除此评论"}, 403)

    # 执行删除
    # 级联删除
    def recursive_delete_comment(cursor, cid):
        """
        递归删除评论及其所有子评论
        """
        # 第一步：查找当前评论的所有子评论（回复）
        sql_find_children = "SELECT comment_id FROM Comment WHERE parent_id = %s"
        cursor.execute(sql_find_children, [cid])
        children = cursor.fetchall()

        # 第二步：对每一个子评论，递归调用删除
        for child in children:
            child_id = child[0]
            recursive_delete_comment(cursor, child_id)

        # 第三步：子孙都删完了，删除自己
        sql_delete_self = "DELETE FROM Comment WHERE comment_id = %s"
        cursor.execute(sql_delete_self, [cid])

    try:
        with connection.cursor() as cursor:
            # 调用递归函数
            recursive_delete_comment(cursor, comment_id)

        return json_cn({"message": "评论及其回复已成功删除"})

    except Exception as e:
        print(f"Delete Error: {e}")
        return json_cn({"error": "删除失败，数据库错误"}, 500)


# 对评论进行点赞 / 举报 (API)
@csrf_exempt
def action_comment(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)

    current_user_id = get_user_id(request)
    data = json.loads(request.body)

    comment_id = data.get("comment_id")
    action = data.get("action")  # 'like', 'report'

    if not comment_id or not action:
        return json_cn({"error": "参数缺失"}, 400)

    if action == 'like':
        # 只能直接增加计数
        sql = "UPDATE Comment SET like_count = like_count + 1 WHERE comment_id = %s"
        with connection.cursor() as cursor:
            cursor.execute(sql, [comment_id])
        return json_cn({"message": "点赞成功"})

    elif action == 'report':
        # 举报：将状态改为 '举报中'
        sql = "UPDATE Comment SET status = '举报中' WHERE comment_id = %s"
        with connection.cursor() as cursor:
            cursor.execute(sql, [comment_id])
        return json_cn({"message": "举报成功，等待管理员审核"})

    else:
        return json_cn({"error": "无效操作"}, 400)


# 点赞评论 (HTML界面)
@csrf_exempt
def like_comment(request, comment_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        type = data.get("type")
        id = data.get("id")

        sql = """
            UPDATE Comment
            SET like_count = like_count + 1
            WHERE comment_id = %s;
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, [comment_id])

        return HttpResponse(f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>点赞成功</title></head>
            <body>
                <h2>点赞成功！</h2>
                <p><a href="/{type}/profile/{id}/">返回详情页</a></p>
            </body>
            </html>
        """)
    
    return json_cn({"error": "POST required"}, 400)


# 查看歌曲/专辑/歌单的评论列表 (GET)
# 支持按热度(like_count)或时间(comment_time)排序
def get_comments_by_target(request):
    if request.method != "GET":
        return json_cn({"error": "GET required"}, 400)

    # GET请求从 query_params 获取
    target_type = request.GET.get("target_type")
    target_id = request.GET.get("target_id")
    sort_by = request.GET.get("sort_by", "time")  # 'time' or 'hot'

    if not target_type or not target_id:
        return json_cn({"error": "参数缺失"}, 400)

    # SQL: 关联 User 表以获取用户名，只获取一级评论 (parent_id IS NULL)
    # 子评论(回复)通常在详情里看，或者另外获取
    sql = """
          SELECT c.comment_id,
                 c.content,
                 c.like_count,
                 c.comment_time,
                 c.user_id,
                 u.user_name,
                 u.profile
          FROM Comment c
                   JOIN User u ON c.user_id = u.user_id
          WHERE c.target_type = %s
            AND c.target_id = %s
            AND c.parent_id IS NULL
            AND c.status = '正常'
          """

    if sort_by == 'hot':
        sql += " ORDER BY c.like_count DESC, c.comment_time DESC"
    else:
        sql += " ORDER BY c.comment_time DESC"

    with connection.cursor() as cursor:
        cursor.execute(sql, [target_type, target_id])
        comments = dictfetchall(cursor)

    return json_cn({"comments": comments, "count": len(comments)})


# 查看单条评论及其回复
def get_comment_detail(request):
    if request.method != "GET":
        return json_cn({"error": "GET required"}, 400)

    comment_id = request.GET.get("comment_id")
    if not comment_id:
        return json_cn({"error": "未检测到评论ID"}, 400)

    with connection.cursor() as cursor:
        # 1. 获取主评论信息
        sql_main = """
                   SELECT c.comment_id,
                          c.content,
                          c.like_count,
                          c.comment_time,
                          c.user_id,
                          u.user_name,
                          c.target_type,
                          c.target_id
                   FROM Comment c
                            JOIN User u ON c.user_id = u.user_id
                   WHERE c.comment_id = %s
                   """
        cursor.execute(sql_main, [comment_id])
        main_rows = dictfetchall(cursor)

        if not main_rows:
            return json_cn({"error": "评论不存在或已删除"}, 404)
        main_comment = main_rows[0]

        # 2. 获取该评论下的回复 (parent_id = comment_id)
        sql_replies = """
                      SELECT c.comment_id,
                             c.content,
                             c.like_count,
                             c.comment_time,
                             c.user_id,
                             u.user_name
                      FROM Comment c
                               JOIN User u ON c.user_id = u.user_id
                      WHERE c.parent_id = %s
                        AND c.status = '正常'
                      ORDER BY c.comment_time ASC
                      """
        cursor.execute(sql_replies, [comment_id])
        replies = dictfetchall(cursor)

    return json_cn({
        "comment": main_comment,
        "replies": replies
    })


# 查看自己发布的评论 (API)
def get_my_comments(request):
    if request.method != "GET":
        return json_cn({"error": "GET required"}, 400)

    # 登录验证需要 session，GET请求也能读 session
    current_user_id = request.session.get("user_id")
    if not current_user_id:
        return json_cn({"error": "请先登录"}, 401)

    sql = """
          SELECT comment_id, target_type, target_id, content, like_count, comment_time, status
          FROM Comment
          WHERE user_id = %s
          ORDER BY comment_time DESC
          """

    with connection.cursor() as cursor:
        cursor.execute(sql, [current_user_id])
        comments = dictfetchall(cursor)

    return json_cn({"my_comments": comments})


# 查看自己发布的评论 (HTML界面)
@csrf_exempt
def list_comment(request):
    if "user_id" not in request.session:
        return HttpResponse("""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>请先登录</title></head>
            <body>
                <h2>请先登录再查看评论</h2>
                <p><a href="/user/login/">返回登录</a></p>
            </body>
            </html>
        """, status=403)

    uid = request.session["user_id"]

    # 获取歌曲的评论
    sql_song = """
        SELECT 
            s.song_id,
            c.comment_id,
            c.content,
            c.like_count,
            c.comment_time
        FROM Comment c
        JOIN Song s ON s.song_id = c.target_id 
        WHERE c.user_id = %s AND c.target_type = 'song'
        ORDER BY c.comment_time DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_song, [uid])
        songs = cursor.fetchall()

    song_count = len(songs)

    # 获取专辑的评论
    sql_album = """
        SELECT 
            a.album_id,
            c.comment_id,
            c.content,
            c.like_count,
            c.comment_time
        FROM Comment c
        JOIN Album a ON a.album_id = c.target_id
        WHERE c.user_id = %s AND c.target_type = 'album'
        ORDER BY c.comment_time DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_album, [uid])
        albums = cursor.fetchall()

    album_count = len(albums)

    # 获取收藏的歌单
    sql_songlist = """
        SELECT 
            sl.songlist_id,
            c.comment_id,
            c.content,
            c.like_count,
            c.comment_time
        FROM Comment c
        JOIN Songlist sl ON sl.songlist_id = c.target_id
        WHERE c.user_id = %s AND c.target_type = 'songlist'
        ORDER BY c.comment_time DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_songlist, [uid])
        songlists = cursor.fetchall()

    songlist_count = len(songlists)

    # ---------- 歌曲评论 ----------
    html_songs = f"""
        <h2>歌曲的评论（{song_count} 条）</h2>
        <ul>
    """
    if song_count == 0:
        html_songs += "<p>暂无歌曲评论。</p>"
    else:
        for song_id, comment_id, content, like_count, comment_time in songs:
            html_songs += f"""
                <li>
                    内容：<strong>{content}</strong>
                    <p>点赞数：{like_count}<p>
                    <p>评论时间：{comment_time.strftime("%Y-%m-%d %H:%M")}</p>

                    <a href="/song/profile/{song_id}/">查看详情</a>
        
                    <form action="/comment/delete_comment/" method="post">
                    <input type="hidden" name="target_type" value="song">
                    <input type="hidden" name="target_id" value="{song_id}">
                    <button type="submit">删除评论</button>
                </form>

                </li>
            """
    html_songs += "</ul><hr>"

    # ---------- 专辑评论 ----------
    html_albums = f"""
        <h2>专辑的评论（{album_count} 条）</h2>
        <ul>
    """
    if album_count == 0:
        html_albums += "<p>暂无专辑评论。</p>"
    else:
        for album_id, comment_id, content, like_count, comment_time in albums:
            html_albums += f"""
                <li>
                    内容：<strong>{content}</strong>
                    <p>点赞数：{like_count}<p>
                    <p>评论时间：{comment_time.strftime("%Y-%m-%d %H:%M")}</p>

                    <a href="/album/profile/{album_id}/">查看详情</a>

                    <form action="/comment/delete_comment/" method="post">
                    <input type="hidden" name="target_type" value="album">
                    <input type="hidden" name="target_id" value="{album_id}">
                    <button type="submit">删除评论</button>
                </form>

                </li>
            """
    html_albums += "</ul><hr>"

    # ---------- 歌单评论 ----------
    html_songlists = f"""
        <h2>歌单的评论（{songlist_count} 个）</h2>
        <ul>
    """
    if songlist_count == 0:
        html_songlists += "<p>暂无收藏歌单。</p>"
    else:
        for songlist_id, comment_id, content, like_count, comment_time in songlists:
            html_songlists += f"""
                <li>
                    内容：<strong>{content}</strong>
                    <p>点赞数：{like_count}<p>
                    <p>评论时间：{comment_time.strftime("%Y-%m-%d %H:%M")}</p>

                    <a href="/songlist/profile/{songlist_id}/">查看详情</a>

                    <form action="/comment/delete_comment/" method="post">
                    <input type="hidden" name="target_type" value="songlist">
                    <input type="hidden" name="target_id" value="{songlist_id}">
                    <button type="submit">删除评论</button>
                </form>

                </li>
            """
    html_songlists += "</ul><hr>"

    # ---------- 总输出 ----------
    return HttpResponse(f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>我的评论</title></head>
        <body>
            <h1>我的评论</h1>
            {html_songs}
            {html_albums}
            {html_songlists}

            <p><a href="/user/profile/{uid}">返回个人中心</a></p>
        </body>
        </html>
    """)


# 评论统计信息 (GET)
# 显示某对象的总评论数、最热评论
def get_comment_stats(request):
    if request.method != "GET":
        return json_cn({"error": "GET required"}, 400)

    target_type = request.GET.get("target_type")
    target_id = request.GET.get("target_id")

    if not target_type or not target_id:
        return json_cn({"error": "参数缺失"}, 400)

    with connection.cursor() as cursor:
        # 1. 统计总数
        sql_count = """
                    SELECT COUNT(*)
                    FROM Comment
                    WHERE target_type = %s
                      AND target_id = %s
                      AND status = '正常'
                    """
        cursor.execute(sql_count, [target_type, target_id])
        total_count = cursor.fetchone()[0]

        # 2. 获取最热的一条评论 (Hot Comment)
        sql_hot = """
                  SELECT c.comment_id, c.content, c.like_count, u.user_name
                  FROM Comment c
                           JOIN User u ON c.user_id = u.user_id
                  WHERE c.target_type = %s
                    AND c.target_id = %s
                    AND c.status = '正常'
                  ORDER BY c.like_count DESC LIMIT 1
                  """
        cursor.execute(sql_hot, [target_type, target_id])
        hot_rows = dictfetchall(cursor)
        hot_comment = hot_rows[0] if hot_rows else None

    return json_cn({
        "target_type": target_type,
        "target_id": target_id,
        "total_comments": total_count,
        "hot_comment": hot_comment
    })

# 评论与互动模块
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.http import HttpResponse
import json
from .tools import *


# ================================
# 1.发布评论（含回复）
# ================================
@csrf_exempt
def add_comment(request):
    # --------------------------
    # 1. 检验登录
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h2>请先登录再进行评论</h2>
            <p><a href="/user/login/">返回登录</a></p>
        """, status=403)

    user_id = request.session["user_id"]


    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        # --------------------------
        # 2. 获取数据并验证
        # --------------------------
        target_type = data["target_type"]   # song/album/songlist
        target_id = int(data["target_id"])
        content = data["content"].strip()
        parent_id = data.get("parent_id")  # 允许为None

        if target_type not in ["song", "album", "songlist"] :
            return HttpResponse(f"""
                <h2>非法评论对象</h2>
                <p><a href="/{target_type}/profile/{target_id}/">返回详情页</a></p>
            """)   

        if not content:
            return HttpResponse(f"""
                <h2>评论内容不能为空</h2>
                <p><a href="/{target_type}/profile/{target_id}/">返回详情页</a></p>
            """)

        # --------------------------
        # 3. 插入评论
        # --------------------------
        sql = """
            INSERT INTO Comment(user_id, target_type, target_id, content, parent_id, status)
            VALUES (%s, %s, %s, %s, %s, '正常');
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, [user_id, target_type, target_id, content, parent_id])
            cursor.fetchone()

        return HttpResponse(f"""
                <h2>评论成功</h2>
                <p><a href="/{target_type}/profile/{target_id}/">返回详情页</a></p>
            """)

        
    return json_cn({"error": "POST required"}, 400)



# ================================
# 2.删除自己的评论
# ================================
@csrf_exempt
def delete_comment(request):
    # --------------------------
    # 1. 检验登录
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h2>请先登录再进行操作</h2>
            <p><a href="/user/login/">返回登录</a></p>
        """, status=403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 获取数据
    # --------------------------
    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    target_type = data.get("target_type")
    target_id = data.get("target_id")

    if target_type not in ["song", "album", "songlist"] :
        return HttpResponse(f"""
            <h2>非法的评论类型！</h2>
            <p><a href="/comment/list_comment/">返回个人评论页</a></p>
        """)

    # --------------------------
    # 3. 检查是否已收藏
    # --------------------------
    sql_check = f"""
        SELECT 1
        FROM Comment
        WHERE user_id = %s AND target_type = %s AND target_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_check, [uid, target_type, target_id])
        exists = cursor.fetchone()

    if not exists:
        return HttpResponse(f"""
            <h2>未评论不能取消</h2>
            <p><a href="/comment/list_comment/">返回个人评论页</a></p>
        """)

    # --------------------------
    # 4. 删除收藏记录
    # --------------------------
    sql_insert = f"""
        DELETE FROM Comment
        WHERE user_id = %s AND target_type = %s AND target_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_insert, [uid, target_type, target_id])

    # --------------------------
    # 5. 返回成功页面
    # --------------------------
    return HttpResponse(f"""
        <h2>删除评论成功！</h2>
        <p><a href="/comment/list_comment/">返回个人评论页</a></p>
    """)




# ==========================
# 3. 个人评论
# ==========================
# http://127.0.0.1:8000/comment/list_comment
@csrf_exempt
def list_comment(request):
    # --------------------------
    # 1. 必须登录
    # --------------------------
    if "user_id" not in request.session:
        return HttpResponse("""
            <h2>请先登录再查看评论</h2>
            <p><a href="/user/login/">返回登录</a></p>
        """, status=403)

    uid = request.session["user_id"]

    # --------------------------
    # 2. 获取歌曲的评论
    # --------------------------
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


    # --------------------------
    # 3. 获取专辑的评论
    # --------------------------
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

    # --------------------------
    # 4. 获取收藏的歌单
    # --------------------------
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

    # --------------------------
    # 5. 生成 HTML
    # --------------------------

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
                    <input type="hidden" name="target_id" value="{ song_id }">
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
                    <input type="hidden" name="target_id" value="{ album_id }">
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
                    <input type="hidden" name="target_id" value="{ songlist_id }">
                    <button type="submit">删除评论</button>
                </form>

                </li>
            """
    html_songlists += "</ul><hr>"

    # ---------- 总输出 ----------
    return HttpResponse(f"""
        <h1>我的评论</h1>
        {html_songs}
        {html_albums}
        {html_songlists}

        <p><a href="/user/profile/{uid}">返回个人中心</a></p>
    """)



# ================================
# 4.点赞评论
# ================================
# /comment/like_comment/<comment_id>/
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
            <h2>点赞成功！</h2>
            <p><a href="/{type}/profile/{id}/">返回详情页</a></p>
        """)
    
    return json_cn({"error": "POST required"}, 400)
    

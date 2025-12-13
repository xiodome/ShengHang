# ShengHang 音乐平台

一个基于 Django 的音乐流媒体平台，提供歌曲、专辑、歌单、评论等完整功能。

## 项目状态

✅ **模块重构完成** - 已将重复模块合并为 5 个核心模块  
✅ **前后端分离** - 同时提供 HTML 界面和 JSON API  
✅ **代码优化** - 代码量减少 29.3%

## 模块结构

### 核心功能模块 (5个)

1. **user.py** - 用户管理
   - 注册、登录、资料管理
   - 关注用户和歌手
   - 管理员功能

2. **music.py** - 音乐内容管理
   - 歌手、专辑、歌曲的管理
   - 搜索和浏览功能

3. **songlist.py** - 歌单与收藏
   - 歌单创建和管理
   - 收藏功能（歌曲、专辑、歌单）
   - 热门排行

4. **comment.py** - 评论与互动
   - 发布评论和回复
   - 点赞和举报
   - 评论统计

5. **history.py** - 播放记录
   - 播放历史跟踪
   - 播放统计
   - 个人榜单

### 工具模块 (2个)

- **tools.py** - 工具函数
- **initialTable.py** - 数据库初始化

## 技术特点

### 前后端分离
- **HTML 界面**: 传统网页访问，适合浏览器用户
- **JSON API**: RESTful 接口，适合前端框架和移动应用

### 双接口示例

```python
# HTML 界面
GET  /user/login/          → 登录页面
POST /user/login/          → 处理登录并返回页面

# JSON API
POST /user/login/          → {"message": "登录成功", "user_id": 123}
GET  /user/get_user_info/  → {"user": {...}}
```

## 快速开始

### 安装依赖
```bash
pip install django pymysql
```

### 运行服务器
```bash
python manage.py runserver
```

### 访问应用
- 主页: http://localhost:8000/
- 登录: http://localhost:8000/user/login/
- 注册: http://localhost:8000/user/register/

## API 使用

### JavaScript 示例
```javascript
// 登录
fetch('/user/login/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        username: 'test',
        password: '123456'
    })
})
.then(response => response.json())
.then(data => console.log(data));

// 获取歌单列表
fetch('/songlist/get_songlist_list?filter_user_id=1')
.then(response => response.json())
.then(data => console.log(data.songlists));
```

## 文档

详细文档请参阅：

- **MODULE_CONSOLIDATION.md** - 模块合并指南
- **CONSOLIDATION_SUMMARY.md** - 变更总结
- **FRONTEND_BACKEND_SEPARATION.md** - API 使用指南
- **COMPLETION_REPORT.md** - 项目完成报告

## 项目统计

- **代码行数**: 4,427 行 (优化后)
- **模块数量**: 5 个核心模块
- **代码减少**: 29.3%
- **功能保留**: 100%

## 技术栈

- **后端**: Django 5.x
- **数据库**: MySQL (通过 PyMySQL)
- **前端**: HTML5 + 原生 JavaScript
- **API**: RESTful JSON

## 许可证

本项目用于数据库课程设计。

---

**最后更新**: 2025年12月

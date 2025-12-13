# Frontend-Backend Separation Guide

## Overview

The ShengHang music platform now implements a clean frontend-backend separation architecture. Each module provides both **HTML web interfaces** and **JSON REST APIs**.

## Architecture Pattern

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                         │
├─────────────────────────────────────────────────────────┤
│  Web Browser          │        Frontend Apps            │
│  (HTML Interface)     │     (React/Vue/Mobile)          │
└──────────┬────────────┴──────────────┬─────────────────┘
           │                           │
           │ HTTP/HTML                 │ HTTP/JSON
           │                           │
┌──────────▼───────────────────────────▼─────────────────┐
│              Django URL Router                          │
│                 (app/urls.py)                           │
└──────────┬───────────────────────────┬─────────────────┘
           │                           │
           │ HTML Views                │ API Views
           │                           │
┌──────────▼────────────┐    ┌─────────▼────────────────┐
│   HTML Functions      │    │   API Functions          │
│   Returns HTML pages  │    │   Returns JSON data      │
└───────────────────────┘    └──────────────────────────┘
```

## Two Access Patterns

### 1. HTML Web Interface
**For**: Direct browser access, traditional web users

**Characteristics**:
- Returns complete HTML pages
- Uses forms for data submission
- Server-side rendering
- Session-based authentication

**Example**:
```python
@csrf_exempt
def create_songlist(request):
    if request.method == "GET":
        # Return HTML form
        return HttpResponse("""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>Create Playlist</title></head>
            <body>
                <h2>Create New Playlist</h2>
                <form method="POST">
                    <input name="songlist_title" required><br>
                    <textarea name="description"></textarea><br>
                    <button type="submit">Create</button>
                </form>
            </body>
            </html>
        """)
    
    if request.method == "POST":
        # Process form data from request.POST
        # Return success/error HTML page
```

### 2. JSON REST API
**For**: Frontend frameworks (React, Vue, Angular), mobile apps, third-party integrations

**Characteristics**:
- Returns JSON data
- RESTful design principles
- Token or session-based auth
- Machine-readable responses

**Example**:
```python
@csrf_exempt
def add_songlist(request):
    if request.method != "POST":
        return json_cn({"error": "POST required"}, 400)
    
    data = json.loads(request.body)
    # Process JSON data
    return json_cn({"message": "Playlist created", "id": songlist_id})
```

## URL Patterns

### HTML Interfaces
```
Pattern: /module/action/
Method: GET (view) / POST (submit)
Returns: HTML pages

Examples:
  GET  /user/login/              → Login form page
  POST /user/login/              → Process login, return result page
  GET  /songlist/list_songlists/ → Display user's playlists
  GET  /comment/list_comment/    → Display user's comments
```

### API Endpoints
```
Pattern: /module/api_action
Method: Specified in docs (usually POST for actions, GET for queries)
Returns: JSON responses

Examples:
  POST /user/login/              → {"message": "Login successful"}
  POST /songlist/add_songlist/   → {"message": "Playlist created"}
  GET  /comment/get_comments_by_target → {"comments": [...]}
```

## Request/Response Examples

### HTML Interface Example

**Request** (Browser):
```http
GET /user/login/ HTTP/1.1
Host: localhost:8000
```

**Response**:
```html
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Login</title></head>
<body>
    <h2>User Login</h2>
    <form method="POST">
        <input name="username" required><br>
        <input name="password" type="password" required><br>
        <button type="submit">Login</button>
    </form>
</body>
</html>
```

### API Example

**Request** (JavaScript/App):
```http
POST /user/login/ HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
    "username": "test_user",
    "password": "password123"
}
```

**Response**:
```json
{
    "message": "Login successful",
    "user_id": 123
}
```

## Using the API with JavaScript

### Fetch API Example
```javascript
// Login
async function login(username, password) {
    const response = await fetch('/user/login/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({username, password})
    });
    
    const data = await response.json();
    if (response.ok) {
        console.log('Logged in:', data.user_id);
    } else {
        console.error('Error:', data.error);
    }
}

// Get playlists
async function getPlaylists(userId) {
    const response = await fetch(`/songlist/get_songlist_list?filter_user_id=${userId}`);
    const data = await response.json();
    return data.songlists;
}

// Create playlist
async function createPlaylist(title, description) {
    const response = await fetch('/songlist/add_songlist/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            songlist_title: title,
            description: description,
            is_public: true
        })
    });
    
    return await response.json();
}

// Add comment
async function addComment(targetType, targetId, content) {
    const response = await fetch('/comment/publish_comment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            target_type: targetType,
            target_id: targetId,
            content: content
        })
    });
    
    return await response.json();
}
```

### Axios Example
```javascript
import axios from 'axios';

// Configure base settings
axios.defaults.baseURL = 'http://localhost:8000';
axios.defaults.headers.post['Content-Type'] = 'application/json';

// Login
const login = async (username, password) => {
    try {
        const response = await axios.post('/user/login/', {
            username,
            password
        });
        return response.data;
    } catch (error) {
        console.error('Login failed:', error.response.data);
        throw error;
    }
};

// Get comments
const getComments = async (targetType, targetId, sortBy = 'time') => {
    try {
        const response = await axios.get('/comment/get_comments_by_target', {
            params: {
                target_type: targetType,
                target_id: targetId,
                sort_by: sortBy
            }
        });
        return response.data.comments;
    } catch (error) {
        console.error('Failed to get comments:', error);
        throw error;
    }
};
```

## Module API Reference

### User Module (user.py)

#### HTML Interfaces
- `GET  /user/register/` - Registration form
- `POST /user/register/` - Submit registration
- `GET  /user/login/` - Login form
- `POST /user/login/` - Submit login
- `GET  /user/profile/<id>/` - View user profile

#### API Endpoints
- `POST /user/logout/` - Logout user
- `POST /user/change_password/` - Change password
- `POST /user/follow_user/` - Follow another user
- `POST /user/unfollow_user/` - Unfollow user
- `GET  /user/get_user_info/` - Get user information
- `GET  /user/<uid>/get_followers/` - Get user's followers
- `GET  /user/<uid>/get_followings/` - Get user's followings

### Songlist Module (songlist.py)

#### HTML Interfaces
- `GET  /songlist/list_songlists/` - View my playlists
- `GET  /songlist/create_songlist/` - Create playlist form
- `POST /songlist/create_songlist/` - Submit new playlist
- `GET  /songlist/profile/<id>/` - View playlist details
- `GET  /favorite/list_favorite/` - View my favorites

#### API Endpoints
- `POST /songlist/add_songlist/` - Create playlist
- `POST /songlist/update_songlist/` - Update playlist
- `POST /songlist/delete_songlist/` - Delete playlist
- `POST /songlist/add_song_to_songlist/` - Add song to playlist
- `POST /songlist/delete_song_from_songlist` - Remove song
- `GET  /songlist/get_songlist_list` - Get playlists
- `POST /songlist/get_songlist_detail` - Get playlist details
- `POST /favorite/manage_favorite` - Add/remove favorite
- `POST /favorite/get_favorite_list` - Get favorites list

### Comment Module (comment.py)

#### HTML Interfaces
- `GET  /comment/list_comment/` - View my comments
- `POST /comment/add_comment/` - Submit comment
- `POST /comment/like_comment/<id>/` - Like a comment

#### API Endpoints
- `POST /comment/publish_comment` - Publish comment/reply
- `POST /comment/delete_comment` - Delete comment
- `POST /comment/action_comment` - Like/report comment
- `GET  /comment/get_comments_by_target` - Get comments list
- `GET  /comment/get_comment_detail` - Get comment with replies
- `GET  /comment/get_my_comments` - Get my comments
- `GET  /comment/get_comment_stats` - Get comment statistics

### History Module (history.py)

#### API Endpoints
- `POST /playHistory/record_play` - Record play
- `GET  /playHistory/get_total_play_stats` - Get play stats
- `POST /playHistory/get_my_play_history` - Get my history
- `POST /playHistory/get_play_report` - Get play report
- `POST /playHistory/get_user_top_charts` - Get top charts

## Best Practices

### For Frontend Developers

1. **Use the API endpoints** for modern frontend frameworks
2. **Handle errors gracefully** - check response status codes
3. **Store session/token** appropriately
4. **Validate input** on client side before sending
5. **Show loading states** during API calls

### For Backend Developers

1. **Keep both interfaces in sync** - same functionality in HTML and API
2. **Use consistent error messages** across modules
3. **Return appropriate HTTP status codes**:
   - 200: Success
   - 400: Bad request (missing/invalid params)
   - 401: Unauthorized (not logged in)
   - 403: Forbidden (no permission)
   - 404: Not found
   - 500: Server error

4. **Document API changes** in commit messages
5. **Test both interfaces** when adding features

### Error Response Format

**Consistent JSON error format**:
```json
{
    "error": "Error message in Chinese or English"
}
```

**HTML error pages should be user-friendly**:
```html
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Error</title></head>
<body>
    <h2>Error Message</h2>
    <p>Detailed explanation</p>
    <p><a href="/back/">Go Back</a></p>
</body>
</html>
```

## Testing Your Implementation

### Testing HTML Interface
```bash
# Use curl to test HTML endpoints
curl http://localhost:8000/user/login/

# Or just open in browser
open http://localhost:8000/user/login/
```

### Testing API Endpoints
```bash
# Login
curl -X POST http://localhost:8000/user/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'

# Get playlists
curl http://localhost:8000/songlist/get_songlist_list?filter_user_id=1

# Create playlist
curl -X POST http://localhost:8000/songlist/add_songlist/ \
  -H "Content-Type: application/json" \
  -d '{"songlist_title":"My Playlist","description":"Test"}'
```

## Security Considerations

1. **CSRF Protection**: HTML forms use Django's CSRF middleware, APIs use `@csrf_exempt`
2. **Session Management**: HTML interfaces use Django sessions
3. **Input Validation**: Always validate and sanitize input data
4. **SQL Injection**: Use parameterized queries (already implemented)
5. **XSS Prevention**: Escape user content in HTML pages

## Future Enhancements

1. **API Versioning**: `/api/v1/...`, `/api/v2/...`
2. **JWT Authentication**: For stateless API authentication
3. **Rate Limiting**: Prevent API abuse
4. **API Documentation**: Swagger/OpenAPI integration
5. **GraphQL**: Alternative to REST for complex queries
6. **WebSocket**: For real-time features (notifications, live updates)

## Summary

The frontend-backend separation provides:
- ✅ **Flexibility**: Support multiple client types
- ✅ **Scalability**: APIs can be scaled independently
- ✅ **Maintainability**: Clear separation of concerns
- ✅ **Modern**: Ready for SPA frameworks and mobile apps
- ✅ **Backward Compatible**: Existing HTML interface still works

Choose the right interface for your needs:
- **HTML**: Quick prototyping, simple apps, direct browser access
- **API**: Modern frameworks, mobile apps, third-party integration

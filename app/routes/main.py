from flask import Blueprint, request, jsonify
from app.database import graph, Node
from app.models.user import User
from app.models.relations import Relations
from app.models.post import Post
from app.models.comment import Comment

main_bp = Blueprint('main', __name__)
user = User(graph)
relations = Relations(graph)
post  = Post(graph)
comment = Comment(graph)


# Test route

@main_bp.route('/')
def accueil():
    return "<h1>Welcome to the API!</h1>"

@main_bp.route('/healthcheck')
def health_check():
    try:
        graph.run("MATCH (n) RETURN n LIMIT 1")
        return "Database OK", 200
    except Exception as e:
        return str(e), 500

# User routes

@main_bp.route('/users', methods=['GET'])
def get_users():
    users = graph.nodes.match("User")
    return jsonify([{"id": user.identity, "name": user["name"], "email": user["email"]} for user in users])

@main_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    
    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400
    
    user.create_user(name, email)
    return jsonify({"message": "User created successfully"}), 201

@main_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user_data = graph.nodes.match("User")
    return jsonify([{"id": user.identity, "name": user["name"], "email": user["email"]} for user in user_data if user.identity == user_id]), 200

@main_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')

    user = graph.nodes.get(user_id)
    if not user or user.labels != {"User"}:
        return jsonify({"error": "User not found"}), 404
        
    user["name"] = name if name else user["name"]
    user["email"] = email if email else user["email"]
    graph.push(user)
    return jsonify({"message": "User updated successfully"}), 200

@main_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = graph.nodes.get(user_id)
    if user and user.labels == {"User"}:
        graph.delete(user)
        return jsonify({"message": "User deleted successfully"})
    return jsonify({"error": "User not found"}), 404

@main_bp.route('/users/<int:user_id>/friends', methods=['GET'])
def get_user_friends(user_id):
    user = graph.nodes.get(user_id)
    if user and user.labels == {"User"}:
        friends = graph.match((user,), r_type="FRIENDS_WITH")
        return jsonify([{"id": friend.end_node.identity, "name": friend.end_node["name"]} for friend in friends])
    return jsonify({"error": "User not found"}), 404

@main_bp.route('/users/<int:user_id>/friends', methods=['POST'])
def add_friend(user_id):
    data = request.get_json()
    friend_id = data.get('friend_id')
    
    if not friend_id:
        return jsonify({"error": "Friend ID is required"}), 400
    
    relations.add_friend(user_id, friend_id)
    return jsonify({"message": "Friend added successfully"}), 201

@main_bp.route('/users/<int:user_id>/friends/<int:friend_id>', methods=['DELETE'])
def remove_friend(user_id, friend_id):
    user = graph.nodes.get(user_id)
    friend = graph.nodes.get(friend_id)
    if user and friend and user.labels == {"User"} and friend.labels == {"User"}:
        rel = graph.match_one((user, friend), r_type="FRIENDS_WITH")
        if rel is not None:
            graph.separate(rel)
            return jsonify({"message": "Friend removed successfully"})
    return jsonify({"error": "User or friend not found"}), 404

@main_bp.route('/users/<int:user_id>/friends/<int:friend_id>', methods=['GET'])
def check_friendship(user_id, friend_id):
    user = graph.nodes.get(user_id)
    friend = graph.nodes.get(friend_id)
    if user and friend and user.labels == {"User"} and friend.labels == {"User"}:
        rel = graph.match_one((user, friend), r_type="FRIENDS_WITH")
        if rel is not None:
            return jsonify({"message": "They are friends"})
        else:
            return jsonify({"message": "They are not friends"})
    return jsonify({"error": "User or friend not found"}), 404

@main_bp.route('/users/<int:user_id>/mutual-friends/<int:other_id>', methods=['GET'])
def get_mutual_friends(user_id, other_id):
    user = graph.nodes.get(user_id)
    other_user = graph.nodes.get(other_id)
    if user and other_user and user.labels == {"User"} and other_user.labels == {"User"}:
        user_friends = set(friend.end_node for friend in graph.match((user,), r_type="FRIENDS_WITH"))
        other_friends = set(friend.end_node for friend in graph.match((other,), r_type="FRIENDS_WITH"))
        mutual_friends = user_friends.intersection(other_friends)
        return jsonify(mutual_friends)
    return jsonify({"error": "User or other user not found"}), 404

# Post routes

@main_bp.route('/posts', methods=['GET'])
def get_posts():
    posts = graph.nodes.match("Post")
    return jsonify([{"id": post.identity, "title": post["title"], "content": post["content"]} for post in posts])

@main_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post_by_id(post_id):
    post = graph.nodes.get(post_id)
    if post and post.labels == {"Post"}:
        return jsonify({"id": post.identity, "title": post["title"], "content": post["content"]})
    return jsonify({"error": "Post not found"}), 404

@main_bp.route('/users/<int:user_id>/posts', methods=['GET'])
def get_user_posts(user_id):
    user = graph.nodes.get(user_id)
    if user and user.labels == {"User"}:
        posts = graph.match((user,), r_type="CREATED")
        return jsonify([{"id": post.end_node.identity, "title": post.end_node["title"], "content": post.end_node["content"]} for post in posts])
    return jsonify({"error": "User not found"}), 404

@main_bp.route('/users/<int:user_id>/posts', methods=['POST'])
def create_post(user_id):
    data = request.json
    title = data['title']
    content = data['content']
    user = graph.nodes.get(user_id)
    if user and user.labels == {"User"}:
        post_node = Node("Post", title=title, content=content)
        graph.create(post_node)
        relations.create_created_relationship(user, post_node)
        return jsonify({"message": "Post created successfully"}), 201
    return jsonify({"error": "User not found"}), 404

@main_bp.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    post = graph.nodes.get(post_id)
    if post and post.labels == {"Post"}:
        graph.delete(post)
        return jsonify({"message": "Post deleted successfully"})
    return jsonify({"error": "Post not found"}), 404

@main_bp.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    data = request.json
    post = graph.nodes.get(post_id)
    if post and post.labels == {"Post"}:
        post["title"] = data.get("title", post["title"])
        post["content"] = data.get("content", post["content"])
        graph.push(post)
        return jsonify({"message": "Post updated successfully"})
    return jsonify({"error": "Post not found"}), 404

@main_bp.route('/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    data = request.json
    user_id = data['user_id']
    user_id = int(user_id)
    user = graph.nodes.get(user_id)
    post = graph.nodes.get(post_id)
    if user and post and post.labels == {"Post"} and user.labels == {"User"}:
        relations.create_likes_relationship(user, post)
        return jsonify({"message": "Post liked successfully"})
    return jsonify({"error": "User or post not found"}), 404

@main_bp.route('/posts/<int:post_id>/like', methods=['DELETE'])
def unlike_post(post_id):
    data = request.json
    user_id = data['user_id']
    user_id = int(user_id)
    user = graph.nodes.get(user_id)
    post = graph.nodes.get(post_id)

    if user and post and post.labels == {"Post"} and user.labels == {"User"}:
        rel = graph.match_one((user, post), r_type="LIKES")
        if rel is not None:
            graph.separate(rel)
            return jsonify({"message": "Post unliked successfully"})
    return jsonify({"error": "User or post not found"}), 404

# Comment routes

@main_bp.route('/comments', methods=['GET'])
def get_all_comments():
    comments = graph.nodes.match("Comment")
    return jsonify([
        {"id": comment.identity, "content": comment["content"]}
        for comment in comments
    ])

@main_bp.route('/comments/<int:comment_id>', methods=['GET'])
def get_comment_by_id(comment_id):
    comment = graph.nodes.get(comment_id)
    if comment and comment.labels == {"Comment"}:
        return jsonify({"id": comment.identity, "content": comment["content"]})
    return jsonify({"error": "Comment not found"}), 404

@main_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
def create_comment(post_id):
    data = request.json
    user_id = data['user_id']
    content = data['content']

    user = graph.nodes.get(user_id)
    post = graph.nodes.get(post_id)

    if user and post and post.labels == {"Post"} and user.labels == {"User"}:
        comment_node = Node("Comment", content=content, created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        graph.create(comment_node)
        commentaire
        relations.create_created_relationship(user, comment_node)
        relations.create_has_comment_relationship(post, comment_node)
        return jsonify({"message": "Comment added successfully"}), 201

    return jsonify({"error": "User or post not found"}), 404

@main_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments_for_post(post_id):
    post = graph.nodes.get(post_id)
    if post and post.labels == {"Post"}:
        comments = graph.match((post,), r_type="HAS_COMMENT")
        return jsonify([
            {"id": comment.end_node.identity, "content": comment.end_node["content"]}
            for comment in comments
        ])
    return jsonify({"error": "Post not found"}), 404

@main_bp.route('/comments/<int:comment_id>', methods=['PUT'])
def update_comment(comment_id):
    data = request.json
    comment = graph.nodes.get(comment_id)
    if comment and comment.labels == {"Comment"}:
        comment["content"] = data.get("content", comment["content"])
        graph.push(comment)
        return jsonify({"message": "Comment updated successfully"})
    return jsonify({"error": "Comment not found"}), 404

@main_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    comment = graph.nodes.get(comment_id)
    if comment and comment.labels == {"Comment"}:
        graph.delete(comment)
        return jsonify({"message": "Comment deleted successfully"})
    return jsonify({"error": "Comment not found"}), 404

@main_bp.route('/posts/<int:post_id>/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment_from_post(post_id, comment_id):
    post = graph.nodes.get(post_id)
    comment = graph.nodes.get(comment_id)
    if post and comment and post.labels == {"Post"} and comment.labels == {"Comment"}:
        rel = graph.match_one((post, comment), r_type="HAS_COMMENT")
        if rel is not None:
            graph.delete(comment)
            return jsonify({"message": "Comment deleted successfully"})
    return jsonify({"error": "Post or comment not found"}), 404

@main_bp.route('/comments/<int:comment_id>/like', methods=['POST'])
def like_comment(comment_id):
    data = request.json
    user_id = data['user_id']
    user = graph.nodes.get(user_id)
    comment = graph.nodes.get(comment_id)
    if user and comment and comment.labels == {"Comment"} and user.labels == {"User"}:
        relations.create_likes_relationship(user, comment)
        return jsonify({"message": "Comment liked successfully"})

@main_bp.route('/comments/<int:comment_id>/like', methods=['DELETE'])
def unlike_comment(comment_id):
    data = request.json
    user_id = data['user_id']
    user = graph.nodes.get(user_id)
    comment = graph.nodes.get(comment_id)
    if user and comment and comment.labels == {"Comment"} and user.labels == {"User"}:
        print("User and comment found")
        rel = graph.match_one((user, comment), r_type="LIKES")
        print(rel is not None)
        if rel is not None:
            print("Relationship found")
            graph.separate(rel)
            return jsonify({"message": "Comment unliked successfully"})
    return jsonify({"error": "User or comment not found"}), 404
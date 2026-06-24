from rest_framework.response import Response
from rest_framework.views import APIView

from games.models import Comment, Game, GameGroup, GameGroupMember, Post


def _avatar_url(user, request=None):
    if not user.profile_image:
        return ""
    try:
        url = user.profile_image.url
        return request.build_absolute_uri(url) if request else url
    except Exception:
        return ""


def _post_to_dict(post, user=None, request=None):
    is_auth = bool(user and user.is_authenticated)
    likes_list = list(post.likes.all())
    likes_count = len(likes_list)
    is_liked = is_auth and any(u.id == user.id for u in likes_list)
    is_mine = is_auth and post.user_id == user.id
    comment_count = len(list(post.comments.all()))
    return {
        "id": post.id,
        "game_id": post.game_id,
        "category": post.category,
        "title": post.title,
        "body": post.content,
        "author": post.user.nickname or post.user.username,
        "author_id": post.user_id,
        "author_username": post.user.username,
        "author_avatar": _avatar_url(post.user, request),
        "created_at": post.created_at.strftime("%Y-%m-%d %H:%M"),
        "likes": likes_count,
        "is_liked": is_liked,
        "is_mine": is_mine,
        "comment_count": comment_count,
    }


def _group_to_dict(group, user=None, request=None):
    members = list(group.members.select_related("user").all())
    is_auth = bool(user and user.is_authenticated)
    is_joined = is_auth and any(m.user_id == user.id for m in members)
    is_mine = is_auth and group.owner_id == user.id
    return {
        "id": group.id,
        "game_id": group.game_id,
        "name": group.name,
        "description": group.description,
        "schedule": group.schedule,
        "style": group.play_style,
        "role": group.required_role,
        "capacity": group.capacity,
        "members": len(members),
        "joined": is_joined,
        "is_mine": is_mine,
        "memberNames": [m.user.nickname or m.user.username for m in members],
        "memberList": [
            {
                "name": m.user.nickname or m.user.username,
                "username": m.user.username,
                "avatar": _avatar_url(m.user, request),
            }
            for m in members
        ],
        "owner": group.owner.nickname or group.owner.username,
        "created_at": group.created_at.strftime("%Y-%m-%d"),
    }


class CommunityPostListView(APIView):
    def get(self, request, game_id):
        qs = (
            Post.objects.filter(game_id=game_id)
            .select_related("user")
            .prefetch_related("likes", "comments")
            .order_by("-created_at")
        )
        return Response([_post_to_dict(post, request.user, request) for post in qs])

    def post(self, request, game_id):
        if not request.user.is_authenticated:
            return Response({"detail": "로그인이 필요합니다."}, status=401)

        try:
            game = Game.objects.get(pk=game_id)
        except Game.DoesNotExist:
            return Response({"detail": "게임을 찾을 수 없습니다."}, status=404)

        title = request.data.get("title", "").strip()
        body = request.data.get("body", "").strip()
        category = request.data.get("category", "잡담").strip()

        if not title or not body:
            return Response({"detail": "제목과 내용은 필수입니다."}, status=400)

        post = Post.objects.create(
            game=game,
            user=request.user,
            title=title,
            content=body,
            category=category,
        )

        data = _post_to_dict(post, request.user, request)
        data["comments"] = []
        return Response(data, status=201)


class CommunityPostDetailView(APIView):
    def get(self, request, game_id, post_id):
        try:
            post = (
                Post.objects.select_related("user")
                .prefetch_related("likes", "comments__user")
                .get(pk=post_id, game_id=game_id)
            )
        except Post.DoesNotExist:
            return Response({"detail": "게시글을 찾을 수 없습니다."}, status=404)

        user = request.user
        is_auth = bool(user and user.is_authenticated)
        data = _post_to_dict(post, user, request)
        data["comments"] = [
            {
                "id": c.id,
                "author": c.user.nickname or c.user.username,
                "author_id": c.user_id,
                "author_username": c.user.username,
                "author_avatar": _avatar_url(c.user, request),
                "body": c.content,
                "created_at": c.created_at.strftime("%Y-%m-%d %H:%M"),
                "is_mine": is_auth and c.user_id == user.id,
            }
            for c in post.comments.all()
        ]
        return Response(data)

    def delete(self, request, game_id, post_id):
        if not request.user.is_authenticated:
            return Response({"detail": "로그인이 필요합니다."}, status=401)

        try:
            post = Post.objects.get(pk=post_id, game_id=game_id, user=request.user)
        except Post.DoesNotExist:
            return Response({"detail": "게시글을 찾을 수 없습니다."}, status=404)

        post.delete()
        return Response(status=204)


class CommunityPostLikeView(APIView):
    def post(self, request, game_id, post_id):
        if not request.user.is_authenticated:
            return Response({"detail": "로그인이 필요합니다."}, status=401)

        try:
            post = Post.objects.get(pk=post_id, game_id=game_id)
        except Post.DoesNotExist:
            return Response({"detail": "게시글을 찾을 수 없습니다."}, status=404)

        user = request.user
        if post.likes.filter(id=user.id).exists():
            post.likes.remove(user)
            is_liked = False
        else:
            post.likes.add(user)
            is_liked = True

        return Response({"likes": post.likes.count(), "is_liked": is_liked})


class CommunityCommentView(APIView):
    def post(self, request, game_id, post_id):
        if not request.user.is_authenticated:
            return Response({"detail": "로그인이 필요합니다."}, status=401)

        try:
            post = Post.objects.get(pk=post_id, game_id=game_id)
        except Post.DoesNotExist:
            return Response({"detail": "게시글을 찾을 수 없습니다."}, status=404)

        body = request.data.get("body", "").strip()
        if not body:
            return Response({"detail": "댓글 내용은 필수입니다."}, status=400)

        comment = Comment.objects.create(
            post=post,
            user=request.user,
            content=body,
        )

        return Response(
            {
                "id": comment.id,
                "author": comment.user.nickname or comment.user.username,
                "author_id": comment.user_id,
                "author_username": comment.user.username,
                "author_avatar": _avatar_url(comment.user, request),
                "body": comment.content,
                "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
                "is_mine": True,
            },
            status=201,
        )


class CommunityCommentDeleteView(APIView):
    def delete(self, request, game_id, comment_id):
        if not request.user.is_authenticated:
            return Response({"detail": "로그인이 필요합니다."}, status=401)

        try:
            comment = Comment.objects.select_related("post").get(
                pk=comment_id, post__game_id=game_id, user=request.user
            )
        except Comment.DoesNotExist:
            return Response({"detail": "댓글을 찾을 수 없습니다."}, status=404)

        comment.delete()
        return Response(status=204)


class CommunityGroupListView(APIView):
    def get(self, request, game_id):
        gs = (
            GameGroup.objects.filter(game_id=game_id)
            .prefetch_related("members__user")
            .select_related("owner")
            .order_by("-created_at")
        )
        return Response([_group_to_dict(g, request.user, request) for g in gs])

    def post(self, request, game_id):
        if not request.user.is_authenticated:
            return Response({"detail": "로그인이 필요합니다."}, status=401)

        try:
            game = Game.objects.get(pk=game_id)
        except Game.DoesNotExist:
            return Response({"detail": "게임을 찾을 수 없습니다."}, status=404)

        name = request.data.get("name", "").strip()
        if not name:
            return Response({"detail": "그룹 이름은 필수입니다."}, status=400)

        try:
            capacity = max(2, min(20, int(request.data.get("capacity", 4))))
        except (TypeError, ValueError):
            capacity = 4

        group = GameGroup.objects.create(
            game=game,
            owner=request.user,
            name=name,
            description=request.data.get("description", "").strip(),
            schedule=request.data.get("schedule", "").strip(),
            play_style=request.data.get("style", "").strip(),
            required_role=request.data.get("role", "").strip(),
            capacity=capacity,
        )
        GameGroupMember.objects.create(group=group, user=request.user)

        user = request.user
        member_name = user.nickname or user.username
        return Response(
            {
                "id": group.id,
                "game_id": group.game_id,
                "name": group.name,
                "description": group.description,
                "schedule": group.schedule,
                "style": group.play_style,
                "role": group.required_role,
                "capacity": group.capacity,
                "members": 1,
                "joined": True,
                "is_mine": True,
                "memberNames": [member_name],
                "memberList": [
                    {
                        "name": member_name,
                        "username": user.username,
                        "avatar": _avatar_url(user, request),
                    }
                ],
                "owner": member_name,
                "created_at": group.created_at.strftime("%Y-%m-%d"),
            },
            status=201,
        )


class CommunityGroupJoinView(APIView):
    def post(self, request, game_id, group_id):
        if not request.user.is_authenticated:
            return Response({"detail": "로그인이 필요합니다."}, status=401)

        try:
            group = GameGroup.objects.prefetch_related("members").get(
                pk=group_id, game_id=game_id
            )
        except GameGroup.DoesNotExist:
            return Response({"detail": "그룹을 찾을 수 없습니다."}, status=404)

        if group.members.filter(user=request.user).exists():
            return Response({"detail": "이미 참여 중인 그룹입니다."}, status=400)

        if group.members.count() >= group.capacity:
            return Response({"detail": "그룹 인원이 가득 찼습니다."}, status=400)

        GameGroupMember.objects.create(group=group, user=request.user)

        group = (
            GameGroup.objects.prefetch_related("members__user")
            .select_related("owner")
            .get(pk=group_id)
        )
        return Response(_group_to_dict(group, request.user, request))


class CommunityGroupLeaveView(APIView):
    def delete(self, request, game_id, group_id):
        if not request.user.is_authenticated:
            return Response({"detail": "로그인이 필요합니다."}, status=401)

        try:
            member = GameGroupMember.objects.select_related("group__owner").get(
                group__id=group_id, group__game_id=game_id, user=request.user
            )
        except GameGroupMember.DoesNotExist:
            return Response({"detail": "참여 중인 그룹이 아닙니다."}, status=404)

        group = member.group
        member.delete()

        remaining = GameGroupMember.objects.filter(group=group).count()
        if remaining == 0:
            group.delete()
            return Response(status=204)

        if group.owner_id == request.user.id:
            new_owner_member = (
                GameGroupMember.objects.select_related("user")
                .filter(group=group)
                .first()
            )
            if new_owner_member:
                group.owner = new_owner_member.user
                group.save(update_fields=["owner"])

        return Response(status=204)

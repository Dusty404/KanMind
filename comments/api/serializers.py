from rest_framework import serializers
from ..models import Comment


class CommentsSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="owner.profile.fullname", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]
        read_only_fields = ["id", "created_at", "author"]

    def create(self, validated_data):
        request = self.context["request"]

        return Comment.objects.create(
            owner=request.user,
            task=self.context["task"],
            **validated_data
        )

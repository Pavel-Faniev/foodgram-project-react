from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Subscribe
from .serializers import SubscribeViewSerializer

User = get_user_model()


class SubscribeApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        pk = kwargs.get('id', None)
        author = get_object_or_404(User, pk=pk)
        user = request.user

        if author == user:
            return Response(
                {'error': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST)

        if Subscribe.objects.filter(author=author, user=user).exists():
            return Response(
                {'error': 'Вы уже подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST)

        obj = Subscribe(author=author, user=user)
        obj.save()

        serializer = SubscribeViewSerializer(
            author, context={'request': request})

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        try:
            subscription = get_object_or_404(Subscribe, user=user,
                                             author=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Subscribe.DoesNotExist:
            return Response(
                'Ошибка отписки',
                status=status.HTTP_400_BAD_REQUEST,
            )


class ListSubscribeViewSet(generics.ListAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubscribeViewSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(subscribing__user=user)

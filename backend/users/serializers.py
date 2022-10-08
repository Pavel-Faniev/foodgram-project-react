from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import Recipe  # isort:skip
from foodgram.settings import RECIPES_LIMIT  # isort:skip
from .models import Subscribe  # isort:skip

User = get_user_model()


class UserRegistrationSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'password')


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context['request']
        if not request or request.user.is_anonymous:
            return False
        return Subscribe.objects.filter(
            user=self.context['request'].user,
            author=obj
        ).exists()


class SubscribeUserSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Subscribe
        fields = ('user', 'author')

    def validate(self, data):
        user = self.context['request'].user
        subscribing_id = data['author'].id
        if Subscribe.objects.filter(user=user,
                                    subscribing__id=subscribing_id).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя')
        if user.id == subscribing_id:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя')
        return data


class SubscribingRecipesSerializers(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeViewSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        if not self.context['request'].user.is_authenticated:
            return False
        return Subscribe.objects.filter(
            author=obj, user=self.context['request'].user).exists()

    def get_recipes(self, obj):
        recipes_limit = int(self.context['request'].GET.get(
            'recipes_limit', RECIPES_LIMIT))
        user = get_object_or_404(User, pk=obj.pk)
        recipes = Recipe.objects.filter(author=user)[:recipes_limit]

        return SubscribingRecipesSerializers(recipes, many=True).data

    def get_recipes_count(self, obj):
        user = get_object_or_404(User, pk=obj.pk)
        return Recipe.objects.filter(author=user).count()

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import IngredientsFilter, RecipeFilter
from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)
from .permissions import IsAuthorOrAdmin
from .serializers import (AddRecipeSerializer, FavoriteSerializer,
                          IngredientSerializer, ShowRecipeFullSerializer,
                          TagSerializer)
from .utils import get_shopping_list


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели рецепта"""
    queryset = Recipe.objects.all().order_by("-id")
    filter_backends = (DjangoFilterBackend,)
    filter_class = RecipeFilter
    serializer_class = ShowRecipeFullSerializer
    permission_classes = (IsAuthorOrAdmin,)

    def get_serializer_class(self):
        """Метод выбора сериализатора в зависимости от запроса."""
        if self.request.method == "GET":
            return ShowRecipeFullSerializer
        return AddRecipeSerializer

    def add_recipe(self, model, user, pk):
        """Метод для добавления"""
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response({
                'errors': 'Рецепт уже добавлен в список'
            }, status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = FavoriteSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe(self, model, user, pk):
        """Метод для удаления"""
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({
            'errors': 'Рецепт уже удален'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        url_path="favorite",
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Метод для добавления/удаления из избранного"""
        if request.method == 'POST':
            return self.add_recipe(Favorite, request.user, pk)
        else:
            return self.delete_recipe(Favorite, request.user, pk)

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        url_path="shopping_cart",
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """Метод для добавления/удаления из продуктовой корзины"""
        if request.method == 'POST':
            return self.add_recipe(ShoppingCart, request.user, pk)
        else:
            return self.delete_recipe(ShoppingCart, request.user, pk)

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[IsAuthenticated],
        url_path="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        """Метод для получения и скачивания
        списка продуктов из продуктовой корзины"""
        ingredients_list = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            "ingredient__name",
            "ingredient__measurement_unit"
        ).annotate(amount=Sum("amount"))
        return get_shopping_list(ingredients_list)


class IngredientsViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели ингридиента"""
    pagination_class = None
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientsFilter
    search_fields = ("^name",)


class TagsViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели тега"""
    pagination_class = None
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

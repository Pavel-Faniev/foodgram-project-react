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
                          IngredientSerializer, ShoppingCartSerializer,
                          ShowRecipeFullSerializer, TagSerializer)
from .utils import get_shopping_list


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by("-id")
    filter_backends = [DjangoFilterBackend]
    filter_class = RecipeFilter
    serializer_class = ShowRecipeFullSerializer
    permission_classes = [IsAuthorOrAdmin]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ShowRecipeFullSerializer
        return AddRecipeSerializer

    def post(self, model, model_serializer, text_error, user, recipe, request):
        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {"error": text_error},
                status=status.HTTP_400_BAD_REQUEST,
            )
        object = model.objects.create(user=user, recipe=recipe)
        serializer = model_serializer(object,
                                      context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, model, user, recipe):
        object = model.objects.filter(user=user, recipe=recipe)
        if object.exists():
            object.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        url_path="favorite",
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == "POST":
            self.post(Favorite,
                      FavoriteSerializer,
                      "Вы уже добавили рецепт в избранное",
                      user, recipe, request)
        if request.method == "DELETE":
            self.delete(Favorite, user, recipe)

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        url_path="shopping_cart",
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == "POST":
            self.post(ShoppingCart,
                      ShoppingCartSerializer,
                      "Вы уже добавили рецепт в список покупок",
                      user, recipe, request)
        if request.method == "DELETE":
            self.delete(ShoppingCart, user, recipe)

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[IsAuthenticated],
        url_path="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        ingredients_list = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            "ingredient__name",
            "ingredient__measurement_unit"
        ).annotate(amount=Sum("amount"))
        return get_shopping_list(ingredients_list)


class IngredientsViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientsFilter
    search_fields = ("^name",)


class TagsViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

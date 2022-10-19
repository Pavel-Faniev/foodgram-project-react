from drf_extra_fields.fields import Base64ImageField
from jsonschema import ValidationError
from rest_framework import serializers
from users.serializers import CustomUserSerializer

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингридиентов"""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингридиентов в рецепте"""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.CharField(
        read_only=True,
        source='ingredient.name'
    )
    measurement_unit = serializers.CharField(
        read_only=True,
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор модели тегов"""
    slug = serializers.SlugField()

    class Meta:
        model = Tag
        fields = '__all__'
        lookup_field = 'slug'


class AddRecipeIngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для продуктов при создании рецепта"""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class AddRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов"""
    author = CustomUserSerializer(read_only=True)
    ingredients = AddRecipeIngredientsSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    cooking_time = serializers.IntegerField()
    image = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'name',
                  'image', 'text', 'cooking_time')

    def validate_ingredients(self, data):
        """Валидатор ингридиентов"""
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Нужно выбрать минимум 1 ингредиент!')
        for ingredient in ingredients:
            try:
                int(ingredient.get('amount'))
                if int(ingredient.get('amount')) <= 0:
                    raise serializers.ValidationError(
                        'Количество должно быть положительным!')
            except Exception:
                raise ValidationError({'amount': 'Колличество должно'
                                      'быть числом'})
            check_id = ingredient['id']
            check_ingredient = Ingredient.objects.filter(id=check_id)
            if not check_ingredient.exists():
                raise serializers.ValidationError(
                    'Данного продукта нет в базе!')
        return data

    def validate_cooking_time(self, data):
        """Валидатор времени приготовления"""
        cooking_time = self.initial_data.get('cooking_time')
        try:
            int(cooking_time)
            if int(cooking_time) < 1:
                raise serializers.ValidationError(
                    'Время готовки не может быть'
                    ' меньше 1!')
            if int(cooking_time) > 600:
                raise serializers.ValidationError(
                    'Время готовки не может быть'
                    ' больше 600!')
        except Exception:
            raise serializers.ValidationError({'cooking_time': 'Время'
                                               ' должно быть больше 0'})
        return data

    def validate_tags(self, data):
        """Валидатор тегов"""
        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Рецепт не может быть без тегов'
            )
        for tag_id in tags:
            if not Tag.objects.filter(id=tag_id).exists():
                raise serializers.ValidationError(
                    f'Тег с id = {tag_id} не существует'
                )
        tags_bd = set(tags)
        if len(tags) != len(tags_bd):
            raise ValidationError('Теги должны быть уникальными')
        return data

    def create_bulk(self, recipe, ingredients_data):
        """Метод работы bulk_create для создания
           большого числа объектов в БД """
        RecipeIngredient.objects.bulk_create([RecipeIngredient(
            ingredient=ingredient['ingredient'],
            recipe=recipe,
            amount=ingredient['amount']
        ) for ingredient in ingredients_data])

    def create(self, validated_data):
        """Метод создания рецепта"""
        author = self.context.get('request').user
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.save()
        recipe.tags.set(tags_data)
        self.create_bulk(recipe, ingredients_data)
        return recipe

    def update(self, recipe, validated_data):
        """Метод редактирования рецепта"""
        recipe.name = validated_data.get('name', recipe.name)
        recipe.text = validated_data.get('text', recipe.text)
        recipe.cooking_time = validated_data.get(
            'cooking_time', recipe.cooking_time
        )
        recipe.image = validated_data.get('image', recipe.image)
        if 'ingredients' in self.initial_data:
            ingredients = validated_data.pop('ingredients')
            recipe.ingredients.clear()
            for ingredient in ingredients:
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient['ingredient'],
                    amount=ingredient['amount'],
                )
        if 'tags' in self.initial_data:
            tags_data = validated_data.pop('tags')
            recipe.tags.set(tags_data)
        recipe.save()
        return recipe

    def to_representation(self, recipe):
        """Метод представления результатов сериализатора"""
        self.fields.pop('ingredients')
        self.fields['tags'] = TagSerializer(many=True)

        representation = super().to_representation(recipe)
        representation['ingredients'] = RecipeIngredientSerializer(
            RecipeIngredient.objects.filter(
                recipe=recipe).all(), many=True).data

        return representation


class ShowRecipeFullSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'name',
                  'image', 'text', 'cooking_time', 'is_favorited',
                  'is_in_shopping_cart')

    def get_ingredients(self, obj):
        """Получает список ингридиентов для рецепта."""
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        """Проверяет находится ли рецепт в избранном."""
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Favorite.objects.filter(recipe=obj,
                                       user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверяет находится ли рецепт в продуктовой корзине."""
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(recipe=obj,
                                           user=request.user).exists()


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов"""
    id = serializers.CharField(
        read_only=True, source='recipe.id',
    )
    cooking_time = serializers.CharField(
        read_only=True, source='recipe.cooking_time',
    )
    image = serializers.CharField(
        read_only=True, source='recipe.image',
    )
    name = serializers.CharField(
        read_only=True, source='recipe.name',
    )

    def validate(self, data):
        """Валидатор избранных рецептов"""
        recipe = data['recipe']
        user = data['user']
        if user == recipe.author:
            raise serializers.ValidationError(
                'Вы не можете добавить свои рецепты в избранное')
        if Favorite.objects.filter(recipe=recipe, user=user).exists():
            raise serializers.ValidationError(
                'Вы уже добавили рецепт в избранное')
        return data

    def create(self, validated_data):
        """Метод создания избранного"""
        favorite = Favorite.objects.create(**validated_data)
        favorite.save()
        return favorite

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор продуктовой корзины"""
    id = serializers.CharField(
        read_only=True,
        source='recipe.id',
    )
    cooking_time = serializers.CharField(
        read_only=True,
        source='recipe.cooking_time',
    )
    image = serializers.CharField(
        read_only=True,
        source='recipe.image',
    )
    name = serializers.CharField(
        read_only=True,
        source='recipe.name',
    )

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time')

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

User = get_user_model()


class Recipe(models.Model):
    author = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='user_recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Картинка',
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        'Tag',
        through='RecipeTag',
        related_name='tag_recipes',
        verbose_name='Теги',
    )
    cooking_time = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1,
                              'Минимальное время приготовления 1 мин'
                              )
        ],
        verbose_name='Время приготовления (в минутах)',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.text


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название тега',
        db_index=True,
    )
    color = models.CharField(
        'Цвет',
        help_text=(
            'Введите код цвета в шестнадцетиричном формате (#ABCDEF)'),
        max_length=7,
        unique=True,
        validators=(
            RegexValidator(
                regex='^#[a-fA-F0-9]{6}$', code='wrong_hex_code',
                message='Неправильный формат цвета'),
        )
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Уникальный слаг'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
    )

    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент по рецепту'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=(MinValueValidator(1),)
    )


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_tag',
        verbose_name='Рецепт',
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='recipe_tag',
        verbose_name='Тег рецепта',
    )


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='favorite'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite'
            )
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_cart'
            )
        ]

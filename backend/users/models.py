from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    USER = 'user'
    ADMIN = 'admin'

    ROLES = (
        (USER, USER),
        (ADMIN, ADMIN),
    )

    username = models.TextField('Пользователь',
                                unique=True,
                                max_length=150
                                )
    role = models.CharField('Роль',
                            max_length=10,
                            choices=ROLES,
                            default=USER)
    first_name = models.TextField('Имя',
                                  max_length=150)
    last_name = models.TextField('Фамилия',
                                 max_length=150)
    email = models.EmailField('E-mail',
                              unique=True,
                              max_length=254)

    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser

    class Meta:
        ordering = ('username',)

    def __str__(self):
        if self.username:
            return self.username
        return self.email


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribing'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_author_user_subscribing'
            )
        ]

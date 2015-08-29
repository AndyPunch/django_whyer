import factory

from models import User


class UserFactory(factory.Factory):
    FACTORY_FOR = User

    username = factory.Sequence(lambda i: 'username%s' % i)
    first_name = factory.Sequence(lambda i: 'first_name%s' % i)
    last_name = factory.Sequence(lambda i: 'last_name%s' % i)
    email = factory.LazyAttribute(lambda o: '%s@example.org' % o.username)
    password = "password"

    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop('password', None)
        user = super(UserFactory, cls)._prepare(create, **kwargs)
        if password:
            user.set_password(password)
            if create:
                user.save()
        return user
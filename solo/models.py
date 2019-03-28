try:
    from django.core.cache import caches
    get_cache = lambda cache_name: caches[cache_name]
except ImportError:
    from django.core.cache import get_cache

from django.conf import settings
from django.db.models import Model
from django.utils.timezone import now

from solo import settings as solo_settings


cache_name = getattr(settings, 'SOLO_CACHE', solo_settings.SOLO_CACHE)
cache = get_cache(cache_name)

__all__ = ('SingletonModel',)


class SingletonModel(Model):
    """
    Use class constructor for saving and retrieving singletone:

    class SingleModel(SingletonModel):
        pass

    solo = SingleModel.get_solo()

    That's it.
    """

    def delete(self, *args, **kwargs):
        pass

    def save(self, *args, **kwargs):
        self.id = 1
        super(SingletonModel, self).save(*args, **kwargs)
        self._update_solo(self)

    @classmethod
    def get_cache_key(cls):
        prefix = getattr(settings, 'SOLO_CACHE_PREFIX', solo_settings.SOLO_CACHE_PREFIX)
        return '%s:%s' % (prefix, cls.__name__.lower())

    @classmethod
    def check_expired(cls):
        """
        If cached timestamp for singleton is newer than current instance, reset instance.
        It's necessary due to keeping actual instance between multiple processes/threads.
        """
        val = cache.get(cls.get_cache_key())
        if val and hasattr(cls, '_instance') and val > cls._instance._timestamp:
            del cls._instance

    @classmethod
    def _update_solo(cls, instanse):
        cls._instance = instanse
        instanse._timestamp = now()

        cache.set(cls.get_cache_key(), instanse._timestamp)

    @classmethod
    def get_solo(cls):
        cls.check_expired()

        if not hasattr(cls, '_instance'):
            cls._instance, created = cls.objects.get_or_create(id=1)
            cls._instance._timestamp = now()

        return cls._instance

    class Meta:
        abstract = True

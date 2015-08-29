from django.db.models import IntegerField, PositiveIntegerField
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

import forms
from datetime import datetime

from models import Vote, Score
from default_settings import RATINGS_VOTES_PER_IP
from exceptions import *

if 'django.contrib.contenttypes' not in settings.INSTALLED_APPS:
    raise ImportError("djangoratings requires django.contrib.contenttypes in your INSTALLED_APPS")

from django.contrib.contenttypes.models import ContentType

__all__ = ('Rating', 'RatingField', 'AnonymousRatingField')

try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5
    

def md5_hexdigest(value):
    return md5(value).hexdigest()


class Rating(object):
    def __init__(self, score, votes):
        self.score = score
        self.votes = votes


class RatingManager(object):
    def __init__(self, instance, field):
        self.content_type = None
        self.instance = instance
        self.field = field
        
        self.votes_field_name = "%s_votes" % (self.field.name,)
        self.score_field_name = "%s_score" % (self.field.name,)
    
    def get_percent(self):
        """get_percent()
        
        Returns the weighted percentage of the score from min-max values"""
        return 100 * ((self.get_rating() - self.field.range_lower) / (self.field.range_upper - self.field.range_lower))
    
    def get_real_percent(self):
        """get_real_percent()
        
        Returns the unmodified percentage of the score based on a 0-point scale."""
        return 100 * ((self.get_real_rating() - self.field.range_lower) / (self.field.range_upper - self.field.range_lower))
    
    def get_ratings(self):
        """get_ratings()
        
        Returns a Vote QuerySet for this rating field."""
        return Vote.objects.filter(content_type=self.get_content_type(), object_id=self.instance.pk, key=self.field.key)
        
    def get_rating(self):
        """get_rating()
        
        Returns the weighted average rating."""
        if not self.votes:
            return 0
        return float(self.score)/(self.votes+self.field.weight)
    
    def get_opinion_percent(self):
        """get_opinion_percent()
        
        Returns a neutral-based percentage."""
        return (self.get_percent()+100)/2

    def get_real_rating(self):
        """get_rating()
        
        Returns the unmodified average rating."""
        if not self.votes:
            return 0
        return float(self.score)/self.votes
    
    def get_rating_for_user(self, user, ip_address=None, cookies={}):
        """get_rating_for_user(user, ip_address=None, cookie=None)
        
        Returns the rating for a user or anonymous IP."""
        kwargs = dict(
            content_type    = self.get_content_type(),
            object_id       = self.instance.pk,
            key             = self.field.key,
        )

        if not (user and user.is_authenticated()):
            if not ip_address:
                raise ValueError('``user`` or ``ip_address`` must be present.')
            kwargs['user__isnull'] = True
            kwargs['ip_address'] = ip_address
        else:
            kwargs['user'] = user
        
        use_cookies = (self.field.allow_anonymous and self.field.use_cookies)
        if use_cookies:
            # TODO: move 'vote-%d.%d.%s' to settings or something
            cookie_name = 'vote-%d.%d.%s' % (kwargs['content_type'].pk, kwargs['object_id'], kwargs['key'][:6],) # -> md5_hexdigest?
            cookie = cookies.get(cookie_name)
            if cookie:    
                kwargs['cookie'] = cookie
            else:
                kwargs['cookie__isnull'] = True
            
        try:
            rating = Vote.objects.get(**kwargs)
            try:
                return self.field.values[rating.score - self.field.range_lower]
            except IndexError:
                pass
        except Vote.MultipleObjectsReturned:
            pass
        except Vote.DoesNotExist:
            pass
        return
        
    def add(self, score, user, ip_address, cookies={}, commit=True):
        """add(score, user, ip_address)
        
        Used to add a rating to an object."""
        if score in self.field.types:
            score = self.field.types[score]
        
        try:
            score = int(score)
        except (ValueError, TypeError):
            raise InvalidRating("%s is not a valid choice for %s" % (score, self.field.name))
        
        delete = (score == 0)
        if delete and not self.field.allow_delete:
            raise CannotDeleteVote("you are not allowed to delete votes for %s" % (self.field.name,))
            # ... you're also can't delete your vote if you haven't permissions to change it. I leave this case for CannotChangeVote
        
        if score and (score < self.field.range_lower or score > self.field.range_upper):
            raise InvalidRating("%s is not a valid choice for %s" % (score, self.field.name))

        is_anonymous = (user is None or not user.is_authenticated())
        if is_anonymous and not self.field.allow_anonymous:
            raise AuthRequired("user must be a user, not '%r'" % (user,))
        
        if is_anonymous:
            user = None
        
        defaults = dict(
            score = score,
            ip_address = ip_address,
        )
        
        kwargs = dict(
            content_type    = self.get_content_type(),
            object_id       = self.instance.pk,
            key             = self.field.key,
            user            = user,
        )
        if not user:
            kwargs['ip_address'] = ip_address
        
        use_cookies = (self.field.allow_anonymous and self.field.use_cookies)
        if use_cookies:
            defaults['cookie'] = datetime.now().strftime('%Y%m%d%H%M%S%f') # -> md5_hexdigest?
            # TODO: move 'vote-%d.%d.%s' to settings or something
            cookie_name = 'vote-%d.%d.%s' % (kwargs['content_type'].pk, kwargs['object_id'], kwargs['key'][:6],) # -> md5_hexdigest?
            cookie = cookies.get(cookie_name) # try to get existent cookie value
            if not cookie:
                kwargs['cookie__isnull'] = True
            kwargs['cookie'] = cookie

        try:
            rating, created = Vote.objects.get(**kwargs), False
        except Vote.DoesNotExist:
            if delete:
                raise CannotDeleteVote("attempt to find and delete your vote for %s is failed" % (self.field.name,))
            if getattr(settings, 'RATINGS_VOTES_PER_IP', RATINGS_VOTES_PER_IP):
                num_votes = Vote.objects.filter(
                    content_type=kwargs['content_type'],
                    object_id=kwargs['object_id'],
                    key=kwargs['key'],
                    ip_address=ip_address,
                ).count()
                if num_votes >= getattr(settings, 'RATINGS_VOTES_PER_IP', RATINGS_VOTES_PER_IP):
                    raise IPLimitReached()
            kwargs.update(defaults)
            if use_cookies:
                # record with specified cookie was not found ...
                cookie = defaults['cookie'] # ... thus we need to replace old cookie (if presented) with new one
                kwargs.pop('cookie__isnull', '') # ... and remove 'cookie__isnull' (if presented) from .create()'s **kwargs
            rating, created = Vote.objects.create(**kwargs), True
            
        has_changed = False
        if not created:
            if self.field.can_change_vote:
                has_changed = True
                self.score -= rating.score
                # you can delete your vote only if you have permission to change your vote
                if not delete:
                    rating.score = score
                    rating.save()
                else:
                    self.votes -= 1
                    rating.delete()
            else:
                raise CannotChangeVote()
        else:
            has_changed = True
            self.votes += 1

        if has_changed:
            if not delete:
                self.score += rating.score
            if commit:
                self.instance.save()
            #setattr(self.instance, self.field.name, Rating(score=self.score, votes=self.votes))
            
            score, created = Score.objects.get_or_create(
                content_type=self.get_content_type(),
                object_id=self.instance.pk,
                key=self.field.key,
            defaults = dict(
                score   = self.score,
                votes   = self.votes,
            )
            )
            if not created:
                if (score.score != self.score or
                    score.votes != self.votes):
                    score.score = self.score
                    score.votes = self.votes
                score.save()
        
        # return value
        adds = {}
        if use_cookies:
            adds['cookie_name'] = cookie_name
            adds['cookie'] = cookie
        if delete:
            adds['deleted'] = True
        return adds

    def delete(self, user, ip_address, cookies={}, commit=True):
        return self.add(0, user, ip_address, cookies, commit)
    
    def _get_votes(self, default=None):
        return getattr(self.instance, self.votes_field_name, default)
    
    def _set_votes(self, value):
        return setattr(self.instance, self.votes_field_name, value)
        
    votes = property(_get_votes, _set_votes)

    def _get_score(self, default=None):
        return getattr(self.instance, self.score_field_name, default)
    
    def _set_score(self, value):
        if value in self.field.types:
            value = self.field.types[value]
        return setattr(self.instance, self.score_field_name, value)
        
    score = property(_get_score, _set_score)

    def get_content_type(self):
        if self.content_type is None:
            self.content_type = ContentType.objects.get_for_model(self.instance)
        return self.content_type
    
    def _update(self, commit=False):
        """Forces an update of this rating (useful for when Vote objects are removed)."""
        votes = Vote.objects.filter(
            content_type    = self.get_content_type(),
            object_id       = self.instance.pk,
            key             = self.field.key,
        )
        obj_score = sum([v.score for v in votes])
        obj_votes = len(votes)

        score, created = Score.objects.get_or_create(
            content_type    = self.get_content_type(),
            object_id       = self.instance.pk,
            key             = self.field.key,
            defaults        = dict(
                score       = obj_score,
                votes       = obj_votes,
            )
        )
        if not created:
            score.score = obj_score
            score.votes = obj_votes
            score.save()
        self.score = obj_score
        self.votes = obj_votes
        if commit:
            self.instance.save()


class RatingCreator(object):
    def __init__(self, field):
        self.field = field
        self.votes_field_name = "%s_votes" % (self.field.name,)
        self.score_field_name = "%s_score" % (self.field.name,)

    def __get__(self, instance, type=None):
        if instance is None:
            return self.field
            #raise AttributeError('Can only be accessed via an instance.')
        return RatingManager(instance, self.field)

    def __set__(self, instance, value):
        if isinstance(value, Rating):
            setattr(instance, self.votes_field_name, value.votes)
            setattr(instance, self.score_field_name, value.score)
        else:
            raise TypeError("%s value must be a Rating instance, not '%r'" % (self.field.name, value))


class RatingField(IntegerField):
    """
    A rating field contributes two columns to the model instead of the standard single column.
    """
    def __init__(self, *args, **kwargs):
        if 'choices' in kwargs:
            raise TypeError("%s invalid attribute 'choices'" % (self.__class__.__name__,))
        self.can_change_vote = kwargs.pop('can_change_vote', False)
        self.allow_anonymous = kwargs.pop('allow_anonymous', False)
        self.use_cookies = kwargs.pop('use_cookies', False)
        self.allow_delete = kwargs.pop('allow_delete', False)
        self.widget_template = kwargs.pop('widget_template', 'djangoratings/_rating.html')
        self.weight = kwargs.pop('weight', 0)
        self.range_lower = kwargs.pop('lower', 1)
        self.range_upper = kwargs.pop('upper', None)
        if self.range_upper is None:
            self.range_upper = kwargs.pop('range', 2)
        self.titles = kwargs.pop('titles', [])
        self.values = kwargs.pop('values', range(self.range_lower, self.range_upper+1))
        self.types = dict(zip(self.values, range(self.range_lower, self.range_upper+1)))
        self.types[''] = 0
        kwargs['editable'] = False
        kwargs['default'] = 0
        kwargs['blank'] = True
        super(RatingField, self).__init__(*args, **kwargs)
    
    def contribute_to_class(self, cls, name):
        self.name = name

        # Votes tally field
        self.votes_field = PositiveIntegerField(
            editable=False, default=0, blank=True)
        cls.add_to_class("%s_votes" % (self.name,), self.votes_field)

        # Score sum field
        self.score_field = IntegerField(
            editable=False, default=0, blank=True)
        cls.add_to_class("%s_score" % (self.name,), self.score_field)

        self.key = md5_hexdigest(self.name)

        field = RatingCreator(self)

        if not hasattr(cls, '_djangoratings'):
            cls._djangoratings = []
        cls._djangoratings.append(self)

        setattr(cls, name, field)

    def get_db_prep_save(self, value, connection=None):
        # XXX: what happens here?
        pass

    def get_db_prep_lookup(self, lookup_type, value, connection=None, prepared=False):
        # TODO: hack in support for __score and __votes
        # TODO: order_by on this field should use the weighted algorithm
        raise NotImplementedError(self.get_db_prep_lookup)
        # if lookup_type in ('score', 'votes'):
        #     lookup_type = 
        #     return self.score_field.get_db_prep_lookup()
        if lookup_type == 'exact':
            return [self.get_db_prep_save(value, connection)]
        elif lookup_type == 'in':
            return [self.get_db_prep_save(v, connection) for v in value]
        else:
            return super(RatingField, self).get_db_prep_lookup(lookup_type, value)

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.RatingField}
        defaults.update(kwargs)
        return super(RatingField, self).formfield(**defaults)

    # TODO: flatten_data method


class AnonymousRatingField(RatingField):
    def __init__(self, *args, **kwargs):
        kwargs['allow_anonymous'] = True
        super(AnonymousRatingField, self).__init__(*args, **kwargs)


class VotingField(RatingField):
    def __init__(self, *args, **kwargs):
        kwargs['widget_template'] = kwargs.get('widget_template', 'djangoratings/_voting.html')
        kwargs['lower'] = -1
        kwargs['upper'] = 1
        kwargs['titles'] = (_("Down"), _("Clear"), _("Up"))
        kwargs['values'] = ('down', 'clear', 'up')
        super(VotingField, self).__init__(*args, **kwargs)


class AnonymousVotingField(VotingField):
    def __init__(self, *args, **kwargs):
        kwargs['allow_anonymous'] = True
        super(AnonymousVotingField, self).__init__(*args, **kwargs)


class FavoriteField(RatingField):
    def __init__(self, *args, **kwargs):
        kwargs['widget_template'] = kwargs.get('widget_template', 'djangoratings/_favorite.html')
        kwargs['lower'] = 0
        kwargs['upper'] = 1
        kwargs['titles'] = (_("Clear"), _("Favorite"))
        kwargs['values'] = ('clear', 'favorite')
        super(FavoriteField, self).__init__(*args, **kwargs)


class AnonymousFavoriteField(FavoriteField):
    def __init__(self, *args, **kwargs):
        kwargs['allow_anonymous'] = True
        super(AnonymousFavoriteField, self).__init__(*args, **kwargs)


class FlagField(RatingField):
    def __init__(self, *args, **kwargs):
        kwargs['widget_template'] = kwargs.get('widget_template', 'djangoratings/_flag.html')
        kwargs['lower'] = 0
        kwargs['upper'] = 1
        kwargs['titles'] = (_("Clear"), _("Flag"))
        kwargs['values'] = ('clear', 'flag')
        super(FlagField, self).__init__(*args, **kwargs)


class AnonymousFlagField(FlagField):
    def __init__(self, *args, **kwargs):
        kwargs['allow_anonymous'] = True
        super(AnonymousFlagField, self).__init__(*args, **kwargs)

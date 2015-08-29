from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse, Http404

from exceptions import *
from default_settings import RATINGS_VOTES_PER_IP

def _rating_widget(instance, field, had_voted):
    ratings = []
    for num in range(field.field.range_lower, field.field.range_upper+1):
        if num == field.score:
            checked = True
        else:
            checked = False
        try:
            value = field.field.values[num-field.field.range_lower]
        except IndexError:
            value = num
        try:
            title = field.field.titles[num-field.field.range_lower]
        except IndexError:
            title = ''
        ratings.append({
            'checked': checked,
            'value': value,
            'title': title,
        })
    content_type = ContentType.objects.get_for_model(instance)
    return {
        'content_type': content_type,
        'instance': instance,
        'model': content_type.model,
        'app_label': content_type.app_label,
        'object_id': instance.id,
        'field_name': field.field.name,
        'had_voted' : had_voted,
        'score': field.score,
        'votes': field.votes,
        'vote': int(round(field.score)),
        'ratings': ratings,
        'percent': field.get_percent(),
        'real_percent': field.get_real_percent(),
        'positive': int((field.votes * field.get_real_percent() / 100) + 0.5),
        'negative': int((field.votes - (field.votes * (field.get_real_percent() / 100))) + 0.5),
    }


class AddRatingView(object):
    def __call__(self, request, content_type_id, object_id, field_name, score):
        """__call__(request, content_type_id, object_id, field_name, score)
        
        Adds a vote to the specified model field."""
        
        try:
            instance = self.get_instance(content_type_id, object_id)
        except ObjectDoesNotExist:
            message = _("Object does not exist")
            raise Http404(message)
        
        context = self.get_context(request)
        context['instance'] = instance
        
        try:
            field = getattr(instance, field_name)
        except AttributeError:
            return self.invalid_field_response(request, context)
        
        context.update({
            'field': field,
            'score': score,
        })
        
        had_voted = field.get_rating_for_user(request.user, request.META['REMOTE_ADDR'], request.COOKIES)
        
        context['had_voted'] = had_voted
                    
        try:
            adds = field.add(score, request.user, request.META.get('REMOTE_ADDR'), request.COOKIES)
        except IPLimitReached:
            return self.too_many_votes_from_ip_response(request, context)
        except AuthRequired:
            return self.authentication_required_response(request, context)
        except InvalidRating:
            return self.invalid_rating_response(request, context)
        except CannotChangeVote:
            return self.cannot_change_vote_response(request, context)
        except CannotDeleteVote:
            return self.cannot_delete_vote_response(request, context)
        if had_voted is not None:
            return self.rating_changed_response(request, context, adds)
        return self.rating_added_response(request, context, adds)
    
    def get_context(self, request, context={}):
        return context
    
    def render_to_response(self, template, context, request):
        raise NotImplementedError

    def too_many_votes_from_ip_response(self, request, context):
        message = _("Too many votes from this IP address for this object.")
        response = HttpResponse(message)
        return response

    def rating_changed_response(self, request, context, adds={}):
        message = _("Vote changed.")
        response = HttpResponse(message)
        if 'cookie' in adds:
            cookie_name, cookie = adds['cookie_name'], adds['cookie']
            if 'deleted' in adds:
                response.delete_cookie(cookie_name)
            else:
                response.set_cookie(cookie_name, cookie, 31536000, path='/') # TODO: move cookie max_age to settings
        return response
    
    def rating_added_response(self, request, context, adds={}):
        message = _("Vote recorded.")
        response = HttpResponse(message)
        if 'cookie' in adds:
            cookie_name, cookie = adds['cookie_name'], adds['cookie']
            if 'deleted' in adds:
                response.delete_cookie(cookie_name)
            else:
                response.set_cookie(cookie_name, cookie, 31536000, path='/') # TODO: move cookie max_age to settings
        return response

    def authentication_required_response(self, request, context):
        message = _("You must be logged in to vote.")
        response = HttpResponse(message)
        response.status_code = 403
        return response
    
    def cannot_change_vote_response(self, request, context):
        message = "You have already voted."
        response = HttpResponse(message)
        response.status_code = 403
        return response
    
    def cannot_delete_vote_response(self, request, context):
        message = _("You can't delete this vote.")
        response = HttpResponse(message)
        response.status_code = 403
        return response
    
    def invalid_field_response(self, request, context):
        message = _("Invalid field name.")
        response = HttpResponse(message)
        response.status_code = 403
        return response
    
    def invalid_rating_response(self, request, context):
        message = _("Invalid rating value.")
        response = HttpResponse(message)
        response.status_code = 403
        return response
        
    def get_instance(self, content_type_id, object_id):
        return ContentType.objects.get(pk=content_type_id)\
            .get_object_for_this_type(pk=object_id)


class AddRatingFromModel(AddRatingView):
    def __call__(self, request, model, app_label, object_id, field_name, score):
        """__call__(request, model, app_label, object_id, field_name, score)
        
        Adds a vote to the specified model field."""
        try:
            content_type = ContentType.objects.get(model=model, app_label=app_label)
        except ContentType.DoesNotExist:
            message = _("Invalid `model` or `app_label`.")
            raise Http404(message)
        
        return super(AddRatingFromModel, self).__call__(request, content_type.id,
                                                        object_id, field_name, score)

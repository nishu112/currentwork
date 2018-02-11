from django.forms import ModelForm
from django.contrib.auth.models import User
from friendsbook.models import *
from betterforms.multiform import MultiModelForm
from django.forms import widgets
from djng.forms import fields
from django.utils import six
from django import forms
from djng.forms.fields import ImageField
from django.core.exceptions import ValidationError
from djng.forms import fields,NgDeclarativeFieldsMetaclass, NgModelFormMixin , NgForm,  NgModelForm, NgFormValidationMixin
from djng.styling.bootstrap3.forms import Bootstrap3Form
from django.urls import reverse_lazy
from djng.forms.fields import ImageField
from django.core.exceptions import ValidationError


class SubscribeForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3Form):
    use_required_attribute = False
    scope_prefix = 'my_data'
    form_name = 'my_form'

    photo = ImageField(
        label='Photo of yourself',
        fileupload_url=reverse_lazy('UpdateCover'),
        area_label='Drop image here or click to upload',
        required=False)




class SignUpForm(ModelForm):
	class Meta:
		model=User
		fields = ["username","password","password"]

class ProfileForm(ModelForm):
	class Meta:
		model=Profile
		fields= ["fname","lname","emailid","gender"]


class CreatePost(ModelForm):
	class Meta:
		model=Status
		fields = ["text","image","privacy"]

class LoginForm(ModelForm):
	class Meta:
		model=User
		fields = ["username","password"]

class UpdateCover(ModelForm):
	class Meta:
		model=Status
		fields=["image"]

class UpdateProfile(ModelForm):
		class Meta:
			model=Status
			fields=["image"]

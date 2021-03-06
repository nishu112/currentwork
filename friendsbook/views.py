from django.contrib.auth import authenticate, login as auth_login
from django.contrib import auth
from django.shortcuts import HttpResponse, render, redirect
from django.views.generic import View
from django.views import generic
from .forms import *
from . import views
from django.shortcuts import get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
import datetime

from django.http import JsonResponse
from django.db.models import Q
from django.core import serializers
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist


def fishy(request):
    return HttpResponse('Something Fishy is going on')


def user_post(request, user, posts):
    # modify it to get all the timeline posts
    for x in posts:
        x.likes = StatusLikes.objects.filter(sid=x).count()
        x.comments = Comment.objects.filter(sid=x).count()
        x.is_like = StatusLikes.objects.filter(username=request.user, sid=x).count()
    return posts


def Check_user_online(request, user):
    obj1 = FriendsWith.objects.filter(username=user, confirm_request=2, blocked_status=0).select_related(
        'fusername').values('fusername')
    obj1 = User.objects.filter(id__in=obj1)
    obj2 = FriendsWith.objects.filter(fusername=user, confirm_request=2, blocked_status=0).select_related(
        'username').values('username')
    obj2 = User.objects.filter(id__in=obj2)
    obj = obj1 | obj2
    chatusers = obj
    for x in chatusers:
        x.status = 'Online' if hasattr(x, 'logged_in_user') else 'Offline'
        x.noOf_unread = int(Message.objects.filter(username=x, fusername=user, is_read=False).count())
    return chatusers


def Check_user_Username(request, user):
    obj1 = FriendsWith.objects.filter(username=user, confirm_request=2, blocked_status=0).select_related(
        'fusername').values('fusername')
    obj1 = User.objects.filter(id__in=obj1).values('username')
    obj2 = FriendsWith.objects.filter(fusername=user, confirm_request=2, blocked_status=0).select_related(
        'username').values('username')
    obj2 = User.objects.filter(id__in=obj2).values('username')
    obj = obj1 | obj2
    return obj


def group_list(request):
    groups = ConsistOf.objects.filter(username=request.user, confirm=1).select_related('gid')
    return groups


def user_list_data(request):
    users = User.objects.select_related('logged_in_user')
    for user in users:
        user.status = 'Online' if hasattr(user, 'logged_in_user') else 'Offline'
    return users


def user_list(request):
    users = Check_user_online(request, request.user)

    return render(request, 'chat/main_chat.html', {'chatusers': users})


# remove these lines

def FriendsOfFriends(request, user):
    chatusers = Check_user_online(request, User.objects.get(username=user))
    friends_suggestion = User.objects.none()
    for x in chatusers:
        y = Check_user_online(request, x)
        friends_suggestion = friends_suggestion | y
    user = User.objects.filter(username=user)
    user.status = 'Online' if hasattr(user, 'logged_in_user') else 'Offline'
    chatusers = user | chatusers
    friends_suggestion = friends_suggestion | chatusers
    return friends_suggestion


# get all the friends
def FriendList(request, user):
    friends = Profile.objects.all()
    return friends


##searching of user

def friendship(user_obj, fuser_obj):
    friendship = FriendsWith.objects.filter(
        Q(username=user_obj, fusername=fuser_obj) | Q(username=fuser_obj, fusername=user_obj))
    if friendship.exists():
        for y in friendship:
            if y.confirm_request == 2:
                return 3
            else:
                checkConnectionDirection = FriendsWith.objects.filter(username=user_obj, fusername=fuser_obj)
                if checkConnectionDirection.exists():
                    return 1
                else:
                    return 2
    else:
        return 0


def friends_list(request, searched_by, context):
    addfriends_list = list()

    for x in context['data']:
        if str(x.username) == searched_by:
            addfriends_list.append(-1)
        else:
            user = searched_by
            fuser = x.username
            user_obj = User.objects.get(username=user)
            fuser_obj = User.objects.get(username=fuser)
            addfriends_list.append(friendship(user_obj, fuser_obj))
    context['data'] = zip(context['data'], addfriends_list)
    return context


# define
# 0-send request
# 1-cancel request
# 2- confirm request sent by user
# 3 unfriends( means already friends)

class RegistrationView(View):
    user_class = SignUpForm
    profile_class = ProfileForm
    template_name = "user/signup.html"

    # get get request from form
    def get(self, request):
        user_form = self.user_class(None)
        profile_form = self.profile_class(None)
        return render(request, self.template_name, {'user_form': user_form, 'profile_form': profile_form})

    ##if we get post request from 'form'
    def post(self, request):
        user_form = self.user_class(request.POST)
        profile_form = self.profile_class(request.POST)
        if (user_form.is_valid() and profile_form.is_valid()):
            user = user_form.save(commit=False)
            username = user_form.cleaned_data['username']
            raw_password = user_form.cleaned_data['password']
            fname = request.POST['fname']
            lname = request.POST['lname']
            emailid = request.POST['emailid']
            gender = request.POST['gender']
            user.set_password(raw_password)
            user.save()
            id = User.objects.get(username=username).id
            Profile.objects.filter(username_id=id).update(fname=fname, lname=lname, emailid=emailid, gender=gender)
            return redirect('login')
        # user=authenticate(username=username,password=raw_password)
        # if user is not None:
        #				if user.is_active:
        #					auth_login(request,user)
        # return redirect('index')
        # verify though emailid first then login
        # create view for this
        return render(request, self.template_name, {'user_form': user_form, 'profile_form': profile_form})


def education(request):
    if request.method == 'POST':
        details = EducationDetails(request.POST)
        if details.is_valid():
            education = details.save(commit=False)
            education.username = request.user
            education.save()
            return redirect('workDetail')
        else:
            return render(request, "user/educationDetails.html", {'form': form})
    else:
        form = EducationDetails(None)
        return render(request, "user/educationDetails.html", {'form': form})


def workingProfile(request):
    # return redirect('index')
    if request.method == 'POST':
        details = WorkingFor(request.POST)
        if details.is_valid():
            education = details.save(commit=False)
            education.username = request.user
            education.save()
            return redirect('index')
        else:
            return render(request, "user/educationDetails.html", {'form': form})
    else:
        form = WorkingFor(None)
        return render(request, "user/working.html", {'form': form})


class LoginView(View):
    form_class = LoginForm
    template_name = "user/login.html"

    # get method
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('index')
        form = LoginForm(None)
        return render(request, self.template_name, {'form': form})

    # post method
    def post(self, request):
        form = LoginForm(request.POST)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            auth_login(request, user)
            epsilon = '0:10:60.000000'
            diff = datetime.datetime.now() - request.user.date_joined
            if str(diff) < epsilon:
                return redirect('educationDetails')
            return redirect('index')
        else:
            return render(request, "user/login.html", {'form': form})


def logout(request):
    auth.logout(request)
    return render(request, "user/logout.html")


# update_profile   //Complete it using class based views
# @login_required
# @transaction.atomic
# def update_profile(request):
#    if request.method == 'POST':
#        user_form = UserForm(request.POST, instance=request.user)
#        profile_form = ProfileForm(request.POST, instance=request.user.profile)
#        if user_form.is_valid() and profile_form.is_valid():
#            user_form.save()
#            profile_form.save()
#            messages.success(request, _('Your profile was successfully updated!'))
#            return redirect('settings:profile')
#        else:
#            messages.error(request, _('Please correct the error below.'))
#    else:
#        user_form = UserForm(instance=request.user)
#        profile_form = ProfileForm(instance=request.user.profile)
#    return render(request, 'profiles/profile.html', {
#        'user_form': user_form,
#        'profile_form': profile_form
#    })

POSTS_NUM_PAGES = 4


def GetUserPosts(request):
    chatusers = Check_user_online(request, request.user)
    friends_suggestion = FriendsOfFriends(request, request.user)
    user = User.objects.filter(username=request.user)
    user.status = 'Online' if hasattr(user, 'logged_in_user') else 'Offline'
    friendsAndMe = chatusers | user

    friends_suggestion = User.objects.filter(id__in=friends_suggestion).exclude(id__in=friendsAndMe)
    friendsPostWithoutGroup = Status.objects.filter(username__in=chatusers, gid__isnull=True).exclude(
        privacy='me').select_related('username').order_by('-time')  ##friends Posts
    tempfriendsPostWithGroupPrivacyOpen = Status.objects.filter(username__in=chatusers,
                                                                gid__isnull=False).select_related('username').order_by(
        '-time')
    friendsPostWithGroupPrivacyOpen = Status.objects.none()
    UserPartOfGroup = ConsistOf.objects.filter(username=request.user, confirm=1).values('gid')
    PostOfUserPartOfGroup = Status.objects.filter(gid__in=UserPartOfGroup)
    for x in tempfriendsPostWithGroupPrivacyOpen:
        if x.gid.privacy == 'OP':
            friendsPostWithGroupPrivacyOpen = friendsPostWithGroupPrivacyOpen | Status.objects.filter(id=x.id)
    myPosts = Status.objects.filter(username=request.user).select_related('username').order_by('-time')
    friendsOfFriendsPosts = Status.objects.filter(username__in=friends_suggestion, gid__isnull=True).exclude(
        privacy='me').exclude(privacy='fs').select_related('username').order_by('-time')
    posts = friendsPostWithoutGroup | friendsPostWithGroupPrivacyOpen | myPosts | friendsOfFriendsPosts | PostOfUserPartOfGroup
    # from_feed = -1
    # if allposts:
    #    from_feed = feeds[0].id
    return posts


# load on timeline posts for ajax call

def GetUserPostsByAjax(request):
    page = request.GET.get('page')
    group = request.GET.get('groupid')

    user = request.GET.get('requestuser')

    # check validations that requested user is connected to a group or not
    if user:
        user = get_object_or_404(User, username=user)
        try:
            profile = Profile.objects.get(username=user)
        except ObjectDoesNotExist:
            return JsonResponse(0, safe=False)
        chatusers = Check_user_online(request, profile.username)
        friends_suggestion = FriendsOfFriends(request, profile.username)
        tempuser = User.objects.filter(username=profile.username)

        y = friendship(request.user, profile.username)
        privacy = 'NoConnection'
        for x in chatusers:
            if str(request.user.username) == str(x.username):
                privacy = 'fs'
        friends_suggestion = friends_suggestion.exclude(username=User.objects.get(username=profile.username))
        # queryset.exclude(lugar="Quito")
        if request.user == profile.username:
            posts = user_post(request, request.user, GetUserPosts(request))
            privacy = 'NoNeed'
        elif request.user in friends_suggestion and privacy != 'fs':
            privacy = 'fsofs'
        # check all conditions for all privacy
        PusersFriends = Check_user_online(request, profile.username)
        LoggedInUserFriends = Check_user_online(request, request.user)
        if privacy == 'fsofs':
            commonFriends = PusersFriends & LoggedInUserFriends

            CommonFriendsPosts = Status.objects.filter(Q(username__in=commonFriends, gid__isnull=True)).exclude(
                privacy='me').exclude(privacy='fs')
            # update
            UserPostWithPrivacyPublic = Status.objects.filter(username=profile.username, gid__isnull=True).exclude(
                privacy='me').exclude(privacy='fs')
            LoggedInUserPosts = Status.objects.filter(username=request.user, gid__isnull=True).exclude(
                privacy='me').exclude(privacy='fs')
            PuserFriendsWithoutCommon = Status.objects.filter(username__in=PusersFriends, gid__isnull=True,
                                                              privacy='Pbc')
            posts = CommonFriendsPosts | PuserFriendsWithoutCommon | LoggedInUserPosts | UserPostWithPrivacyPublic


        elif privacy == 'fs':

            # chatusers=Check_user_online(request,profile.username)
            commonFriends = PusersFriends & LoggedInUserFriends
            mutualFriendsPosts = Status.objects.filter(username__in=commonFriends, gid__isnull=True).exclude(
                privacy='me').order_by('-time')
            PuserFriendsPosts = Status.objects.filter(username__in=PusersFriends, gid__isnull=True).exclude(
                privacy='me').exclude(privacy='fs').order_by('-time')
            LoggedInUserPosts = Status.objects.filter(username=request.user, gid__isnull=True).exclude(
                privacy='me').order_by('-time')

            PuserPosts = Status.objects.filter(username=profile.username, gid__isnull=True).exclude(privacy='me')

            posts = LoggedInUserPosts | PuserFriendsPosts | mutualFriendsPosts | PuserPosts
        elif privacy == 'NoConnection':
            # define some post methods here
            userposts = Status.objects.filter(username=profile.username, gid__isnull=True,
                                              privacy='Pbc').select_related('username').order_by('time')
            FriendsPostsWithPublicPrivacy = Status.objects.filter(username__in=PusersFriends, gid__isnull=True,
                                                                  privacy='Pbc')
            posts = userposts | FriendsPostsWithPublicPrivacy

        # group posts a users can see on anyone profile
        # common groups
        PuserGroupPostWithClosedPrivacy = ConsistOf.objects.filter(username=profile.username).select_related(
            'gid').values('gid')
        LoggedInUserGroupsWithClosedPrivacy = ConsistOf.objects.filter(username=request.user).select_related(
            'gid').values('gid')
        commonGroups = PuserGroupPostWithClosedPrivacy & LoggedInUserGroupsWithClosedPrivacy
        PuserGroupPost = Status.objects.filter(gid__in=commonGroups, username=profile.username).order_by('-time')
        # PuserGroupWithOpenPrivacy=ConsistOf.objects.filter(username=profile.username)
        # PuserGroupWithOpenPrivacy=ConsistOf.objects.none().select_related('gid').values('gid')
        PuserGroupsWithOpenPrivacy = Groups.objects.filter(id__in=PuserGroupPostWithClosedPrivacy, privacy='OP').values(
            'id')

        PuserGroupPostWithOpenPrivacy = Status.objects.filter(username=profile.username,
                                                              gid__in=PuserGroupsWithOpenPrivacy).order_by('-time')
        posts = posts | PuserGroupPost | PuserGroupPostWithOpenPrivacy
        if privacy != 'NoNeed':
            posts = user_post(request, request.user, posts)

    # code to load post and using the privacy features
    elif group is None:
        postsOfUserExcludingGroupPosts = GetUserPosts(request)
        UserPartOfGroup = ConsistOf.objects.filter(username=request.user, confirm=1).values('gid')
        GroupFeeds = Status.objects.filter(gid__in=UserPartOfGroup).order_by('-time')
        posts = postsOfUserExcludingGroupPosts | GroupFeeds
        posts = user_post(request, request.user, posts)

    else:
        UserPartOfGroup = ConsistOf.objects.filter(username=request.user, confirm=1).values('gid')
        GroupFeeds = Status.objects.filter(gid=group).order_by('-time')
        posts = GroupFeeds
        posts = user_post(request, request.user, posts)

    all_posts = posts
    paginator = Paginator(all_posts, POSTS_NUM_PAGES)
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        return HttpResponseBadRequest()
    except EmptyPage:
        posts = []
    if (len(posts) == 0):
        return JsonResponse(0, safe=False)
    ajax_posts = render_to_string('uposts/partials/ajax_only_post.html', {'posts': posts}, request)
    return JsonResponse(ajax_posts, safe=False)


def home(request):
    chatusers = Check_user_online(request, request.user)
    user = User.objects.filter(username=request.user)
    user.status = 'Online' if hasattr(user, 'logged_in_user') else 'Offline'
    friends_suggestion = FriendsOfFriends(request, request.user)
    friendsAndMe = chatusers | user
    friends_suggestion = User.objects.filter(id__in=friends_suggestion).exclude(id__in=friendsAndMe)
    postsOfUserExcludingGroupPosts = GetUserPosts(request)
    UserPartOfGroup = ConsistOf.objects.filter(username=request.user, confirm=1).values('gid')
    GroupFeeds = Status.objects.filter(gid__in=UserPartOfGroup).order_by('-time')
    posts = postsOfUserExcludingGroupPosts | GroupFeeds
    posts = user_post(request, request.user, posts)

    all_posts = posts
    paginator = Paginator(all_posts, POSTS_NUM_PAGES)
    posts = paginator.page(1)
    groups = group_list(request)
    pending_request = FriendsWith.objects.filter(fusername=request.user, confirm_request=1)

    return render(request, "home/index.html", {'posts': posts, 'page': 1, 'chatusers': chatusers, 'groups': groups,
                                               'friends_suggestion': friends_suggestion[0:10],
                                               'pending_request': pending_request[0:10],
                                               'newGroupForm': CreateGroup(None)})


def getSinglePost(request):
    if request.is_ajax():
        id = request.GET.get('id')

        status = Status.objects.get(id=id)
        # chatusers=Check_user_online(request,request.user)
        # user=User.objects.filter(username=request.user)
        # user.status = 'Online' if hasattr(user, 'logged_in_user') else 'Offline'
        # friends_suggestion=FriendsOfFriends(request,request.user)
        # friendsAndMe=chatusers|user
        # friends_suggestion=User.objects.filter(id__in=friends_suggestion).exclude(id__in=friendsAndMe)
        status.likes = StatusLikes.objects.filter(sid=status).count()
        status.comments = Comment.objects.filter(sid=status).count()
        status.is_like = StatusLikes.objects.filter(username=request.user, sid=status).count()
        content = render_to_string('uposts/posts.html', {'status': status}, request)
        return JsonResponse(content, safe=False)


def PostDetailView(request, slug):
    status = Status.objects.get(slug=slug)
    chatusers = Check_user_online(request, request.user)
    user = User.objects.filter(username=request.user)
    user.status = 'Online' if hasattr(user, 'logged_in_user') else 'Offline'
    friends_suggestion = FriendsOfFriends(request, request.user)
    friendsAndMe = chatusers | user
    friends_suggestion = User.objects.filter(id__in=friends_suggestion).exclude(id__in=friendsAndMe)
    status.likes = StatusLikes.objects.filter(sid=status).count()
    status.comments = Comment.objects.filter(sid=status).count()
    status.is_like = StatusLikes.objects.filter(username=request.user, sid=status).count()

    groups = group_list(request)
    template_name = 'uposts/single_post.html'
    return render(request, template_name,
                  {'status': status, 'chatusers': chatusers, 'friends_suggestion': friends_suggestion,
                   'groups': groups})


def AboutGroup(request, pk):
    group = get_object_or_404(Groups, id=pk)
    try:
        result = ConsistOf.objects.get(username=request.user, gid=group)
    except ObjectDoesNotExist:
        result = None
    if result and result.confirm == 1:
        group.new = 0
    else:
        group.new = 1
    if result == None:
        group.relation = 0
    else:
        group.relation = 1

    if group.privacy == 'CL' and result == None or result and result.confirm == 0:
        return redirect('groupMembers', pk=pk)

    # check user have the permission to access this group
    # only then user able to access this method
    chatusers = Check_user_online(request, request.user)
    try:
        group_consist = ConsistOf.objects.get(gid=group, username=request.user, confirm=1)
    except ObjectDoesNotExist:
        group_consist = None

    return render(request, "groups/partial/about.html",
                  {'group': group, 'chatusers': chatusers, 'group_consist': group_consist})


def grouphome(request, pk):
    group = get_object_or_404(Groups, id=pk)
    try:
        result = ConsistOf.objects.get(username=request.user, gid=group)
    except ObjectDoesNotExist:
        result = None
    if result and result.confirm == 1:
        group.new = 0
    else:
        group.new = 1
    if result == None:
        group.relation = 0
    else:
        group.relation = 1

    if group.privacy == 'CL' and result == None or result and result.confirm == 0:
        return redirect('groupMembers', pk=pk)

    if request.method == 'POST':
        form = CreateGroupPost(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.username = User.objects.get(username=request.user.username)
            post.title = "posted in "
            post.gid = group
            post = form.save()
            groupMembers = ConsistOf.objects.filter(gid=group, confirm=1).exclude(username=request.user).select_related(
                'username').values('username')
            for x in groupMembers:
                Notification.objects.create(from_user=request.user, to_user_id=x['username'], gid=group,
                                            notification_type='PG')
        # Notification.objects.create(from_user=request.user,gid=group,notification_type='PG')
        return HttpResponseRedirect(request.path_info)
    else:
        form = CreateGroupPost(None)
        # check user have the permission to access this group
        # only then user able to access this method
        posts = Status.objects.filter(gid=group).select_related('username').order_by('-time')
        posts = user_post(request, request.user, posts)
        all_posts = posts
        paginator = Paginator(all_posts, POSTS_NUM_PAGES)
        posts = paginator.page(1)

        chatusers = Check_user_online(request, request.user)
        try:
            group_consist = ConsistOf.objects.get(gid=group, username=request.user, confirm=1)
        except ObjectDoesNotExist:
            group_consist = None

        return render(request, "groups/index.html",
                      {'posts': posts, 'page': 1, 'group': group, 'form': form, 'chatusers': chatusers,
                       'group_consist': group_consist})


def groupMembers(request, pk):
    group = get_object_or_404(Groups, id=pk)

    try:
        result = ConsistOf.objects.get(username=request.user, gid=group)
    except ObjectDoesNotExist:
        result = None
    if result and result.confirm == 1:
        group.new = 0
    else:
        group.new = 1

    if result == None:
        group.relation = 0
    else:
        group.relation = 1

    # check user have the permission to access this group
    # only then user able to access this method
    chatusers = Check_user_online(request, request.user)
    members = ConsistOf.objects.filter(gid=group, gadmin=0, confirm=1).select_related('username')
    admins = ConsistOf.objects.filter(gid=group, gadmin=1).select_related('username')
    try:
        group_consist = ConsistOf.objects.get(gid=group, username=request.user, confirm=1)
    except ObjectDoesNotExist:
        group_consist = None

    return render(request, "groups/partial/group_members.html",
                  {'group_members': members, 'group': group, 'chatusers': chatusers, 'admins': admins,
                   'group_consist': group_consist, 'group_consist': group_consist})


def GroupsPhotos(request, pk):
    group = get_object_or_404(Groups, id=pk)
    # use paginartor to show all photos
    try:
        result = ConsistOf.objects.get(username=request.user, gid=group)
    except ObjectDoesNotExist:
        result = None
    if result and result.confirm == 1:
        group.new = 0
    else:
        group.new = 1

    if result == None:
        group.relation = 0
    else:
        group.relation = 1

    if group.privacy == 'CL' and result == None or result and result.confirm == 0:
        return redirect('groupMembers', pk=pk)

    chatusers = Check_user_online(request, request.user)

    posts = Status.objects.filter(gid=group).select_related('username').order_by('-time')
    photo_albums = Status.objects.filter(gid=group)
    try:
        group_consist = ConsistOf.objects.get(gid=group, username=request.user, confirm=1)
    except ObjectDoesNotExist:
        group_consist = None
    return render(request, "groups/partial/photo_frame.html",
                  {'group': group, 'chatusers': chatusers, 'group_consist': group_consist,
                   'photo_albums': photo_albums})


# update this to just load the group photos

def Groupfiles(request, pk):
    group = get_object_or_404(Groups, id=pk)

    try:
        result = ConsistOf.objects.get(username=request.user, gid=group)
    except ObjectDoesNotExist:
        result = None
    if result and result.confirm == 1:
        group.new = 0
    else:
        group.new = 1

    if result == None:
        group.relation = 0
    else:
        group.relation = 1

    if group.privacy == 'CL' and result == None or result and result.confirm == 0:
        return redirect('groupMembers', pk=pk)

    chatusers = Check_user_online(request, request.user)

    posts = Status.objects.filter(gid=group).select_related('username').order_by('-time')
    photo_albums = Status.objects.filter(gid=group)
    try:
        group_consist = ConsistOf.objects.get(gid=group, username=request.user, confirm=1)
    except ObjectDoesNotExist:
        group_consist = None
    files = Status.objects.none()
    return render(request, "groups/partial/files.html",
                  {'group': group, 'chatusers': chatusers, 'group_consist': group_consist, 'files': files})


def GroupsSettings(request, pk):
    group = get_object_or_404(Groups, id=pk)

    try:
        result = ConsistOf.objects.get(username=request.user, gid=group)
    except ObjectDoesNotExist:
        result = None
    if result and result.confirm == 1:
        group.new = 0
    else:
        group.new = 1

    if result == None:
        group.relation = 0
    else:
        group.relation = 1
    if group.privacy == 'CL' and result == None or result and result.confirm == 0 or group.new is 1:
        return redirect('groupMembers', pk=pk)

    # check user have the permission to access this group
    # only then user able to access this method
    chatusers = Check_user_online(request, request.user)
    members = ConsistOf.objects.filter(gid=group, gadmin=0, confirm=1).select_related('username')
    admins = ConsistOf.objects.filter(gid=group, gadmin=1).select_related('username')
    try:
        group_consist = ConsistOf.objects.get(gid=group, username=request.user, confirm=1)
    except ObjectDoesNotExist:
        group_consist = None

    if request.method == 'POST':
        form = CreateGroup(request.POST, instance=group)
        if form.is_valid():
            form.save()
        else:
            return render(request, "groups/partial/settings.html",
                          {'group': group, 'chatusers': chatusers, 'group_consist': group_consist, 'form': form})
        return redirect('AboutGroup', group.id)
    else:
        form = CreateGroup(instance=group)
        return render(request, "groups/partial/settings.html",
                      {'group': group, 'chatusers': chatusers, 'group_consist': group_consist, 'form': form})


def EditAboutGroupInfo(request, pk):
    group = get_object_or_404(Groups, id=pk)

    try:
        result = ConsistOf.objects.get(username=request.user, gid=group)
    except ObjectDoesNotExist:
        result = None
    if result and result.confirm == 1:
        group.new = 0
    else:
        group.new = 1

    if result == None:
        group.relation = 0
    else:
        group.relation = 1

    # check user have the permission to access this group
    # only then user able to access this method
    chatusers = Check_user_online(request, request.user)
    members = ConsistOf.objects.filter(gid=group, gadmin=0, confirm=1).select_related('username')
    admins = ConsistOf.objects.filter(gid=group, gadmin=1).select_related('username')
    try:
        group_consist = ConsistOf.objects.get(gid=group, username=request.user, confirm=1)
    except ObjectDoesNotExist:
        group_consist = None

    if request.method == 'POST':
        form = EditAboutGroup(request.POST, instance=group)
        if form.is_valid():
            about = request.POST['about']
            Groups.objects.filter(id=pk).update(about=about)
        return redirect('AboutGroup', group.id)
    else:
        form = EditAboutGroup(instance=group)
        return render(request, "groups/partial/Edit about.html",
                      {'group': group, 'chatusers': chatusers, 'group_consist': group_consist, 'form': form})


def LeaveGroup(request):
    if request.is_ajax() and request.method == 'POST':
        gid = request.POST['id']
        group = get_object_or_404(Groups, id=gid)
        ConsistOf.objects.filter(username=request.user, gid=group).delete()
        noOfAdminLeft = len(ConsistOf.objects.filter(gid=group), admin=1)
        members = 0
        if noOfAdminLeft is 0:
            members = len(ConsistOf.objects.filter(gid=group))
            if members is 0:
                return redirect('index')
            else:
                # user with highest number of post will be made admin
                groupMembers = ConsistOf.objects.filter(gid=group)
                newadmin = groupMembers[:1]
                Max = -1
                for x in groupMembers:
                    x.noOfPosts = Status.objects.filter(username=x.username, gid=group)
                    if max < x.noOfPosts:
                        newadmin = x
                        max = x.noOfPosts
                ConsistOf.objects.filter(gid=group, username=x.username).update(gadmin=1, confirm=1)
                ConsistOf.objects.all()

        return redirect('GroupsHomepage', pk=group.id)


def ManageGroupMember(request, pk):
    group = get_object_or_404(Groups, id=pk)

    try:
        result = ConsistOf.objects.get(username=request.user, gid=group)
    except ObjectDoesNotExist:
        result = None
    if result and result.confirm == 1:
        group.new = 0
    else:
        group.new = 1

    if result == None:
        group.relation = 0
    else:
        group.relation = 1
    try:
        group_consist = ConsistOf.objects.get(gid=group, username=request.user, confirm=1)
    except ObjectDoesNotExist:
        group_consist = None

    if group.privacy == 'CL' and result == None or result and result.confirm == 0 or group_consist.gadmin == 0:
        return redirect('groupMembers', pk=pk)

    chatusers = Check_user_online(request, request.user)
    pendingrequests = ConsistOf.objects.filter(gid=group, confirm=0)
    return render(request, "groups/partial/pending members.html",
                  {'group': group, 'chatusers': chatusers, 'group_consist': group_consist,
                   'pendingrequests': pendingrequests})


# update this to just load the group photos


def groupVideos(request, pk):
    group = get_object_or_404(Groups, id=pk)

    try:
        result = ConsistOf.objects.get(username=request.user, gid=group)
    except ObjectDoesNotExist:
        result = None
    if result and result.confirm == 1:
        group.new = 0
    else:
        group.new = 1
    if result == None:
        group.relation = 0
    else:
        group.relation = 1

    if group.privacy == 'CL' and result == None or result and result.confirm == 0:
        return redirect('groupMembers', pk=pk)

    form = CreateGroupPost(None)
    # check user have the permission to access this group
    # only then user able to access this method
    posts = Status.objects.filter(gid=group).select_related('username').order_by('-time')
    posts = user_post(request, request.user, posts)
    chatusers = Check_user_online(request, request.user)
    try:
        group_consist = ConsistOf.objects.get(gid=group, username=request.user, confirm=1)
    except ObjectDoesNotExist:
        group_consist = None
    videos = Status.objects.none()
    return render(request, "groups/partial/videos.html",
                  {'group': group, 'chatusers': chatusers, 'group_consist': group_consist})


def MemberListActions(request):
    if request.is_ajax() and request.method == 'POST':
        action = request.POST['action']
        gid = request.POST['gid']
        username = request.POST['user']
        group = get_object_or_404(Groups, pk=gid)
        user = get_object_or_404(User, username=username)

        if action == 'Make him admin':
            ConsistOf.objects.filter(gid=group, username=user).update(gadmin=1, confirm=1)
        elif action == 'Remove From group':
            ConsistOf.objects.filter(gid=group, username=user).delete()
        elif action == 'Remove from admin':
            ConsistOf.objects.filter(gid=group, username=user).update(gadmin=0)
        else:
            return JsonResponse(0, safe=False)
        try:
            member = ConsistOf.objects.get(gid=group, username=user, confirm=1)
        except ObjectDoesNotExist:
            member = None
        group_consist = group
        group.new = 0
        try:
            group_consist = ConsistOf.objects.get(gid=group, username=request.user, confirm=1)
        except ObjectDoesNotExist:
            group_consist = None
        try:
            user_isadmin = ConsistOf.objects.get(gid=group, username=user, confirm=1)
        except ObjectDoesNotExist:
            user_isadmin = None
        if user_isadmin is None:
            return JsonResponse(0, safe=False)
        content = render_to_string('groups/partial/custom_button_for_members.html',
                                   {'group_consist': group_consist, 'group': group, 'member': member,
                                    'user_isadmin': user_isadmin}, request)
        return JsonResponse(content, safe=False)


def UploadGroupCover(request):
    if request.is_ajax and request.method == 'POST':
        form = Cover(request.POST, request.FILES)
        gid = request.POST['gid']
        group = get_object_or_404(Groups, id=gid)
        if form.is_valid():
            cover = form.save(commit=False)
            cover.username = request.user
            cover.title = "Posted in "
            cover.gid = group
            ##correct this behavior right now only changing cover for a specific group
            cover.save()
            groupMembers = ConsistOf.objects.filter(gid=group, confirm=1).exclude(username=request.user).select_related(
                'username').values('username')
            for x in groupMembers:
                Notification.objects.create(from_user=request.user, to_user_id=x['username'], gid=group,
                                            notification_type='PG')
            # Notification.objects.create(from_user=request.user,gid=group,notification_type='PG')
            sid = Status.objects.get(id=cover.id)
            Groups.objects.filter(id=gid).update(cover=sid)
            gid = Groups.objects.get(id=gid)
            obj = Status.objects.get(id=cover.id)
            data = {'is_valid': True, 'url': obj.image.url}
        else:
            data = {'is_valid': False}
        return JsonResponse(data, safe=False)


def joinrequest(request):
    if request.is_ajax and request.method == 'POST':
        gid = request.POST['id']
        data = request.POST['data']
        group = get_object_or_404(Groups, id=gid)
        if data == 'Request To join':
            ConsistOf.objects.create(gid=group, username=request.user)
            return JsonResponse("Cancel request", safe=False)
        else:
            ConsistOf.objects.filter(gid=group, username=request.user).delete()
            return JsonResponse("Request To join", safe=False)


def AdminAddQueueMembers(request):
    if request.is_ajax() and request.method == 'POST':
        gid = request.POST['id']
        username = request.POST['username']

        group = get_object_or_404(Groups, id=gid)
        user = get_object_or_404(User, username=username)
        ConsistOf.objects.filter(gid=group, username=user).update(confirm=1)
        return JsonResponse(2, safe=False)


def AddMembers(request):
    if request.is_ajax:
        user = request.POST['search_user']
        gid = request.POST['group_id']
        try:
            user = User.objects.get(username=user)
        except:
            return JsonResponse(0, safe=False)

        gid = get_object_or_404(Groups, id=gid)
        user = User.objects.get(username=user)
        ConsistOf.objects.create(gid=gid, username=user)
        return JsonResponse(1, safe=False)


class UploadProfile(View):
    def get(self, request):
        user = self.request.username
        ProfileObj = Profile.objects.get(username=User.objects.get(username=user))
        return render(self.request, 'user/profile.html', {'ProfileObj': ProfileObj})

    def post(self, request):
        form = Cover(self.request.POST, self.request.FILES)
        if form.is_valid():
            ProfileForm = form.save(commit=False)
            ProfileForm.username = User.objects.get(username=self.request.user.username)
            ProfileForm.title = "Updated Profile"
            ProfileForm.privacy = 'fs'
            status = ProfileForm.save()
            sid = ProfileForm
            friends = giveFriendsUsername(request, request.user)
            for x in friends:
                Notification.objects.create(from_user=request.user, to_user=x, sid=sid, notification_type='P')
            # Notification.objects.create(from_user=request.user,sid=Status.objects.get(id=ProfileForm.id),notification_type='P')
            Profile.objects.filter(username=self.request.user).update(sid=Status.objects.get(id=ProfileForm.id))
            obj = Status.objects.get(id=ProfileForm.id)
            data = {'is_valid': True, 'url': obj.image.url}
        else:
            data = {'is_valid': False}
        return JsonResponse(data)


class UploadCover(View):
    def post(self, request):
        form = Cover(self.request.POST, self.request.FILES)
        if form.is_valid():
            CoverForm = form.save(commit=False)
            CoverForm.username = User.objects.get(username=self.request.user.username)
            CoverForm.title = "Updated Cover"
            CoverForm.privacy = 'fs'
            CoverForm.save()
            Profile.objects.filter(username=self.request.user).update(profileCover=Status.objects.get(id=CoverForm.id))
            obj = Status.objects.get(id=CoverForm.id)
            data = {'is_valid': True, 'url': obj.image.url}
        else:
            data = {'is_valid': False}
        return JsonResponse(data)


def NewGroup(request):
    if request.is_ajax() and request.method == 'POST':
        form = CreateGroup(request.POST)
        if form.is_valid():
            newgroup = form.save(commit=False)
            form.save()
            group = Groups.objects.get(id=newgroup.id)
            ConsistOf.objects.create(username=request.user, gid=group, gadmin=1, confirm=1)
            data = {'is_valid': True, 'gname': group.gname, 'gid': group.id}
            return JsonResponse(data)


# Comment this
def index(request):
    if request.user.is_authenticated:
        return render(request, "friendsbook/Home.html")
    return redirect(views.logout)  # update this functionality


def query(request):
    id = 17
    username = 'nishu'
    query_set = likes = Status.objects.filter(id=12)
    query_set = User.objects.all()
    template_name = 'friendsbook/home.html'
    form = CreateGroup(None)
    return render(request, template_name, {'data': query_set, 'form': form})


def giveFriendsUsername(request, user):
    obj1 = FriendsWith.objects.filter(username=user, confirm_request=2, blocked_status=0).select_related(
        'fusername').values('fusername')
    obj1 = User.objects.filter(id__in=obj1)
    obj2 = FriendsWith.objects.filter(fusername=user, confirm_request=2, blocked_status=0).select_related(
        'username').values('username')
    obj2 = User.objects.filter(id__in=obj2)
    obj = obj1 | obj2
    return obj


def create_post(request):
    if request.method == "POST":
        form = CreatePost(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.username = User.objects.get(username=request.user.username)
            post = form.save()
            sid = Status.objects.get(id=post.id)
            friends = giveFriendsUsername(request, request.user)
            for x in friends:
                Notification.objects.create(from_user=request.user, to_user=x, sid=sid, notification_type='P')

            return redirect('index')
    else:
        form = CreatePost(None)
    return render(request, "uposts/post_create.html", {'form': form})


Friends_Per_Page = 5


def LoadFriendsListViaAjax(request):
    page = request.GET.get('page')
    fname = request.GET.get('search_user')
    # Profile.objects.filter(Q(fname__istartswith=fname) | Q(lname__istartswith=fname)).select_related('username').select_related('sid')

    all_friends = Profile.objects.filter(Q(fname__istartswith=fname) | Q(lname__istartswith=fname)).select_related(
        'username').select_related('sid')
    context = friends_list(self.request, self.request.user.username, context)

    addfriends_list = list()
    searched_by = self.request.user.username
    for x in all_friends:
        if str(x.username) == searched_by:
            addfriends_list.append(-1)
        else:
            user = searched_by
            fuser = x.username
            user_obj = User.objects.get(username=user)
            fuser_obj = User.objects.get(username=fuser)
            addfriends_list.append(friendship(user_obj, fuser_obj))
    all_friends = zip(all_friends, addfriends_list)
    paginator = Paginator(all_friends, Friends_Per_Page)

    try:
        friends = paginator.page(page)
    except PageNotAnInteger:
        return HttpResponseBadRequest()
    except EmptyPage:
        friends = []
    if (len(friends) == 0):
        return JsonResponse(0, safe=False)

    content = render_to_string('Ajax_load_SearchFriendList.html', {'data': friends}, request)
    return JsonResponse(content, safe=False)


def SearchGroup(request, val):
    return Groups.objects.filter(Q(gname__istartswith=val))


def combineFriendshipDetailwithUsers(request, users):
    addfriends_list = list()
    searched_by = request.user.username
    for x in users:
        if str(x.username) == searched_by:
            addfriends_list.append(-1)
        else:
            user = searched_by
            fuser = x.username
            user_obj = User.objects.get(username=user)
            fuser_obj = User.objects.get(username=fuser)
            addfriends_list.append(friendship(user_obj, fuser_obj))
    return zip(users, addfriends_list)


def advanceSearch(request):
    if request.method == 'GET':
        # form=advanceSearchForm(request.GET)

        name = request.GET.get('name')
        # InstituteName=request.GET.get('InstituteName')
        InstituteName = request.GET.get('InstituteName')
        courseName = request.GET.get('courseName')
        profile = request.GET.get('profile')
        location = request.GET.get('location')

        users = Profile.objects.filter(Q(fname__istartswith=name) | Q(lname__istartswith=name)).select_related(
            'username').select_related('sid')
        usernamesEducation = Education.objects.filter(
            Q(institute_name__istartswith=InstituteName) & Q(course_class__istartswith=courseName)).values('username')
        users1 = Profile.objects.filter(username__in=usernamesEducation)
        usernamesWorking = Working.objects.filter(
            Q(profile__istartswith=profile) & Q(location__istartswith=location)).values('username')
        users2 = Profile.objects.filter(username__in=usernamesWorking)
        username = users1 & users2
        users = users & username

        users = combineFriendshipDetailwithUsers(request, users)
        groups = SearchGroup(request, name)
        form = advanceSearchForm(request.GET)
        return render(request, 'user/advance_search_user.html', {'data': users, 'sgroups': groups, 'form': form})


class FriendsView(generic.ListView):  ###print friendlist of user here
    template_name = 'user/search_user.html'
    context_object_name = 'data'

    def get_queryset(self):
        if self.request.method == "GET":
            fname = self.request.GET.get('search_user')
            searchVal = fname
            return Profile.objects.filter(Q(fname__istartswith=fname) | Q(lname__istartswith=fname)).select_related(
                'username').select_related('sid')

    def get_context_data(self, **kwargs):
        context = super(FriendsView, self).get_context_data(**kwargs)
        context['sgroups'] = SearchGroup(self.request, self.request.GET.get('search_user'))

        context['chatusers'] = Check_user_online(self.request, self.request.user)
        context['newGroupForm'] = CreateGroup(None)

        context['groups'] = group_list(self.request)
        context['advanceSearchForm'] = advanceSearchForm()

        context = friends_list(self.request, self.request.user.username, context)
        return context

def UserProfile(request, slug):
    profile = Profile.objects.get(slug=slug)
    chatusers = Check_user_online(request, profile.username)
    friends_suggestion = FriendsOfFriends(request, profile.username)
    tempuser = User.objects.filter(username=profile.username)
    workprofile = Working.objects.filter(username=profile.username).order_by('-WorkingFrom')[0:1]
    educationprofile = Education.objects.filter(username=profile.username).order_by('-date')[0:1]
    for x in tempuser:
        x.status = 'Online' if hasattr(tempuser, 'logged_in_user') else 'Offline'

    y = friendship(request.user, profile.username)
    privacy = 'NoConnection'
    for x in chatusers:
        if str(request.user.username) == str(x.username):
            privacy = 'fs'
    friends_suggestion = friends_suggestion.exclude(username=User.objects.get(username=profile.username))
    if request.user == profile.username:
        posts = user_post(request, request.user, GetUserPosts(request))
        privacy = 'NoNeed'
    elif request.user in friends_suggestion and privacy != 'fs':
        privacy = 'fsofs'
    # check all conditions for all privacy
    PusersFriends = Check_user_online(request, profile.username)
    LoggedInUserFriends = Check_user_online(request, request.user)
    if privacy == 'fsofs':
        commonFriends = PusersFriends & LoggedInUserFriends

        CommonFriendsPosts = Status.objects.filter(Q(username__in=commonFriends, gid__isnull=True)).exclude(
            privacy='me').exclude(privacy='fs')
        UserPostWithPrivacyPublic = Status.objects.filter(username=profile.username, gid__isnull=True).exclude(
            privacy='me').exclude(privacy='fs')
        LoggedInUserPosts = Status.objects.filter(username=request.user, gid__isnull=True).exclude(
            privacy='me').exclude(privacy='fs')
        PuserFriendsWithoutCommon = Status.objects.filter(username__in=PusersFriends, gid__isnull=True, privacy='Pbc')
        posts = CommonFriendsPosts | PuserFriendsWithoutCommon | LoggedInUserPosts | UserPostWithPrivacyPublic


    elif privacy == 'fs':

        # chatusers=Check_user_online(request,profile.username)
        commonFriends = PusersFriends & LoggedInUserFriends
        mutualFriendsPosts = Status.objects.filter(username__in=commonFriends, gid__isnull=True).exclude(
            privacy='me').order_by('-time')
        PuserFriendsPosts = Status.objects.filter(username__in=PusersFriends, gid__isnull=True).exclude(
            privacy='me').exclude(privacy='fs').order_by('-time')
        LoggedInUserPosts = Status.objects.filter(username=request.user, gid__isnull=True).exclude(
            privacy='me').order_by('-time')
        PuserPosts = Status.objects.filter(username=profile.username, gid__isnull=True).exclude(privacy='me')
        posts = LoggedInUserPosts | PuserFriendsPosts | mutualFriendsPosts | PuserPosts
    elif privacy == 'NoConnection':
        # define some post methods here
        userposts = Status.objects.filter(username=profile.username, gid__isnull=True, privacy='Pbc').select_related(
            'username').order_by('time')
        FriendsPostsWithPublicPrivacy = Status.objects.filter(username__in=PusersFriends, gid__isnull=True,
                                                              privacy='Pbc')
        posts = userposts | FriendsPostsWithPublicPrivacy

    # group posts a users can see on anyone profile
    # common groups
    PuserGroupPostWithClosedPrivacy = ConsistOf.objects.filter(username=profile.username, confirm=1).values('gid')
    LoggedInUserGroupsWithClosedPrivacy = ConsistOf.objects.filter(username=request.user, confirm=1).values('gid')
    commonGroups = PuserGroupPostWithClosedPrivacy & LoggedInUserGroupsWithClosedPrivacy
    PuserGroupPost = Status.objects.filter(gid__in=commonGroups, username=profile.username).order_by('-time')
    # PuserGroupWithOpenPrivacy=ConsistOf.objects.filter(username=profile.username)
    # PuserGroupWithOpenPrivacy=ConsistOf.objects.none().select_related('gid').values('gid')
    PuserGroupsWithOpenPrivacy = Groups.objects.filter(id__in=PuserGroupPostWithClosedPrivacy, privacy='OP').values(
        'id')

    PuserGroupPostWithOpenPrivacy = Status.objects.filter(username=profile.username,
                                                          gid__in=PuserGroupsWithOpenPrivacy).order_by('-time')
    posts = posts | PuserGroupPost | PuserGroupPostWithOpenPrivacy
    # paginator
    all_posts = posts
    paginator = Paginator(all_posts, POSTS_NUM_PAGES)
    posts = paginator.page(1)

    posts = user_post(request, profile.username, posts)

    chatusers = Check_user_online(request,
                                  request.user)  # define herebecause it was giving me searched user chatmembers
    userPartOfGroups = ConsistOf.objects.filter(username=profile.username, confirm=1)

    return render(request, 'user/profile.html',
                  {'User': profile, 'page': 1, 'posts': posts, 'y': y, 'chatusers': chatusers,
                   'userPartOfGroups': userPartOfGroups, 'workprofile': workprofile,
                   'educationprofile': educationprofile})


def UserFriendsList(request, slug):
    profile = Profile.objects.get(slug=slug)
    chatusers = Check_user_online(request, profile.username)
    friends_suggestion = FriendsOfFriends(request, request.user)
    tempuser = User.objects.filter(username=profile.username)
    for x in tempuser:
        x.status = 'Online' if hasattr(tempuser, 'logged_in_user') else 'Offline'
    y = friendship(request.user, profile.username)

    friends_list = Profile.objects.filter(username__in=chatusers)
    for x in friends_list:
        if str(x.username) == request.user:
            x.y = -1
        else:
            user = request.user
            fuser = x.username
            user_obj = User.objects.get(username=user)
            fuser_obj = User.objects.get(username=fuser)
            x.y = friendship(user_obj, fuser_obj)

    return render(request, 'user/partial/friends_list.html',
                  {'User': profile, 'y': y, 'chatusers': chatusers, 'friends_list': friends_list})


def UserPhotos(request, slug):
    profile = Profile.objects.get(slug=slug)
    chatusers = Check_user_online(request, profile.username)
    friends_suggestion = FriendsOfFriends(request, request.user)
    tempuser = User.objects.filter(username=profile.username)
    for x in tempuser:
        x.status = 'Online' if hasattr(tempuser, 'logged_in_user') else 'Offline'
    y = friendship(request.user, profile.username)

    photo_albums = Status.objects.filter(username=profile.username)
    return render(request, 'user/partial/photo_frame.html',
                  {'User': profile, 'y': y, 'chatusers': chatusers, 'photo_albums': photo_albums})


def UserProfileEdit(request, slug):
    profile = Profile.objects.get(slug=slug)
    chatusers = Check_user_online(request, profile.username)
    friends_suggestion = FriendsOfFriends(request, request.user)
    tempuser = User.objects.filter(username=profile.username)
    for x in tempuser:
        x.status = 'Online' if hasattr(tempuser, 'logged_in_user') else 'Offline'
    y = friendship(request.user, profile.username)

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(request.path_info)
        else:
            return render(request, 'user/partial/settings.html',
                          {'User': profile, 'y': y, 'chatusers': chatusers, 'form': form})
    else:
        form = EditProfileForm(instance=request.user.profile)
        return render(request, 'user/partial/settings.html',
                      {'User': profile, 'y': y, 'chatusers': chatusers, 'form': form})


def UserChangePassword(request, slug):
    profile = Profile.objects.get(slug=slug)
    chatusers = Check_user_online(request, profile.username)
    friends_suggestion = FriendsOfFriends(request, request.user)
    tempuser = User.objects.filter(username=profile.username)
    y = friendship(request.user, profile.username)

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data.get('new_password')
            user = request.user
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            return render(request, 'user/partial/password.html',
                          {'User': profile, 'y': y, 'chatusers': chatusers, 'form': form, 'message': 1})
        else:
            return render(request, 'user/partial/password.html',
                          {'User': profile, 'y': y, 'chatusers': chatusers, 'form': form})

    else:

        form = ChangePasswordForm(instance=request.user)
        return render(request, 'user/partial/password.html',
                      {'User': profile, 'y': y, 'chatusers': chatusers, 'form': form})


def liveSearch(request):
    if request.is_ajax():
        fname = request.GET.get('search', None)
        obj = Profile.objects.filter(Q(fname__istartswith=fname)).select_related('username').select_related('sid')
        data = serializers.serialize('json', obj, use_natural_foreign_keys=True)
        return JsonResponse(data, safe=False)


def validate_username(request):
    username = request.GET.get('username', None)
    data = {
        'is_taken': User.objects.filter(username__iexact=username).exists()
    }
    return JsonResponse(data)


# using ajax to like a post
def like(request):
    if request.is_ajax():
        username = request.user.username
        id = request.POST['id']
        type = request.POST['type']
        if type == "post_like":
            check = StatusLikes.objects.filter(username=User.objects.get(username=username)).filter(
                sid=Status.objects.get(id=id))
            likes = Status.objects.get(id=id).likes
            status = Status.objects.get(id=id)
            if not check.exists():
                likes = likes + 1
                Status.objects.filter(id=id).update(likes=likes)
                if status.username != request.user:
                    Notification.objects.create(from_user=request.user, to_user=status.username, sid=status,
                                                notification_type='L')
                like = StatusLikes(username=User.objects.get(username=username), sid=Status.objects.get(id=id))
                like.save()
            else:
                likes = likes - 1
                Status.objects.filter(id=id).update(likes=likes)
                if status.username != request.user:
                    Notification.objects.get(from_user=request.user, to_user=status.username, sid=status,
                                             notification_type='L').delete()
                StatusLikes.objects.filter(username=User.objects.get(username=username),
                                           sid=Status.objects.get(id=id)).delete()
            return HttpResponse(likes)
        if type == "Comment_like":
            check = CommentLikes.objects.filter(username=User.objects.get(username=username)).filter(
                cid=Comment.objects.get(id=id))
            likes = Comment.objects.get(id=id).likes
            comment = Comment.objects.get(id=id)
            if not check.exists():
                likes = likes + 1
                Comment.objects.filter(id=id).update(likes=likes)
                if request.user != comment.username:
                    Notification.objects.create(from_user=request.user, to_user=comment.username, sid=comment.sid,
                                                notification_type='CL')
                like = CommentLikes(username=User.objects.get(username=username), cid=Comment.objects.get(id=id))

                like.save()
            else:
                likes = likes - 1
                Comment.objects.filter(id=id).update(likes=likes)

                if request.user != comment.username:
                    Notification.objects.create(from_user=request.user, to_user=comment.username, sid=comment.sid,
                                                notification_type='CL').delete()
                CommentLikes.objects.filter(username=User.objects.get(username=username),
                                            cid=Comment.objects.get(id=id)).delete()
            return HttpResponse(likes)


# ajax
def deleteCommentPost(request):
    if request.is_ajax():
        id = request.POST['id']
        type = request.POST['type']
        if type == 'delete_comment':
            Comment.objects.get(id=id).delete()
        if type == 'delete_status':
            Status.objects.get(id=id).delete()
        response = 1
        return JsonResponse(response, safe=False)


# ajax function

def Messenger_Chatting(request, slug1, slug2):
    profile1 = Profile.objects.get(slug=slug1)
    profile2 = Profile.objects.get(slug=slug2)
    user_obj = User.objects.get(username=request.user.username)
    fuser_obj = User.objects.get(username=profile2.username)
    friendship = FriendsWith.objects.filter(
        Q(username=user_obj, fusername=fuser_obj, confirm_request=2, blocked_status=0) | Q(username=fuser_obj,
                                                                                           fusername=user_obj,
                                                                                           confirm_request=2,
                                                                                           blocked_status=0))
    if user_obj != profile1.username or not friendship.exists():
        return HttpResponse("Something Fishy is going on")
    read_messages = Message.objects.filter(username=fuser_obj, fusername=user_obj, is_read=False).update(is_read=True)
    msg_obj = Message.objects.filter(
        Q(username=user_obj, fusername=fuser_obj) | Q(username=fuser_obj, fusername=user_obj)).select_related(
        'username').select_related('fusername').order_by('time')

    users = Check_user_online(request, request.user)
    form = ChattingForm(None)
    return render(request, 'chat/messenger.html',
                  {'msg_obj': msg_obj, 'chatusers': users, 'userProfile': profile1, 'fuser_obj': fuser_obj,
                   'form': form})


def Message_received(request):
    if request.is_ajax() and request.method == 'POST':
        fuser_obj = User.objects.get(username=request.POST['fusername'])
        user_obj = request.user
        # clean this data
        text = request.POST['text']
        friendship = FriendsWith.objects.filter(
            Q(username=user_obj, fusername=fuser_obj, confirm_request=2, blocked_status=0) | Q(username=fuser_obj,
                                                                                               fusername=user_obj,
                                                                                               confirm_request=2,
                                                                                               blocked_status=0))
        if friendship.exists():
            obj = Message.objects.create(username=request.user, fusername=fuser_obj, text=text)
            content = render_to_string('chat/partials/single_message.html', {'x': obj, 'user': request.user}, request)
            return JsonResponse(content, safe=False)
    return JsonResponse(0, safe=False)


def user_messages(request):
    if request.is_ajax():
        user = request.user.username
        fuser = request.GET.get('fuser', None)
        user_obj = User.objects.get(username=user)
        fuser_obj = User.objects.get(username=fuser)
        msg_obj = Message.objects.filter(Q(username=user_obj, fusername=fuser_obj)
                                         | Q(username=fuser_obj, fusername=user_obj)).select_related('username')
        msg_list = list(msg_obj.values())
        data = serializers.serialize('json', msg_obj, use_natural_foreign_keys=True)
        return JsonResponse(data, safe=False)


# define
# 0-send request
# 1-cancel request
# 2- confirm request sent by user
# 3 unfriends( means already friends)

def AddFriend(request):
    if request.is_ajax() and request.method == 'POST':
        fuser = request.POST['fuser']
        type = request.POST['type']
        user_obj = User.objects.get(username=request.user)
        fuser_obj = User.objects.get(username=fuser)
        ##check again these conditions to make it more secure and reliable
        # not completed
        if request.user == fuser:  # this can't happen.Only by some inspect element tools
            return JsonResponse(0, safe=False)
        if type == 'Send':
            # check if relationship already exists between users
            obj = FriendsWith.objects.filter(
                Q(username=user_obj, fusername=fuser_obj) | Q(username=fuser_obj, fusername=user_obj))
            if obj.exists():
                return JsonResponse(0, safe=False)
            FriendsWith.objects.create(username=user_obj, fusername=fuser_obj)
            Notification.objects.create(from_user=user_obj, to_user=fuser_obj, notification_type='SR')
        elif type == 'Delete' or type == 'Unfriend' or type == 'Cancel':
            # write code to update te result
            FriendsWith.objects.filter(
                Q(username=user_obj, fusername=fuser_obj) | Q(username=fuser_obj, fusername=user_obj)).delete()
        elif type == 'Confirm':
            FriendsWith.objects.filter(
                Q(username=user_obj, fusername=fuser_obj) | Q(username=fuser_obj, fusername=user_obj)).update(
                confirm_request=2)
            Notification.objects.create(from_user=user_obj, to_user=fuser_obj, notification_type='CR')
        else:
            return JsonResponse(0, safe=False)
        return JsonResponse(1, safe=False)


def Comments(request):
    if request.is_ajax():
        if request.method == "POST":
            user = request.user
            sid = request.POST['Status']
            text = request.POST['post']
            sid = Status.objects.get(id=sid)
            comment = Comment.objects.create(username=user, text=text, sid=sid)
            if request.user is not sid.username:
                LoggedInUser = get_object_or_404(User, pk=request.user.pk)
                friends_obj = get_object_or_404(User, pk=sid.username.pk)
                # Notification.objects.create(from_user=request.user,to_user=friends_obj,sid=sid,notification_type='P')
                if request.user != friends_obj:
                    Notification.objects.create(from_user=request.user, to_user=friends_obj, sid=sid,
                                                notification_type='C')
            # Notification.objects.create(from_user=LoggedInUser,to_user_id=sid.username,notification_type='C')
            noOflikesonComment = CommentLikes.objects.filter(cid=comment.id)
            likes = noOflikesonComment.count()
            jsonobj = render_to_string('uposts/partials/comment.html', {'comment': comment, 'likes': likes}, request)
            return JsonResponse(jsonobj, safe=False)
        else:
            sid = request.GET.get('sid', None)
            comments = Comment.objects.filter(sid=Status.objects.get(id=sid)).select_related('username')
            for x in comments:
                x.likes = CommentLikes.objects.filter(cid=x.id).count()
                x.is_like = CommentLikes.objects.filter(cid=x.id, username=request.user).count()

            jsonobj = render_to_string('uposts/partials/comments.html', {'comments': comments}, request)
            return JsonResponse(jsonobj, safe=False)
    # below methods are not working? because of some unknown issues
    # return render(request, 'uposts/partials/comments.html',{'comments': comments})
    return fishy(request)


def EditComments(request):
    if request.is_ajax() and request.method == 'POST':
        # do validations that user is the owner of comment or not
        cid = request.POST['cid']
        text = request.POST['post']
        if not text:
            return JsonResponse(0, safe=False)
        try:
            comment = Comment.objects.get(id=cid, username=request.user)
        except ObjectDoesNotExist:
            comment = None
            return JsonResponse(0, safe=False)
        Comment.objects.filter(id=cid, username=request.user).update(text=text)
        comment = Comment.objects.get(id=cid, username=request.user)
        comment.likes = CommentLikes.objects.filter(cid=cid).count()
        data = render_to_string('uposts/partials/editComment.html', {'comment': comment}, request)
        return JsonResponse(data, safe=False)
    return fishy(request)


def get_contifications(request):
    if request.is_ajax():
        # Notification.objects.filter(is_read=False).update(is_read=True)
        chatusers = Check_user_online(request, request.user)
        IndividualNotifications = Notification.objects.none()
        for x in chatusers:
            IndividualNotifications = IndividualNotifications | Notification.objects.filter(from_user=x,
                                                                                            to_user=request.user,
                                                                                            is_read=False)
        PostNotification = Notification.objects.none()
        for x in chatusers:
            PostNotification = PostNotification | Notification.objects.filter(from_user=x, to_user__isnull=True,
                                                                              is_read=False)
        notifications = ((IndividualNotifications | PostNotification) | Notification.objects.filter(
            to_user=request.user, is_read=False))[:4]
        for notification in notifications:
            notification.is_read = True
            notification.save()
        data = render_to_string('notification/last_notifications.html', {'notifications': notifications}, request)
        return JsonResponse(data, safe=False)
    else:
        chatusers = Check_user_online(request, request.user)
        IndividualNotifications = Notification.objects.none()
        for x in chatusers:
            IndividualNotifications = IndividualNotifications | Notification.objects.filter(from_user=x,
                                                                                            to_user=request.user)
        PostNotification = Notification.objects.none()
        for x in chatusers:
            PostNotification = PostNotification | Notification.objects.filter(from_user=x, to_user__isnull=True)

        notifications = (IndividualNotifications | PostNotification | Notification.objects.filter(to_user=request.user,
                                                                                                  is_read=False)).select_related(
            'from_user')
        return render(request, "notification/notifications.html", {'notifications': notifications})

    return JsonResponse(1, safe=False)


def check_contification(request):
    if request.is_ajax():
        chatusers = Check_user_online(request, request.user)
        IndividualNotifications = Notification.objects.none()
        for x in chatusers:
            IndividualNotifications = IndividualNotifications | Notification.objects.filter(from_user=x,
                                                                                            to_user=request.user,
                                                                                            is_read=False)
        PostNotification = Notification.objects.none()
        for x in chatusers:
            PostNotification = PostNotification | Notification.objects.filter(from_user=x, to_user__isnull=True,
                                                                              is_read=False)

        notifications = (IndividualNotifications | PostNotification) | Notification.objects.filter(to_user=request.user,
                                                                                                   is_read=False)
        data = len(notifications)
        return JsonResponse(data, safe=False)


def WhoLikedStatus(request):
    if request.is_ajax():
        id = request.GET.get('id')
        PersonNames = StatusLikes.objects.filter(sid=Status.objects.get(id=id))
        content = render_to_string('uposts/partials/PersonLikedPosts.html', {'PersonLikedPosts': PersonNames}, request)
        return JsonResponse(content, safe=False)


def WhoLikedComment(request):
    if request.is_ajax():
        id = request.GET.get('id')
        PersonNames = CommentLikes.objects.filter(cid=Comment.objects.get(id=id))
        content = render_to_string('uposts/partials/PersonLikedPosts.html', {'PersonLikedPosts': PersonNames}, request)
        return JsonResponse(content, safe=False)


def autocompleteforGroup(request):
    if request.is_ajax():
        search = request.GET.get('val')
        return JsonResponse(0, safe=False)

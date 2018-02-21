from django.contrib.auth.decorators import login_required
from django.contrib import admin
from django.urls import path,include
from django.conf.urls import url
from django.shortcuts import HttpResponse
from . import views
from django.contrib.auth import views as auth_views



urlpatterns = [
    path(r'login/', auth_views.login,{'template_name':"user/login.html"}, name='login'),
    path('logout/', views.logout, name='logout'),
    path('signup/', views.RegistrationView.as_view(), name='signup'),
    path('',login_required(views.home),name='index'),
    #path('secret_place/',views.index,name='index1'),
    #going to comment this post url because post list must come in
    url(r'^post/$', login_required(views.home), name='post'),
    url(r'^post/create_post/$',login_required(views.create_post),name='new_post'),
	path('findfriends/', login_required(views.FriendsView.as_view()), name='profiles'),
    url(r'^users/profile/(?P<slug>[\w.@+-]+)/$', login_required(views.FriendView.as_view()), name='profile_info'),
    url(r'^ajax/users/profile/friend_list/$', login_required(views.Timeline_friend_list), name='timeline_friend_list'),
    url(r'^ajax/users/profile/photoframe/$', login_required(views.Timeline_photo_frame), name='timeline_photoframe'),
    url(r'^ajax/users/profile/status/$', login_required(views.Timeline_posts), name='timeline_status'),
    path('ajax/AddFriend/', views.AddFriend, name='add_friend'),
    path('query/', views.query, name='query'),
    url(r'^ajax/validate_username/$', views.validate_username, name='validate_username'),
    url(r'^ajax/liveSearch/$', views.liveSearch, name='liveSearch'),
    url(r'^ajax/like_post/$', views.like, name='post_like'),
    url(r'^ajax/messages/$', views.user_messages, name='user_messages'),
    url(r'^ajax/loadcomment/$', views.Comments, name='loadcomment'),
    url(r'^ajax/deleteCommentPost/$', views.deleteCommentPost, name='deleteCommentPost'),
	url(r'^ajax/UpdateProfile/$',views.UploadProfile.as_view(),name='UpdateProfile'),
    url(r'^ajax/UpdateCover/$',views.UploadCover.as_view(),name='UpdateCover'),
    url(r'^ajax/groupUpdateCover/$',views.UploadGroupCover,name='groupUpdateCover'),
    url(r'^ajax/CreateGroup/$', login_required(views.NewGroup), name='NewGroup'),
    url(r'^chat-room/$', login_required(views.user_list), name='user_list'),
    url(r'^groups/(?P<pk>\d+)$', login_required(views.grouphome), name='GroupsHomepage'),
    url(r'^ajax/groupMembers/$', login_required(views.LoadGroupMembers), name='GroupsMembers'),
    url(r'^ajax/groupPosts/$', login_required(views.LoadGroupPosts), name='GroupsPosts'),
    url(r'^ajax/groupPhotoFrames/$', login_required(views.LoadGroupPhotos), name='Groupsphotos'),
    url(r'^ajax/addnewMembertoGroup/$', login_required(views.AddMembers), name='addgroupmember'),

    url(r'^groups/$', login_required(views.grouphome), name='GroupsHome'),
    #validate_username
]
## learn redirection so that you don't have to use login_required every time

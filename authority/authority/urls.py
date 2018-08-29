from django.conf.urls import url
from django.contrib import admin
from key.views import Key


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^v1/key/$', Key.as_view()),
]

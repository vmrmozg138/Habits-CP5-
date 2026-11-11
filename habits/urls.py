from rest_framework.routers import DefaultRouter

from .apps import HabitsConfig
from .views import HabitViewSet

app_name = HabitsConfig.name

router = DefaultRouter()
router.register("habits", HabitViewSet, basename="habits")

urlpatterns = [] + router.urls

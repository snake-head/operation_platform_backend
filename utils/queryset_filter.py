from django_filters import rest_framework as filters

from apps.course.models import Course, CourseType
from apps.department.models import Department
from apps.knowledge.models import Knowledge
from apps.privilege.models import Privilege
from apps.user.models import UserEntity
from apps.video.models import Video


class VideoFilter(filters.FilterSet):
    videoName_like = filters.CharFilter(field_name='videoName', lookup_expr='contains',
                                        help_text="视频名称，支持模糊查询")
    createdAt_lte = filters.DateTimeFilter(field_name='createdAt', lookup_expr='lte',
                                           help_text="创建时间，查找创建时间小于等于给定时间的视频记录")
    createdAt_gte = filters.DateTimeFilter(field_name='createdAt', lookup_expr='gte',
                                           help_text="创建时间，查找创建时间大于等于给定时间的视频记录")
    lastModifiedAt_lte = filters.DateTimeFilter(field_name='lastModifiedAt', lookup_expr='lte',
                                                help_text="最近修改时间，查找最近修改时间小于等于给定时间的视频记录")
    lastModifiedAt_gte = filters.DateTimeFilter(field_name='lastModifiedAt', lookup_expr='gte',
                                                help_text="最近修改时间，查找最近修改时间大于等于给定时间的视频记录")

    @classmethod
    def filter_for_field(cls, field, field_name, lookup_expr=None):
        extra_kwargs = cls.Meta.extra_kwargs
        filter_class = super().filter_for_field(field, field_name, lookup_expr)
        filter_class.extra['help_text'] = extra_kwargs.get(field_name, {}).get('help_text', "")
        return filter_class

    class Meta:
        model = Video
        fields = [
            'id',
            'videoId',
            'courseId',
            'status'
        ]
        extra_kwargs = {
            'id': {
                'help_text': '数据库主键id，为满足数据库约束而存在，具有唯一性'
            },
            'videoId': {
                'help_text': '视频id，具有唯一性，业务上更常用，也更具有解释性'
            },
            'courseId': {
                'help_text': '视频所属的课程id'
            },
            'status': {
                'help_text': """
                视频目前的状态，有以下几种可选值：
                - 0: 未知状态
                - 1: 正在上传中
                - 2: 正在转码处理中
                - 3: 准备就绪
            """
            }
        }


class CourseFilter(filters.FilterSet):
    courseName_like = filters.CharFilter(field_name='courseName', lookup_expr='contains',
                                         help_text='课程名称，支持模糊查询')

    @classmethod
    def filter_for_field(cls, field, field_name, lookup_expr=None):
        extra_kwargs = cls.Meta.extra_kwargs
        filter_class = super().filter_for_field(field, field_name, lookup_expr)
        filter_class.extra['help_text'] = extra_kwargs.get(field_name, {}).get('help_text', "")
        return filter_class

    class Meta:
        model = Course
        fields = [
            'id',
            'courseId',
            'courseType',
            'department'
        ]
        extra_kwargs = {
            'id': {
                'help_text': '数据库主键id，为满足数据库约束而存在，具有唯一性'
            },
            'courseId': {
                'help_text': '代表一个课程，具有唯一性'
            },
            'courseType': {
                'help_text': '标识课程属于哪个类别，与CourseType表有关'
            },
            'department': {
                'help_text': '标识课程属于哪个部门，与Department表有关'
            }
        }


class CourseTypeFilter(filters.FilterSet):
    name_like = filters.CharFilter(field_name='name', lookup_expr='contains', help_text='课程类别名，支持模糊查询')

    @classmethod
    def filter_for_field(cls, field, field_name, lookup_expr=None):
        extra_kwargs = cls.Meta.extra_kwargs
        filter_class = super().filter_for_field(field, field_name, lookup_expr)
        filter_class.extra['help_text'] = extra_kwargs.get(field_name, {}).get('help_text', "")
        return filter_class

    class Meta:
        model = CourseType
        fields = [
            'id'
        ]
        extra_kwargs = {
            'id': {
                'help_text': '数据库主键id，为满足数据库约束而存在，具有唯一性'
            },
        }


class DepartmentFilter(filters.FilterSet):
    deptName_like = filters.CharFilter(field_name='deptName', lookup_expr='contains', help_text='部门名称，支持模糊查询')

    @classmethod
    def filter_for_field(cls, field, field_name, lookup_expr=None):
        extra_kwargs = cls.Meta.extra_kwargs
        filter_class = super().filter_for_field(field, field_name, lookup_expr)
        filter_class.extra['help_text'] = extra_kwargs.get(field_name, {}).get('help_text', "")
        return filter_class

    class Meta:
        model = Department
        fields = [
            'id',
            'deptCode'
        ]
        extra_kwargs = {
            'id': {
                'help_text': '数据库主键id，为满足数据库约束而存在，具有唯一性'
            },
            'deptCode': {
                'help_text': '代表一个部门，具有唯一性'
            },
        }


class KnowledgeFilter(filters.FilterSet):
    pageName_like = filters.CharFilter(field_name='pageName', lookup_expr='contains', help_text='词条名称，支持模糊查询')

    @classmethod
    def filter_for_field(cls, field, field_name, lookup_expr=None):
        extra_kwargs = cls.Meta.extra_kwargs
        filter_class = super().filter_for_field(field, field_name, lookup_expr)
        filter_class.extra['help_text'] = extra_kwargs.get(field_name, {}).get('help_text', "")
        return filter_class

    class Meta:
        model = Knowledge
        fields = [
            'pageName',
            'courseTypeId'
        ]
        extra_kwargs = {
            'pageName': {
                'help_text': '词条名称，具有唯一性'
            },
            'courseTypeId': {
                'help_text': '该词条所属的分类，具有唯一性'
            },
        }


class PrivilegeFilter(filters.FilterSet):

    @classmethod
    def filter_for_field(cls, field, field_name, lookup_expr=None):
        extra_kwargs = cls.Meta.extra_kwargs
        filter_class = super().filter_for_field(field, field_name, lookup_expr)
        filter_class.extra['help_text'] = extra_kwargs.get(field_name, {}).get('help_text', "")
        return filter_class

    class Meta:
        model = Privilege
        fields = [
            'id',
            'privilegeCode'
        ]
        extra_kwargs = {
            'id': {
                'help_text': '数据库主键id，为满足数据库约束而存在，具有唯一性'
            },
            'privilegeCode': {
                'help_text': '具有唯一性，代表一种权限'
            }
        }


class UserFilter(filters.FilterSet):
    username_like = filters.CharFilter(field_name='username', lookup_expr='contains', help_text="用户名，支持模糊查询")

    @classmethod
    def filter_for_field(cls, field, field_name, lookup_expr=None):
        extra_kwargs = cls.Meta.extra_kwargs
        filter_class = super().filter_for_field(field, field_name, lookup_expr)
        filter_class.extra['help_text'] = extra_kwargs.get(field_name, {}).get('help_text', "")
        return filter_class

    class Meta:
        model = UserEntity
        fields = [
            'id',
            'uid',
            'email',
            'sex',
            'privilege',
            'department',
            'phoneNumber'
        ]
        extra_kwargs = {
            'id': {
                'help_text': '数据库主键id，为满足数据库约束而存在，具有唯一性'
            },
            'uid': {
                'help_text': '视频id，具有唯一性，业务上更常用'
            },
            'email': {
                'help_text': '用户电子邮箱地址'
            },
            'sex': {
                'help_text': '用户性别'
            },
            'privilege': {
                'help_text': '描述用户所具有的权限，与Privilege表相关'
            },
            'department': {
                'help_text': '描述用户所属部门信息，与Department表相关'
            },
            'phoneNumber': {
                'help_text': '用户电话号码'
            }
        }

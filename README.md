# 手术视频示教系统

本仓库是系统的后端部分，前端部分在[这里](https://github.com/Sddft97/coelomoscope-video-player)。

## 使用方式

### 配置环境

建议创建虚拟环境后使用。
使用python自带的`venv`模块，其具体使用说明可参考[官方文档](https://docs.python.org/zh-cn/3/tutorial/venv.html)。

进入虚拟环境后，安装所需依赖。

```shell
pip install -r requirements.txt
```

> 项目使用的python版本为3.8.9

### 启动项目

后端项目使用`Django`编写，采用`Django`项目的启动方式即可。

```shell
python manage.py runserver # 启动项目，默认监听3000端口
```

### 配置文件与环境变量

项目提供了两套配置文件，即`dev`版本和`prod`版本，默认情况下会加载`dev`版本的配置，可以通过配置环境变量改变这一行为。

* 配置环境变量`CURRENT_ENV=dev`则加载`dev`版本配置
* 配置环境变量`CURRENT_ENV=prod`则加载`prod`版本配置

### 数据库连接

数据库使用MySQL 8.0.15，最好采用MySQL 8版本，未验证MySQL 5版本能否正常工作。

运行项目前需要自行修改配置文件中的数据库相关配置，配置完成后使用Django的数据库工具进行数据库连接和迁移。

```shell
# 按顺序执行以下两条命令
python manage.py makemigrations
python manage.py migrate
```

## 接口文档

项目中提供了4种接口文档，可以根据需求配合使用。
启动项目后，访问如下地址：

* [http://localhost:3000/swagger.yaml](http://localhost:3000/swagger.yaml)
  或者[http://localhost:3000/swagger.json](http://localhost:3000/swagger.json)，直接下载接口的yaml或json格式文档
* [http://localhost:3000/swagger/](http://localhost:3000/swagger/)
  ，swagger文档界面，介绍比较详细，功能比较全面，可以直接在页面里发送请求调用相应的接口，缺点是美观度一般
* [http://localhost:3000/redoc/](http://localhost:3000/redoc/)，redoc文档界面，整体比较清晰美观，介绍比较全面，缺点是不能直接发送请求调用接口，缺少互动性
* [http://localhost:3000/docs/](http://localhost:3000/docs/)，coreapi文档界面，美观度最佳，展示效果好，但是一些接口信息的展示存在错误

## 其他注意事项

### FFmpeg

项目中视频处理的部分大量使用到FFmpeg，因此需要先安装[FFmpeg](https://ffmpeg.org/)工具，安装完成后将其添加到环境变量`path`
中。

<details>
  <summary>对其中文件的说明</summary>

- `.gitignore`: Git版本控制系统的忽略文件列表。
- `manage.py`: Django项目的管理脚本。
- `README.md`: 项目的说明文档。
- `requirements.txt`: 列出了项目所需的Python依赖包。

下面是各个目录的说明：

- `.idea`: 包含用于JetBrains IDE（如PyCharm）的项目配置文件。
- `apps`: 包含Django应用程序的目录。每个应用程序都是一个独立的模块，包含了模型、视图、URL配置等。
  - `course`: 一个名为"course"的应用程序。
  - `department`: 一个名为"department"的应用程序。
  - `privilege`: 一个名为"privilege"的应用程序。
  - `user`: 一个名为"user"的应用程序。
  - `video`: 一个名为"video"的应用程序。

每个应用程序目录的结构相似，包含以下文件和目录：

- `admin.py`: Django的后台管理配置文件。
- `apps.py`: 应用程序的配置文件。
- `models.py`: 应用程序的模型文件，定义数据库模型。
- `tests.py`: 应用程序的测试文件。
- `urls.py`: 应用程序的URL配置文件。
- `views.py`: 应用程序的视图函数文件。
- `migrations`: 包含应用程序的数据库迁移文件。
- `__pycache__`: 包含Python字节码文件。

其他目录的说明：

- `config`: 包含项目的配置文件。
  - `settings_dev.py`: 开发环境的配置文件。
  - `settings_prod.py`: 生产环境的配置文件。

- `operation_platform_backend`: 项目的核心应用程序。
  - `asgi.py`: ASGI服务器配置文件。
  - `settings.py`: 项目的主要配置文件。
  - `urls.py`: 项目的URL配置文件。
  - `wsgi.py`: WSGI服务器配置文件。

- `service`: 包含一些服务模块。
  - `multipart_file_upload.py`: 处理多部分文件上传的模块。

- `utils`: 包含一些工具模块。
  - `exception_handler.py`: 异常处理的模块。
  - `paginator.py`: 分页处理的模块。
  - `queryset_filter.py`: 查询集过滤的模块。
  - `response.py`: 响应处理的模块。
  - `serializer.py`: 序列化处理的模块。

每个模块目录包含一个`__init__.py`文件，使其成为一个Python包。

</details>

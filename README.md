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
  <summary>点击这里展开/折叠内容</summary>
  
  这是可折叠的内容。
  
  可以包含任意的Markdown文本、HTML标签和其他内容。
</details>

# 风控系统

### 安装部署
1. 本机安装并启动 redis， mysql，mongodb
```bash
    # 为了简单可以使用docker安装
    # docker安装文档地址(以ubuntu为例): https://docs.docker.com/install/linux/docker-ce/ubuntu/
    mongo: docker run -d --name mongo -v $HOME/docker_volumes/mongodb:/data/db  -p 27017:27017 mongo:latest
    mysql: docker run -d --name mysql -e MYSQL_ROOT_PASSWORD=root -v $HOME/docker_volumes/mysql:/var/lib/mysql -v $HOME/docker_volumes/conf/mysql:/etc/mysql/conf.d -p 3306:3306 mysql:5.6
    redis: docker run -d --name redis -p 6379:6379  -v $HOME/docker_volumes/redis:/var/lib/redis redis:latest
```

2. 在mysql中创建risk_control库
```bash
    docker exec -it mysql mysql -h 127.0.0.1 -u root -p # 后续需输入密码
    CREATE DATABASE risk_control CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; # 创建数据库时指定编码格式，规避乱码问题
```
3. 安装所需依赖pip install -r requirements.txt
4. 初始化django运行所需的表并创建管理员账户
```bash
    python manage.py makemigrations && python manage.py migrate
    # 创建用户可使用django自带的createsuperuser命令创建，也可以手动创建，详见  其它操作--增加用户
    python manage.py createsuperuser # 后续 依次输入用户名、密码、邮箱 即可创建一个管理员账号
```
5. 启动服务
```bash
    bash start.sh # 以nohup的方式启动服务进程、管理后台、拦截日志消费进程
```


### 后台介绍
1. 名单管理

    为名单型策略提供基础的数据管理功能。
    
    名单数据的维度包括：用户ID、IP、设备号、支付账号、手机号。后续也可以根据自己的需求扩充其他的维度。
    
    名单包含三个方向：黑、白、灰名单
    
    名单必须属于某个项目(用于确定名单的范围)，可以在名单管理-名单项目管理中添加项目。
    
    一条名单型策略完整描述是**A {操作码：在/不在} {XX项目:单选，可选全局} 的 {维度：单选}{方向：黑/白/灰名单}**,示例：A在直播活动的设备白名单

2. 名单型策略

    描述符为**{参数名:单选,假设是“用户ID”} {操作码：在/不在} {XX项目:单选，可选全局} 的 {维度：单选}{方向：黑/白/灰名单}**

    示例：用户ID在红包项目的用户ID黑名单

3. 布尔型策略

    不传阈值的布尔型，描述符为 **{参数名:单选，假设是"账号ID"} {操作码：是/不是} {内置函数：异常用户}**
    示例：账号ID是异常用户

    传阈值的布尔型，描述符为 **{参数名:单选，假设是"账号ID"} {操作码：大于/小于/等于/不等于} {内置函数：历史登录次数} {阈值：170}**
    示例：账号ID历史登录次数大于100
    
    `内置函数`是什么？就是自定义的一些逻辑判断函数，只需要满足要求返回布尔值即可。比如注册时间是否在某个范围以内，当前设备是否是常用设备。

4. 时段频控型策略

    描述符为 **同一 {计数维度:单选，假设是“设备”} 在 {时段：时间跨度} 内限制 {阈值：整数N} 次 某动作**
    示例：同一设备一天内限制登录1000次.
    可是我怎么知道当前已经有多少次呢？这就需要上报，上报后将计数，详见第9条 **数据源管理**

5. 限用户数型

    描述符为 **同一 {计数维度:单选，假设是“设备”} 在 {时段：时间跨度} 内限制 {阈值：整数N} 个用户**
    
    示例：同一设备一天内限制登录1000人

6. 规则管理

    管控原子：命中某条策略后的管控动作，比如拦截...
    把上面2--5中所述的策略原子按照优先级组合起来，由上向下执行，直到命中某条策略，则返回对应策略的管控原子。此模块更多是重交互，完成策略的配置、组合、权重等等

7. 日志管理

    所有命中策略的日志均在此展示，`下一期会基于此日志，开放拦截溯源功能`。

8. 权限配置

    供权限设置使用，精确限定某个用户能看哪些页面的数据。

9. 数据源配置

    示例策略：同一设备一天内限制登录1000次
    那么每次登陆就需要上报一条数据，系统会分类计数，并分类存储。
    存储的名字叫啥？就是此处要配置的数据源。对于此策略，只需要配置数据源，命名为login_uid, 字段包含uid, uid类型是str。然后程序就能根据uid为维度计数，并自动计算指定时间窗口内是否超出指定阈值。

    重要：由于逻辑必然依赖时间信息，为通用且必需字段，timestamp为默认隐含字段，类型是时间戳(精确到秒，整数)

### 调用样例
1. 调用查询服务
                     
    假设存在id为1的规则，则可以通过如下方式查询是否命中策略
```
curl 127.0.0.1:50000/query/ -X POST -d '{"rule_id": "1", "user_id": "10000"}' -H "Content-Type:application/json"
```

2. 调用上报服务

    假设存在名称为test的数据源, 且数据源含有的数据是: {"ip": "string", "user_id": "string", "uid": "string"}
```
curl 127.0.0.1:50000/report/ -X POST -d '{"source": "test", "user_id": "10000", "ip": "127.0.0.1", "uid": "abcabc112333222", "timestamp": 1559049606}' -H "Content-Type:application/json"
```

3. 关于服务拆分

    开源样例中，为了简化安装部署，查询和上报揉进了一个服务。实际场景中，显然读写应该分离。

    1.可以直接此方式部署2份，域名不同，一份用于查询(上报接口不被访问)，一份用于上报(查询接口不被访问)，流量分发在nginx层完成

    2.risk_server.py中修改配置URL_2_HANDLERS，选择您需要的服务接口部署


## 内置函数的扩展
1. 不带阈值的内置函数扩展
    
    以`是否异常用户`内置函数为例  
    代码见 aswan/buildin_funcs/sample.py 中的 is_abnormal 方法
    
2. 带阈值的内置函数布尔型策略扩展

    以`历史登录次数`内置函数为例  
    代码见 aswan/buildin_funcs/sample.py 中的 user_login_count 方法  
    注意：阈值计算不包含在内置函数中进行，控制流详见 aswan/buildin_funcs/base.py
    
## 其它操作

### 增加用户

目前界面上未提供增加用户的功能，因此需手动增加，代码如下:

```python
# coding=utf-8
from django.contrib.auth.models import User

username = 'username'
password = 'password'
email = 'email@momo.com'
first_name = '测'
last_name = '试'
# 普通用户
User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
# 管理员账户
User.objects.create_superuser(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
```

添加完成后，让用户登录，然后管理员配置权限即可。

### 权限管理

目前的模型为针对url的权限控制，可将多个url配置为一个uri组, 然后可以将多个uri组，设置为一个权限组，并可以将权限组赋予个人。

    注: 
    1. uri列表中的uri为相对路径地址(如 /log_manage/audit_log_list/);
    2. 管理员默认拥有所有uri的访问权限。
# 选用精简版的 Python 3.12 镜像，体积小
FROM python:3.12-slim

# 安装 Git，因为我们需要在容器里自动拉取代码
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# 设置容器内的工作目录
WORKDIR /app

# 把你当前目录下的所有代码都复制进容器的 /app 目录
COPY . /app

# 给刚才写的启动脚本赋予执行权限
RUN chmod +x /app/start.sh

# 暴露 Streamlit 的默认端口
EXPOSE 8501

# 容器启动时，执行我们的智能脚本
CMD ["/app/start.sh"]
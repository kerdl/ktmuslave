FROM python:3.10.10-bullseye

# .env file contents
ARG VK_TOKEN=YOUR_VK_BOT_TOKEN_HERE
ARG TG_TOKEN=YOUR_TG_BOT_TOKEN_HERE
ARG VK_ADMIN=YOUR_VK_USER_ID_TO_SEND_ERRORS_IN_PMs_OR_SET_TO_ZERO
ARG ADMIN_CONTACT_MAIL=YOUR@CONTACT.MAIL
ARG KTMUSCRAP_ADDR=127.0.0.1:8080
ARG REDIS_ADDR=127.0.0.1:6379
ARG REDIS_PASSWORD=""

# build options
ARG cwd=/ktmuslave

WORKDIR ${cwd}

# update packages
RUN apt-get -y update

# copy this folder contents to the container
COPY . ${cwd}

# create .env file with secrets
# (this bot doesn't support environment variables, only .env)
RUN echo "\
VK_TOKEN = \"${VK_TOKEN}\"\n\
TG_TOKEN = \"${TG_TOKEN}\"\n\
VK_ADMIN = ${VK_ADMIN}\n\
ADMIN_CONTACT_MAIL = ${ADMIN_CONTACT_MAIL}\n\
KTMUSCRAP_ADDR = \"${KTMUSCRAP_ADDR}\"\n\
REDIS_ADDR = \"${REDIS_ADDR}\"\n\
REDIS_PASSWORD = \"${REDIS_PASSWORD}\"\n" >> .env

RUN cat .env

# install needed pip packages from ./requirements.txt
RUN pip install -r requirements.txt
# run the bot
CMD ["python", "src"]

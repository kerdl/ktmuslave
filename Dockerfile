FROM python:3.12-alpine

# build options
ARG cwd=/ktmuslave
ENV TZ="Europe/Moscow"

WORKDIR ${cwd}

# copy this folder contents to the container
COPY . ${cwd}

# install needed pip packages from ./requirements.txt
RUN pip install -r requirements.txt
# run the bot
CMD ["python", "src"]

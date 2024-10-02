FROM python:3.12-bullseye

# build options
ARG cwd=/ktmuslave

WORKDIR ${cwd}

# update packages
RUN apt-get -y update

# copy this folder contents to the container
COPY . ${cwd}

# install needed pip packages from ./requirements.txt
RUN pip install -r requirements.txt
# run the bot
CMD ["python", "src"]

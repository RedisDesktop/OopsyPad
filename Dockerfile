FROM centos:7


RUN rpm -Uvh http://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
RUN yum -y install python36 python36-pip dos2unix git
RUN yum -y install gcc gcc-c++ make libcurl-devel

# workdir and user
WORKDIR /OopsyPad
# USER 0

COPY . .

# Get breakpad inside container
RUN rm -rf ./3rdparty/breakpad/*
RUN git submodule update --init --recursive

# Install dependencies
RUN dos2unix ./3rdparty/build.sh
RUN ./3rdparty/build.sh

# install OopsyPad
RUN python3 -m pip install .

EXPOSE 8000

RUN dos2unix /OopsyPad/start.sh
ENTRYPOINT ["/bin/sh"]
CMD ["/OopsyPad/start.sh"]

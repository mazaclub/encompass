FROM ubuntu-32bit:14.04
MAINTAINER Rob Nelson <guruvan@maza.club>
ENV BUILDER_VER 1.1

VOLUME ["/opt/wine-electrum/drive_c/encompass"]

RUN apt-get update -y \
     && apt-get install -y software-properties-common curl  wget \
        git python-pip pyqt4-dev-tools zip unzip python-dev \
	python-all python-all-dev debhelper \
     &&	pip install stdeb \
     && apt-get purge -y python-software-properties \
     && apt-get autoclean -y 



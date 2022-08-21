FROM 812206152185.dkr.ecr.us-west-2.amazonaws.com/latch-base:6839-main

# install aics-segmentation and dependencies
RUN python3 -m pip install --upgrade pip wheel setuptools
RUN python3 -m pip install numpy && python3 -m pip install scikit-build
RUN python3 -m pip install aicssegmentation

# if you would like to build from source to access features not covered by the latest release,
# comment the above line that executes "pip install aicssegmentation" and uncomment the below two lines
# RUN apt-get install -y curl unzip git
# RUN git clone https://github.com/AllenCell/aics-segmentation.git && cd aics-segmentation && python3 -m pip install -e .[all]

# the reference folder will be available for data resources
COPY reference /root/reference

# latch internal
RUN python3 -m pip install --upgrade latch
COPY wf /root/wf
ARG tag
ENV FLYTE_INTERNAL_IMAGE $tag
WORKDIR /root

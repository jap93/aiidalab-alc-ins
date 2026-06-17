# Use this for the latest official aiidalab image (Python 3.9)
# FROM aiidalab/full-stack:latest 
# Use this for a ported version of the above running on Python 3.10 
FROM ghcr.io/stfc/alc-ux/base:py310  

#USER root
 
# Install the alc-ux AiiDAlab plugin to the apps folder 
#RUN pip install git+https://github.com/stfc/alc-ux.git#egg=alc-ux --src ${HOME}/apps

#RUN pip install aiidalab_widgets_base --no-cache-dir --no-user

ADD aiidalab-mlip /home/jovyan/apps/aiidalab-mlip
RUN pwd
RUN ls -l
RUN ls -l
RUN pip install -e /home/jovyan/apps/aiidalab-mlip --no-cache-dir --no-user
RUN pip install -e /home/jovyan/apps/aiidalab-mlip/aiida-mlip-phonon --no-cache-dir --no-user
RUN pip install mace-torch --no-cache-dir --no-user

USER ${NB_UID}
WORKDIR ${HOME}


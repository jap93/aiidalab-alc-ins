# Use this for the latest official aiidalab image (Python 3.9)
# FROM aiidalab/full-stack:latest 
# Use this for a ported version of the above running on Python 3.10 
FROM ghcr.io/stfc/alc-ux/base:py310  

USER root
 
# Install the alc-ux AiiDAlab plugin to the apps folder 
#RUN pip install git+https://github.com/stfc/alc-ux.git#egg=alc-ux --src ${HOME}/apps
RUN echo ${PWD} 

COPY --chown=${NB_UID}:${NB_GID} . /home/jovyan/apps/aiidalab-alc-ins
RUN ls -l /home/jovyan/apps/aiidalab-alc-ins
RUN pip install /home/jovyan/apps/aiidalab-alc-ins --no-cache-dir --no-user
RUN pip install git+https://github.com/jap93/aiida-mlip-phonon.git@new --no-cache-dir --no-user
#RUN cd /home/jovyan/apps/aiidalab-alc-ins/aiida-mlip-phonon && pip install . --no-cache-dir --no-user
# mace-torch takes a very long time to download and produces a massive (>10Gn) image. It is possibly
# better to open a terminal and download there.
#RUN pip install mace-torch --no-cache-dir --no-user
RUN pip install git+https://github.com/stfc/aiida-alc-ins.git@py310-0.2 --no-cache-dir --no-user
RUN pip install aiida-workgraph --no-cache-dir --no-user
RUN pip install dftd3 --no-cache-dir --no-user

LABEL org.opencontainers.image.source=https://github.com/jap93/aiidalab-alc-ins

USER ${NB_UID}
WORKDIR ${HOME}

#https://github.com/jap93/aiida-mlip-phonon.git
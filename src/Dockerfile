FROM continuumio/anaconda3
 
WORKDIR /dfre
COPY DFRE4Networking/ /dfre/DFRE4Networking/

RUN apt update && apt upgrade -y && apt install -y aptitude vim 

# Create the image
RUN conda create --name dfre python=3.7 
SHELL ["conda", "run", "-n", "dfre", "/bin/bash", "-c"]
RUN cd DFRE4Networking/src && pip install -r requirements.txt
RUN conda install -y pytorch
RUN conda install -y matplotlib
RUN conda install -y redis
RUN pip install libtmux
RUN apt install -y iputils-ping
RUN apt install -y tmux

# Run commands below in shell script. 
#ENTRYPOINT ["conda","run","-n","dfre","bash","-c"]

# # Run the script
# RUN conda activate dfre
# RUN cd DFRE4Networking/src
# RUN python start_uc.py timeseries






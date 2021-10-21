sudo docker network create -d bridge dfre_network
sudo docker network connect dfre_network ozkan.redis
sudo docker run -d --name dfre_container --network=dfre_network dfre4networking bash -c "while [ 1=1 ]; do sleep 1; done"
sudo docker exec -it dfre_container bash

tmux new -s timeseries




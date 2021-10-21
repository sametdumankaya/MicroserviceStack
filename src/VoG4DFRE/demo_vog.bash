#!/bin/bash

echo ''
echo -e "\e[34m======== Step 1 Convert L1 Graph for Structure Discovery  ==========\e[0m"
python3 DATA/convert_oG.py 
echo ''
echo 'Conversion Complete.'

echo ''
echo -e "\e[34m======== Steps 2 & 3: Subgraph Generation and Labeling  ==========\e[0m"
#matlab.exe -r run_structureDiscovery
echo ''
echo 'Structure discovery finished.'

unweighted_graph='DATA/alertstorm.out'
model='DATA/alertstorm_orderedALL.model'
modelFile='alertstorm_orderedALL.model'
modelTop10='DATA/alertstorm_top10ordered.model'

echo ''
echo -e "\e[34m=============== Step 4: Summary Assembly ===============\e[0m"
echo ''
echo -e "\e[31m=============== TOP 10 structures ===============\e[0m"
head -n 10 $model > $modelTop10
echo 'Computing the encoding cost...'
echo ''
python3 MDL/score.py $unweighted_graph $modelTop10 

echo ''
echo 'Explanation of the above output:'
echo 'L(G,M):  Number of bits to describe the data given a model M.'
echo 'L(M): Number of bits to describe only the model.'
echo 'L(E): Number of bits to describe only the error.'
echo ': M_0 is the zero-model where the graph is encoded as noise (no structure is assumed).'
echo ': M_x is the model of the graph as represented by the top-10 structures.'
echo ''

echo -e "\e[31m========= Greedy selection of structures =========\e[0m"
echo 'Computing the encoding cost...'
echo ''
python3 MDL/greedySearch_nStop.py $unweighted_graph $model 
echo '>> Outputs saved in DATA/. To interpret the structures that are selected, check the file MDL/readme.txt.'
echo ": DATA/heuristicSelection_nStop_ALL_$modelFile has the lines of the $model structures included in the summary."
echo ": DATA/heuristic_Selection_costs_ALL_$modelFile has the encoding cost of the considered model at each time step."
echo ''
echo ''
echo -e "\e[31m========= Final Step: Create VoG L2 Graph, Return Cost to L1 Graph =========\e[0m"
echo ''
python3 /MDL/


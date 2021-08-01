# benders-decomposition-gurobi

Repository contains implementation of Bender Decomposition for classical facility/warehause location problem using Python and Gurobi solver.

Implementation is not intendent to be fast but rather descriptive.

See https://grzegorz-siekaniec.github.io/bits-of-this-bits-of-that/2021/may.html for more details.

## How to run

In order to run application.

1. Go to directory `benders-decomposition/src`
2. Execute:
   ```commandline
   python src/main.py --method standalone data/rk_martin_ex_10_8.json

   ``` 
   to solve the problem using standalone model.
   ```commandline
   python src/main.py --method benders_decomposition data/rk_martin_ex_10_8.json

   ``` 
   to solve the problem using Benders Decomposition.
   
   ```commandline
   python src/main.py --method data/rk_martin_ex_10_8.json

   ``` 
   to solve the problem using both methods.
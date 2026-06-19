import random

# determina qual arquivo de dados usar
# mudar para random.randint(1, 6) para atender requisito
NUM_INPUT = 5

# 8080 para server java
# 5000 para server python
URL = "http://localhost:5000/image"

# mudar para "CGNE" if random.randint(0, 1) == 0 else "CGNR" para atender requisito
ALGORITHM = "CGNE"

TIMEOUT = 180
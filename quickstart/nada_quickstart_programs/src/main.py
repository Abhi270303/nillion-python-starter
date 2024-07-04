from nada_dsl import *

def nada_main():
    # Define parties
    party1 = Party(name="Party1")
    party2 = Party(name="Party2")
    party3 = Party(name="Party3")
    party4 = Party(name="Party4")
    
    # Define secret inputs from different parties
    x = SecretInteger(Input(name="X", party=party1))
    y = SecretInteger(Input(name="Y", party=party2))
    z = SecretInteger(Input(name="Z", party=party3))

    # Calculate the sum of the three secret integers
    total = x + y + z

    # Calculate the average
    average = total // 3

    # Return the average to party4
    return [Output(average, "average_output", party4)]

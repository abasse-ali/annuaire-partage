import os

def deco_console(titre: str, taille: int, options_brutes: list, sous_titre: str = None):
    options = [str(opt) for opt in options_brutes if opt is not None]
    largeur_utile = taille - 4
    
    print("=" * taille)
    if titre == "=== CONSOLE SERVEUR ===":
        print("\033[91m" + f"{titre:^{taille}}" + "\033[0m")
    else:  
        print("\033[92m" + f"{titre:^{taille}}" + "\033[0m")
    print("=" * taille)
    
    if sous_titre:
        print(f"| {sous_titre:<{largeur_utile}} |")
        print(f"| {'-' * largeur_utile} |")
        
    if not options:
        print(f"| {'Aucun':<{largeur_utile}} |")
        print("=" * taille)
        return
    
    max_len = max(len(opt) for opt in options) + 2
    nb_cols = largeur_utile // max_len
    if nb_cols < 1: 
        nb_cols = 1
        max_len = largeur_utile

    for i in range(0, len(options), nb_cols):
        ligne = options[i:i + nb_cols]
        ligne_str = "".join(f"{opt:<{max_len}}" for opt in ligne)
        print(f"| {ligne_str:<{largeur_utile}} |")

    print("=" * taille)

def test_valeur(variable: str) -> str:
    while True:
        valeur = input(f"{variable}* : ").strip()
        if valeur == "":
            print(f"Le {variable} est obligatoire")
            continue
        else:
            break
    return valeur

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
    

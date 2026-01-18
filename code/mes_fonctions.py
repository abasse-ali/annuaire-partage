import os

def deco_console(titre: str, taille: int, options_brutes: list, sous_titre: str = None):
    """
    Affiche un menu ou une liste formatée encadrée dans la console.
    Gère l'affichage en colonnes dynamiques si la liste est longue.
    
    Args:
        titre (str): Titre principal du menu.
        taille (int): Largeur de l'affichage.
        options_brutes (list): Liste des items à afficher.
        sous_titre (str, optional): En-tête interne optionnel.
    """
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
    """
    Demande une saisie utilisateur en boucle jusqu'à ce qu'elle ne soit pas vide.
    
    Args:
        variable (str): Nom du champ à afficher dans le prompt.
        
    Returns:
        str: La valeur saisie validée.
    """
    while True:
        valeur = input(f"{variable}* : ").strip()
        if valeur == "":
            print(f"Le {variable} est obligatoire")
            continue
        else:
            break
    return valeur

def clear_console():
    """
    Efface le contenu de la console de manière compatible Windows (cls) et Linux/Mac (clear).
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    

import re
import os
from hashlib import sha512
from getpass import getpass
import connexion_ClientServeur as reseau

"""
Présentation des "status" :
    Succès :
        - 200 (Succès) : Connexion réussie, contact ajouté, liste de contacts récupérée.
        - 201 (Créé) : Uniquement lors de la Création de Compte.
        
    Erreur :
        - 400 (Mauvaise Requête) : L'utilisateur a oublié de taper le Nom ou le Prénom d'un contact, ou l'action demandée n'existe pas.
        - 401 (Non Autorisé) : Mauvais mot de passe lors du login, ou tentative d'ajout de contact sans être connecté.
        - 403 (Interdit) : C'est le code des Permissions. Si un utilisateur essaie de voir l'annuaire d'un autre mais que celui ci ne lui a pas donné la permission, le serveur renvoie 403.
        - 404 (Non Trouvé) : Utilisé si on cherche l'annuaire d'un utilisateur qui n'existe pas (le fichier .csv est introuvable).
        - 409 (Conflit) : Utilisé lors de la création de compte si le nom d'utilisateur existe déjà. On ne peut pas écraser un compte existant.
        - 500 (Erreur Interne) : Le fichier de réponse JSON est vide, illisible, ou le client n'est pas connecté via connecter_serveur().

Client -> Serveur (Requete) :
    PDU :
        {
            "action": "NOM_DE_L_ACTION",
            "demandeur": "Nom_Utilisateur_Connecté",
            "corps":{
                "parametre_1": "valeur",
                "parametre_2": "valeur"
            }
        }
        
Serveur -> Client (Reponse) :
    PDU :
        {
            "status": code_status,
            "message": "Texte explicatif pour l'humain",
            "donnee": [ ... ]
        }
"""
def deco_console(titre: str, taille: int, options_brutes: list, sous_titre: str = None):
    options = [str(opt) for opt in options_brutes if opt is not None]
    largeur_utile = taille - 4

    print("\033[92m" + f"{"=== ANNUAIRE PARTAGE ===":^{taille}}" + "\033[0m")
    print("=" * taille)
    print(f"{titre:^{taille}}")
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

def menu_modif(prenom, nom, tel, adresse, mail):
    while True:
        clear_console()
        titre = f"--- MODIFICATION ({prenom} {nom}) ---"
        taille = 60
        options = [
            f"1. Numéro de téléphone (Actuel: {tel})",
            f"2. Adresse postal (Actuel: {adresse[:25]}{"..." if len(adresse)>25 else ""})",
            f"3. Adresse mail (Actuel: {mail})",
            f"0. Sauvegarder et Quitter"
            ]
        deco_console(titre, taille, options)
        choix_modif = input("Faite votre choix > ").strip()
        if choix_modif == "0":
            break
        elif choix_modif == "1":
            tel = input("Le nouveau numéro : ").strip()
            tel_pattern = r"^0[1-9][0-9]{8}$"
            while not(re.match(tel_pattern, tel)):
                print("Le numéro doit contenir 10 chiffres et doit être du forme : 0YXXXXXXXX.")
                tel = input("Nouveau Numéro : ").strip()
        elif choix_modif == "2":
            adresse = input("Nouveau Adresse: ").strip()
        elif choix_modif == "3":
            mail = test_valeur("Nouveau Email").strip()
            mail_pattern = r"^[a-zA-Z0-9_.-]+@[a-z]{2,}\.[a-z]{2,}$"
            while not(re.match(mail_pattern, mail)):
                print(f"exemple mail valide: {prenom.lower()}{nom.lower()}@gmail.com")
                mail = test_valeur("Email")
    return {"Nom": nom, "Prenom": prenom, "Telephone": tel, "Adresse": adresse, "Email": mail}

def menu_principal():
    utilisateur = None
    role = None
    
    if not reseau.connecter_serveur():
        print("Impossible de joindre le serveur.")
        return

    while True:
        clear_console()
        if not utilisateur:
            titre = "--- ACCUEIL ---"
            taille = 30
            options = [
                "1. Connexion",
                "2. Quitter"
                ]
            deco_console(titre, taille, options)
            
            choix = input("Faite votre choix > ").strip()
            if choix == "2": break
            if choix == "1":
                nom = input("Utilisateur : ").strip()
                mdp = sha512(getpass("Mot de passe : ").strip().encode()).hexdigest()
                reponse = reseau.envoyer_PDU("CONNEXION", {"nom": nom, "mdp": mdp})
                if reponse["status"] == 200:
                    utilisateur = nom
                    role = reponse["role"]
                    print(f"Connecté: {utilisateur}")
                else: print("Erreur:", reponse["message"])
        else:
            titre = f"--- MENU ({utilisateur}) ---"
            taille = 40
            options_brutes = [
                "1. Lister contacts",
                "2. Ajouter / Modifier contact",
                "3. Rechercher",
                "4. Gérer permissions",
                "5. Créer compte" if role == "admin" else None,
                "0. Déconnexion"
                ]
            deco_console(titre, taille, options_brutes)
            
            choix = input("Faite votre choix > ").strip()
            if choix == "0":
                utilisateur = None
                
            elif choix == "1":
                clear_console()
                titre = f"--- LISTE DES CONTACTS ---"
                taille = 60
                reponse = reseau.envoyer_PDU("LISTE_PROPRIO", {}, utilisateur)
                options_brutes = []
                for personne in reponse["donnee"]:
                    options_brutes.append(f" - {personne}")
                deco_console(titre, taille, options_brutes, "Annuaire Consultable :")
                cible = input("Propriétaire de l'annuaire (Vide pour le votre) : ").strip() or utilisateur
                reponse = reseau.envoyer_PDU("LISTE_CONTACTS", {"proprietaire_cible": cible}, utilisateur)
                if reponse["status"] == 200:
                    if reponse["donnee"] != []:
                        for i, element in enumerate(reponse["donnee"]):
                            print(f"\n- Contact N°{i + 1} :")
                            print("=" * taille)
                            print(f"  > Nom : {element["Prenom"]} {element["Nom"]}")
                            print(f"  > Numéro de Téléphone  : {element["Telephone"]}")
                            print(f"  > Adresse postal : {element["Adresse"]}")
                            print(f"  > Adresse mail : {element["Email"]}")
                            
                    else: print("Annuaire Vide")
                else: print(reponse["message"])
                
            elif choix == "2":
                clear_console()
                taille = 60
                print("\033[92m" + f"{"=== ANNUAIRE PARTAGE ===":^{taille}}" + "\033[0m")
                print("=" * taille)
                print(f"{"--- AJOUT D'UN CONTACT ---":^{taille}}")
                print("=" * taille)
                print("Les champs annotés d'une '*' sont obligatoires.")
                nom = test_valeur("Nom").upper()
                prenom = test_valeur("Prénom").capitalize()
                existe = False
                reponse = reseau.envoyer_PDU("LISTE_CONTACTS", {"proprietaire_cible": utilisateur},utilisateur)
                if reponse["status"] == 200:
                    for contact in reponse["donnee"]:
                        if contact["Nom"] == nom and contact["Prenom"] == prenom:
                            existe = True
                            contact_actuel = contact
                            break
                if existe:
                    print(f"Le contact '{prenom} {nom}' existe déjà.")
                    while True:
                        modif = input("Voulez-vous modifier ce contact ? [O/N] : ").strip().lower()
                        if modif in ["o", "n"]: break
                        else: print("Répondez par O ou N.")
                        
                    if modif == "o":
                        tel = contact_actuel["Telephone"]
                        adresse = contact_actuel["Adresse"]
                        mail = contact_actuel["Email"]
                        donnee = menu_modif(prenom, nom, tel, adresse, mail)
                        reponse = reseau.envoyer_PDU("MODIF_CONTACT", {"contact": donnee}, utilisateur)
                        print(reponse["message"])
                else:
                    tel = input("Numéro de téléphone : ").strip()
                    tel_pattern = r"^0[1-9][0-9]{8}$"
                    while not(re.match(tel_pattern, tel)):
                        print("Le numéro doit contenir 10 chiffres et doit être du forme : 0YXXXXXXXX.")
                        tel = input("Numéro de téléphone : ").strip()
                        
                    adresse = input("Adresse: ").strip()
                    
                    mail = test_valeur("Email")
                    mail_pattern = r"^[a-zA-Z0-9_.-]+@[a-z]{2,}\.[a-z]{2,}$"
                    while not(re.match(mail_pattern, mail)):
                        print(f"exemple mail valide: {prenom.lower()}{nom.lower()}@gmail.com")
                        mail = test_valeur("Email")
                    
                    donnee = {"Nom": nom, "Prenom": prenom, "Telephone": tel, "Adresse": adresse, "Email": mail}
                    reponse = reseau.envoyer_PDU("AJOUT_CONTACT", {"contact": donnee}, utilisateur)
                    print(reponse["message"])

            elif choix == "3":
                clear_console()
                titre = f"--- RECHERCHE UN CONTACT ---"
                taille = 60
                reponse = reseau.envoyer_PDU("LISTE_PROPRIO", {}, utilisateur)
                options_brutes = []
                for personne in reponse["donnee"]:
                    options_brutes.append(f" - {personne}")
                deco_console(titre, taille, options_brutes, "Annuaire Consultable :")
                cible = input("Dans l'annuaire de qui (Vide pour le votre) : ").strip() or utilisateur
                quelquun = input("Mot clé recherché : ").strip().lower()
                reponse = reseau.envoyer_PDU("RECHERCHE_CONTACT", {"proprietaire_cible": cible, "recherche": quelquun}, utilisateur)
                if reponse["status"] == 200:
                    for element in reponse["donnee"]:
                        print(f"\nTrouvé: {element["Prenom"]} {element["Nom"]}")
                        print("=" * taille)
                        print(f"  > Numéro : {element["Telephone"]}")
                        print(f"  > Adresse Postal : {element["Adresse"]}")
                        print(f"  > Adresse Mail : {element["Email"]}")
                else: print(reponse["message"])
                
            elif choix == "4":
                clear_console()
                titre = "--- GESTION DES PERMISSION ---"
                taille = 40
                options = [
                    "1. Donner le droit d'accès",
                    "2. Retirer le droit d'accès"
                ]
                deco_console(titre, taille, options)
                reponse = reseau.envoyer_PDU("LISTE_COMPTES", {}, utilisateur)
                tous_les_utilisateur = reponse["donnee"]
                reponse = reseau.envoyer_PDU("LISTE_DROIT", {}, utilisateur)
                utilisateur_avec_droit = reponse["donnee"]
                utilisateur_sans_droit = [utili for utili in tous_les_utilisateur if (utili not in utilisateur_avec_droit and utili != utilisateur)]
                
                while True:
                    choix = input("Faites votre choix > ")
                    if choix == "1":
                        action = "donner"
                        clear_console()
                        titre = "--- DONNER LA PERMISSION ---"
                        taille = 60
                        options = []
                        for option in utilisateur_sans_droit:
                            options.append(f" - {option}")
                        deco_console(titre, taille, options, "Les utilisateurs n'ayant pas accès à votre annuaire :")
                        break
                    elif choix == "2":
                        action = "retirer"
                        clear_console()
                        titre = "--- RETIRER LA PERMISSION ---"
                        taille = 60
                        options = []
                        for option in utilisateur_avec_droit:
                            options.append(f" - {option}")
                        deco_console(titre, taille, options, "Les utilisateurs ayant accès à votre annuaire :")
                        break
                    else:
                        print("Insèrez '1' pour Donner ou '2' pour Retirer l'accès")
                        continue
                while True:
                    cible = input("Utilisateur cible (Vide pour quitter): ").strip()
                    if cible == "":
                        print("Action annulé, retour à l'Accueil")
                        break
                    elif cible not in tous_les_utilisateur:
                        print("La cible doit être un utilisateur existant")
                        continue
                    else:
                        break
                if cible != "":
                    reponse = reseau.envoyer_PDU("GERER_PERMISSION", {"utilisateur_cible": cible, "type": action}, utilisateur)
                if reponse["status"] == 200:
                    if choix == "1" and cible != "":
                        print(f"Permission accordé à {cible}")
                    elif choix == "2" and cible != "":
                        print(f"Permission retiré à {cible}")
                else:
                    print(reponse["message"])
                
            elif choix == "5" and role == "admin":
                clear_console()
                print("\033[92m" + f"{"=== ANNUAIRE PARTAGE ===":^{taille}}" + "\033[0m")
                print("=" * taille)
                print(f"{"--- CRÉER UN COMPTE ---":^{taille}}")
                print("=" * taille)
                while True:
                    nom = input("Nom d'utilisateur : ")
                    if nom == "":
                        print("Insérer un Nom d'utilisateur")
                    else:
                        break
                while True:
                    mdp = getpass("Mot de passe : ")
                    if len(mdp) < 5 :
                        print("Le Mot de passe est trop court")
                    else:
                        mdp = sha512(mdp.encode()).hexdigest()
                        break
                statut = input("Role (Administrateur/Utilisateur) : ")
                reponse = reseau.envoyer_PDU("CREATION_COMPTE", {"nom": nom, "mot_de_passe": mdp, "statut": statut}, utilisateur)
                print(reponse["message"])

        input("\nAppuyez sur Entrée pour continuer...")
            
    reseau.deconnecter_serveur()

if __name__ == "__main__":
    reseau.creer_serveur()
    menu_principal()
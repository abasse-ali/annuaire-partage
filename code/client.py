"""
Client
"""

import re
import time
import mes_fonctions
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
def menu_modif(prenom, nom, tel, adresse, mail):
    while True:
        mes_fonctions.clear_console()
        titre = f"--- MODIFICATION ({prenom} {nom}) ---"
        taille = 60
        options = [
            f"1. Numéro de téléphone (Actuel: {tel})",
            f"2. Adresse postal (Actuel: {adresse[:25]}{"..." if len(adresse)>25 else ""})",
            f"3. Adresse mail (Actuel: {mail})",
            f"0. Sauvegarder et Quitter"
            ]
        mes_fonctions.deco_console(titre, taille, options)
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
            mail = mes_fonctions.test_valeur("Nouveau Email").strip()
            mail_pattern = r"^[a-zA-Z0-9_.-]+@[a-z]{2,}\.[a-z]{2,}$"
            while not(re.match(mail_pattern, mail)):
                print(f"exemple mail valide: {prenom.lower()}{nom.lower()}@gmail.com")
                mail = mes_fonctions.test_valeur("Email")
    return {"Nom": nom, "Prenom": prenom, "Telephone": tel, "Adresse": adresse, "Email": mail}
    
def menu_principal():
    utilisateur = None
    role = None
    
    while True:
        if not reseau.connecter_serveur():
            mes_fonctions.clear_console()
            taille = 40
            titre = "=== ANNUAIRE PARTAGÉ ==="
            options = [
                "1. Réessayer la connexion",
                "0. Quitter"
            ]
            mes_fonctions.deco_console(titre, taille, options)
            print("Le serveur est actuellement HORS LIGNE.")
            choix = input("Choix > ")
            if choix == "0": return
            if choix == "1":
                print("Recherche du serveur...")
                time.sleep(1)
                if reseau.connecter_serveur():
                    print("\033[92mServeur trouvé ! Connexion établie.\033[0m")
                    time.sleep(1)
                else:
                    print("\033[91mÉchec : Le serveur n'a pas ouvert la connexion.\033[0m")
        else:
            mes_fonctions.clear_console()
            if not utilisateur:
                titre = "--- ACCUEIL ---"
                taille = 30
                options = [
                    "1. Connexion",
                    "2. Quitter"
                    ]
                print("\033[92m" + f"{"=== ANNUAIRE PARTAGE ===":^{taille}}" + "\033[0m")
                mes_fonctions.deco_console(titre, taille, options)
                
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
                    "2. Gérer contacts",
                    "3. Rechercher contacts",
                    "4. Gérer permissions",
                    "5. Gérer comptes" if role == "administrateur" else None,
                    "0. Déconnexion"
                    ]
                mes_fonctions.deco_console(titre, taille, options_brutes)
                
                choix = input("Faite votre choix > ").strip()
                if choix == "0":
                    utilisateur = None
                    print("Déconnexion...")
                    
                elif choix == "1":
                    mes_fonctions.clear_console()
                    titre = f"--- LISTE DES CONTACTS ---"
                    taille = 60
                    options_brutes = []
                    reponse = reseau.envoyer_PDU("LISTE_PROPRIO", {}, utilisateur)
                    if reponse["status"] == 200:
                        for personne in reponse["donnee"]:
                            options_brutes.append(f" - {personne}")
                        mes_fonctions.deco_console(titre, taille, options_brutes, "Annuaire Consultable :")
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
                    else: print(reponse["message"])
                
                elif choix == "2":
                    while True:
                        mes_fonctions.clear_console()
                        titre = f"--- GESTION CONTACT ---"
                        taille = 40
                        options_brutes = [
                            "1. Ajouter/Modifier contacts",
                            "2. Supprimer contacts",
                            "0. Retour"
                            ]
                        mes_fonctions.deco_console(titre, taille, options_brutes)
                        choix_contact = input("Faites votre choix > ")
                        if choix_contact == "1":
                            mes_fonctions.clear_console()
                            taille = 60
                            print("=" * taille)
                            print("\033[92m" + f"{"--- AJOUT D'UN CONTACT ---":^{taille}}" + "\033[0m")
                            print("=" * taille)
                            print("Les champs annotés d'une '*' sont obligatoires.")
                            nom = mes_fonctions.test_valeur("Nom").upper()
                            prenom = mes_fonctions.test_valeur("Prénom").capitalize()
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
                                if tel != "":
                                    tel_pattern = r"^0[1-9][0-9]{8}$"
                                    while not(re.match(tel_pattern, tel)):
                                        print("Le numéro doit contenir 10 chiffres et doit être du forme : 0YXXXXXXXX.")
                                        tel = input("Numéro de téléphone : ").strip()
                                        if tel == "":
                                            break
                                        
                                adresse = input("Adresse: ").strip()
                                
                                mail = mes_fonctions.test_valeur("Email")
                                mail_pattern = r"^[a-zA-Z0-9_.-]+@[a-z]{2,}\.[a-z]{2,}$"
                                while not(re.match(mail_pattern, mail)):
                                    print(f"exemple mail valide: {prenom.lower()}{nom.lower()}@gmail.com")
                                    mail = mes_fonctions.test_valeur("Email")
                                
                                donnee = {"Nom": nom, "Prenom": prenom, "Telephone": tel, "Adresse": adresse, "Email": mail}
                                reponse = reseau.envoyer_PDU("AJOUT_CONTACT", {"contact": donnee}, utilisateur)
                                print(reponse["message"])
                            
                        elif choix_contact == "2":
                            mes_fonctions.clear_console()
                            print("=" * taille)
                            print("\033[92m" + f"{"--- SUPPRESSION CONTACT ---":^{taille}}" + "\033[0m")
                            print("=" * taille)
                            nom = input("Nom du contact à supprimer : ").strip().upper()
                            prenom = input("Prénom du contact à supprimer : ").strip().capitalize()
                            
                            if nom == "" or prenom == "":
                                print("Annulation : Nom et Prénom obligatoires.")
                            else:
                                existe = False
                                reponse = reseau.envoyer_PDU("LISTE_CONTACTS", {"proprietaire_cible": utilisateur},utilisateur)
                                if reponse["status"] == 200:
                                    for contact in reponse["donnee"]:
                                        if contact["Nom"] == nom and contact["Prenom"] == prenom:
                                            existe = True
                                            contact_actuel = contact
                                            break
                                
                                if existe:
                                    confirm = input(f"Voulez-vous vraiment supprimer '{prenom} {nom}' ? [O/N] : ").lower()
                                    if confirm == "o":
                                        donnee = {"Nom": nom, "Prenom": prenom}
                                        reponse = reseau.envoyer_PDU("SUPPR_CONTACT", {"contact": donnee}, utilisateur)
                                        print(f"Résultat : {reponse['message']}")
                                    else:
                                        print("Suppression annulée.")
                                else:
                                    print("Ce contact n'existe pas")
                            
                        elif choix_contact == "0":
                            break
                        if choix_contact != "0":
                            input("\nAppuyez sur Entrée pour continuer...")
                elif choix == "3":
                    mes_fonctions.clear_console()
                    titre = f"--- RECHERCHE UN CONTACT ---"
                    taille = 60
                    reponse = reseau.envoyer_PDU("LISTE_PROPRIO", {}, utilisateur)
                    if reponse["status"] == 200:
                        options_brutes = []
                        for personne in reponse["donnee"]:
                            options_brutes.append(f" - {personne}")
                        mes_fonctions.deco_console(titre, taille, options_brutes, "Annuaire Consultable :")
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
                    else: print(reponse["message"])
                elif choix == "4":
                    mes_fonctions.clear_console()
                    titre = "--- GESTION DES PERMISSION ---"
                    taille = 40
                    options = [
                        "1. Donner le droit d'accès",
                        "2. Retirer le droit d'accès"
                    ]
                    mes_fonctions.deco_console(titre, taille, options)
                    reponse = reseau.envoyer_PDU("LISTE_COMPTES", {}, utilisateur)
                    if reponse["status"] == 200:
                        tous_les_utilisateur = reponse["donnee"]
                        reponse = reseau.envoyer_PDU("LISTE_DROIT", {}, utilisateur)
                        if reponse["status"] == 200:
                            utilisateur_avec_droit = reponse["donnee"]
                        utilisateur_sans_droit = [utili for utili in tous_les_utilisateur if (utili not in utilisateur_avec_droit and utili != utilisateur)]
                        
                        while True:
                            choix = input("Faites votre choix > ")
                            if choix == "1":
                                action = "donner"
                                mes_fonctions.clear_console()
                                titre = "--- DONNER LA PERMISSION ---"
                                taille = 60
                                options = []
                                for option in utilisateur_sans_droit:
                                    options.append(f" - {option}")
                                mes_fonctions.deco_console(titre, taille, options, "Les utilisateurs n'ayant pas accès à votre annuaire :")
                                break
                            elif choix == "2":
                                action = "retirer"
                                mes_fonctions.clear_console()
                                titre = "--- RETIRER LA PERMISSION ---"
                                taille = 60
                                options = []
                                for option in utilisateur_avec_droit:
                                    options.append(f" - {option}")
                                mes_fonctions.deco_console(titre, taille, options, "Les utilisateurs ayant accès à votre annuaire :")
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
                    else:
                        print(reponse["message"])
                    
                elif choix == "5" and role == "administrateur":
                    while True:
                        mes_fonctions.clear_console()
                        titre = "--- GESTION COMPTES ---"
                        taille = 40
                        options = [
                            "1. Créer Compte",
                            "2. Supprimer Compte",
                            "3. Modifier Compte",
                            "4. Lister Compte",
                            "0. Retour"
                        ]
                        mes_fonctions.deco_console(titre, taille, options)
                        choix_compte = input("Faites votre choix > ")
                        if choix_compte == "1":
                            mes_fonctions.clear_console()
                            print("=" * taille)
                            print("\033[92m" + f"{"--- CRÉER UN COMPTE ---":^{taille}}" + "\033[0m")
                            print("=" * taille)
                            while True:
                                nom = input("Nom d'utilisateur : ")
                                if nom == "":
                                    print("Insérer un Nom d'utilisateur")
                                    continue
                                else:
                                    break
                            while True:
                                mdp = getpass("Mot de passe : ")
                                if len(mdp) < 5 :
                                    print("Le Mot de passe est trop court")
                                    continue
                                else:
                                    mdp = sha512(mdp.encode()).hexdigest()
                                    break
                            titre = "ROLE"
                            options = ["1. Administrateur", "2. Utilisateur"]
                            mes_fonctions.deco_console(titre, taille, options)
                            while True:
                                choix_role = input("Faites votre choix > ")
                                if choix_role == "1":
                                    statut = "administrateur"
                                    break
                                elif choix_role == "2":
                                    statut = "utilisateur"
                                    break
                                else:
                                    print("Le choix doit être entre '1' ou '2'.")
                                    continue
                            reponse = reseau.envoyer_PDU("CREATION_COMPTE", {"nom": nom, "mot_de_passe": mdp, "statut": statut}, utilisateur)
                            if reponse["status"] == 200:
                                print(reponse["message"])
                            else:
                                print(reponse["message"])
                                break
                            
                        elif choix_compte == "2":
                            mes_fonctions.clear_console()
                            print("=" * taille)
                            print("\033[92m" + f"{"--- SUPPRESSION COMPTE ---":^{taille}}" + "\033[0m")
                            print("=" * taille)
                            
                            cible = input("Nom du compte à supprimer : ").strip()
                            
                            if cible == utilisateur:
                                print("Erreur : Vous ne pouvez pas supprimer votre propre compte connecté.")
                            elif cible == "":
                                print("Annulation.")
                            else:
                                reponse = reseau.envoyer_PDU("LISTE_COMPTES", {}, utilisateur)
                                if reponse["status"] == 200:
                                    comptes = reponse["donnee"]
                                    if cible in comptes:
                                        confirm = input(f"Êtes-vous sûr de vouloir supprimer '{cible}' ? (TOUT sera perdu) [O/N] : ").lower()
                                        if confirm == "o":
                                            reponse = reseau.envoyer_PDU("SUPPRESSION_COMPTE", {"nom_compte": cible}, utilisateur)
                                            print(f"Résultat : {reponse['message']}")
                                        else:
                                            print("Suppression annulée.")
                                    else:
                                        print("Comptes Inexistant")
                                else:
                                    print(reponse["message"])
                                    break

                        elif choix_compte == "3":
                            mes_fonctions.clear_console()
                            print("=" * taille)
                            print("\033[92m" + f"{"--- MODIFIER COMPTE ---":^{taille}}" + "\033[0m")
                            print("=" * taille)

                            cible = input("Nom du compte à modifier : ").strip()
                            
                            if cible == "":
                                print("Annulation.")
                            else:
                                reponse = reseau.envoyer_PDU("LISTE_COMPTES", {}, utilisateur)
                                if reponse["status"] == 200:
                                    comptes = reponse["donnee"]
                                    if cible in comptes:
                                        print(f"Modification de '{cible}' (Laissez vide pour ne pas changer)")
                                        
                                        nouveau_statut = None
                                        print("\nNouveau rôle (Vide pour Inchangé) :")
                                        print(" 1. Administrateur")
                                        print(" 2. Utilisateur")
                                        
                                        choix_role = input("\nFaites votre choix > ").strip()
                                        while choix_role not in ["1", "2", ""]:
                                            print("Le choix doit être entre '1' ou '2' ou ''(vide)")
                                            choix_role = input("Faites votre choix > ").strip()
                                            
                                        if choix_role == "1": nouveau_statut = "administrateur"
                                        elif choix_role == "2": nouveau_statut = "utilisateur"

                                        nouveau_mdp = None
                                        mdp_input = getpass("Nouveau mot de passe (Vide pour Inchangé) : ").strip()
                                        if mdp_input != "":
                                            while len(mdp_input) < 5:
                                                print("Attention: Mot de passe ignoré (trop court). Réessayez !")
                                                mdp_input = getpass("Nouveau mot de passe (Vide pour Inchangé) : ").strip()
                                            
                                            nouveau_mdp = sha512(mdp_input.encode()).hexdigest()

                                        if nouveau_statut or nouveau_mdp:
                                            donnees_modif = {
                                                "nom_compte": cible,
                                                "nouveau_mdp": nouveau_mdp,
                                                "nouveau_statut": nouveau_statut
                                            }
                                            reponse = reseau.envoyer_PDU("MODIF_COMPTE", donnees_modif, utilisateur)
                                            if reponse["status"] == 200:
                                                print(f"Résultat : {reponse['message']}")
                                            else:
                                                print(f"Erreur : {reponse['message']}")
                                                break
                                        else:
                                            print("Aucune modification demandée.")
                                    else:
                                        print("Compte Inexistant")
                        
                        elif choix_compte == "4":
                            mes_fonctions.clear_console()
                            reponse = reseau.envoyer_PDU("INFOS_ADMIN", {}, utilisateur)
                            
                            if reponse["status"] == 200:
                                print("\033[92m" + f"{"=== LISTE GLOBALE DES COMPTES ===":^{80}}" + "\033[0m")
                                print("-" * 80)
                                print(f"| {'Nom':<20} | {'Rôle':<15} | {'Contacts':<10} | {'Annuaire Accèssible':<22} |")
                                print("-" * 80)
                                
                                for row in reponse["donnee"]:
                                    nom = row['Nom']
                                    role = row['Statut']
                                    nb_c = str(row['Nb_Contacts'])
                                    nb_d = str(row['Nb_Annuaires'])
                                    
                                    coul = "\033[91m" if role == "administrateur" else "\033[96m"
                                    reset = "\033[0m"
                                    
                                    print(f"| {coul}{nom:<20}{reset} | {role:<15} | {nb_c:<10} | {nb_d:<22} |")
                                print("-" * 80)
                                print(f"Total comptes : {len(reponse['donnee'])}\n")
                                print("Voir la liste complète des annuaires accessible d'un compte")
                                cible_compte = input("Le compte de qui (vide pour annuler) : ")
                                if cible_compte != "":
                                    reponse = reseau.envoyer_PDU("LISTE_PROPRIO", {}, cible_compte)
                                    print(f"Cible : {cible_compte}")
                                    if reponse["status"] == 200 and reponse["donnee"] != []:
                                        for personne in reponse["donnee"]:
                                            print(f"  - {personne}")
                                    elif reponse["donnee"] == []:
                                        print("  Aucun")
                                    else:
                                        print(reponse["message"])
                            else:
                                print("Erreur lors de la récupération des données.")
                                break

                        elif choix_compte == "0":
                            
                            break
                        if choix_compte != "0":
                            input("\nAppuyez sur Entrée pour continuer...")
                        
        input("\nAppuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    menu_principal()
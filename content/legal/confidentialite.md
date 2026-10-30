+++
title = "Politique de confidentialité"
summary = "Les données que Sensitor conserve, pourquoi, combien de temps, et vos droits."
+++

## Responsable du traitement

{editeur.raison_sociale}, {editeur.siege}. Pour toute question sur vos données : {editeur.contact_donnees}.

## Ce que nous conservons

Sensitor ne conserve que ce que vous lui confiez pour utiliser le service. Rien n'est vendu, rien ne sert à de la publicité, aucun profil marketing n'est constitué.

- **Votre compte** : votre adresse e-mail, votre nom affiché si vous en donnez un, la date de vérification de l'adresse, votre niveau d'accès, la date de votre dernière connexion, et le nombre de tentatives de connexion échouées. Votre mot de passe n'est jamais conservé en clair : seule une empreinte calculée avec l'algorithme scrypt l'est, et personne, chez Sensitor non plus, ne peut le relire.
- **Vos sessions** : pour chaque appareil connecté, une empreinte du jeton de session (jamais le jeton lui-même), sa date de création, de dernière activité et d'expiration.
- **Votre progression** : les leçons terminées, vos réponses aux quiz et leurs résultats.
- **Votre journal de réflexion**, dans l'espace Psychologie et discipline : vos notes, votre humeur et les points de votre routine.
- **Votre journal de trading** : les trades saisis, importés ou synchronisés (instrument, sens, prix, taille, stop, objectif, résultat, frais), vos annotations (setups, écarts, émotions, notes), votre plan de trading, et, pour un import MetaTrader 5, le numéro du compte et les données brutes du courtier pour chaque position. Le mot de passe investisseur demandé pour une synchronisation MetaTrader 5 sert à la connexion et n'est jamais conservé.
- **Vos portefeuilles** : les allocations enregistrées, leurs historiques, le portefeuille de travail, les quantités et les prix que vous saisissez à la main.
- **Vos demandes de revue** : quand vous envoyez un trade à un coach, une copie de ce trade, de sa revue automatique, de votre plan et de votre question.

Sensitor ne demande jamais de phrase de récupération, de clé privée ni de mot de passe d'exchange, et n'en conserve pas.

## Pourquoi

- Pour vous fournir le service que vous utilisez : votre compte, votre progression, vos journaux et vos analyses. Base légale : l'exécution du service auquel vous vous inscrivez.
- Pour la sécurité des comptes : sessions, verrouillage après plusieurs échecs de connexion, liens de réinitialisation à usage unique. Base légale : notre intérêt légitime à protéger vos données.
- Pour vous écrire uniquement les e-mails liés à votre compte : vérification de votre adresse et mot de passe oublié.

## Qui y a accès

- **Vous seul**, pour vos journaux, vos trades, vos portefeuilles et votre progression : un autre membre n'y a jamais accès.
- **Un coach Sensitor**, pour les seuls trades que vous choisissez de lui envoyer, sous un pseudonyme : il ne voit pas votre adresse ni le reste de votre journal.
- **Nos hébergeurs**, qui stockent les données pour notre compte : {hebergement.application} pour l'application, {hebergement.base_de_donnees} pour la base de données, {hebergement.emails} pour l'envoi des e-mails.
- Pour afficher les cours des actifs que vous analysez, nos serveurs interrogent un fournisseur de données de marché avec les seuls symboles des actifs (par exemple « SPY ») : aucune donnée vous concernant ne lui est transmise.

Si un hébergeur traite des données hors de l'Union européenne, ce transfert est encadré par les garanties prévues par le RGPD (décision d'adéquation ou clauses contractuelles types) : {hebergement.application}.

## Combien de temps

- Vos données sont conservées tant que votre compte existe.
- Une session expire au bout de 30 jours. Un lien de réinitialisation expire au bout d'une heure, un lien de vérification au bout de 48 heures.
- Quand vous supprimez votre compte, toutes vos données sont effacées immédiatement de la base. Elles peuvent subsister dans les sauvegardes jusqu'à leur rotation, au plus {sauvegardes_jours} jours.
- Les revues qu'un coach a rédigées et les séances de la salle des marchés restent publiées sans le nom de leur auteur si son compte est supprimé.

## Cookies

Sensitor dépose un seul cookie, `sensitor_session`, qui garde votre connexion d'une visite à l'autre pendant 30 jours. Il est strictement nécessaire au service et ne sert à aucun suivi. Aucun cookie publicitaire ni de mesure d'audience n'est déposé. Les polices de caractères sont servies par Sensitor lui-même : votre navigateur ne contacte aucun service tiers pour les afficher.

## Vos droits

Vous pouvez à tout moment :

- **télécharger toutes vos données** dans un fichier, depuis la page « Compte » (droit d'accès et à la portabilité) ;
- **supprimer votre compte** et tout ce qui s'y rattache, depuis la même page (droit à l'effacement) ;
- corriger une donnée, vous opposer à un traitement ou en demander la limitation, en écrivant à {editeur.contact_donnees}.

Si vous estimez que vos droits ne sont pas respectés, vous pouvez adresser une réclamation à la CNIL (www.cnil.fr).

## Sécurité

Les échanges avec Sensitor sont chiffrés (HTTPS). Les mots de passe sont conservés sous forme d'empreinte scrypt, les jetons de session sous forme d'empreinte, et les données de chaque membre ne sont lisibles que par lui.

## Âge

Sensitor traite des marchés financiers et s'adresse aux personnes majeures.

Dernière mise à jour : {mise_a_jour}.

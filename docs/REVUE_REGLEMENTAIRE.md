# Revue réglementaire avant toute offre payante (P2.0)

Dossier à remettre à un avocat ou un juriste spécialisé (droit financier et
droit de la consommation). Il décrit ce que fait Sensitor aujourd'hui et liste
les questions à trancher **avant** d'ouvrir un paiement. Ce document ne donne
aucune réponse juridique : les références citées sont des pistes à vérifier
par le professionnel.

Le code n'a ni prix, ni bouton de paiement, ni prestataire de paiement : la
règle du projet (CLAUDE.md) interdit d'en ajouter avant cette revue.

## 1. Ce que fait Sensitor aujourd'hui

- **Formation** au trading, à la monnaie, à Bitcoin, aux crypto-actifs et à
  l'investissement : leçons, quiz, exercices, simulateurs, fiches, articles.
- **Outils d'analyse** sur les données du membre : journal de trading (import
  MetaTrader 5), analyse de portefeuille, optimisation et stress tests sur des
  données historiques.
- **Revue d'un trade clôturé** par un coach, à la demande du membre, sur sa
  méthode et le respect de son propre plan.
- **Salle des marchés** : séances préparées par un coach (contexte, scénarios
  et ce qui les invalide), puis relues après la clôture. Pas de signal d'achat
  ou de vente.
- **Accompagnement** : cohortes de membres, ateliers en visio, questions à
  l'équipe sur la méthode, le plan et l'organisation. Les formulaires précisent
  que la réponse n'est jamais une recommandation sur un actif, un montant ou un
  moment.
- **Accès** : gratuit, Premium (attribué à la main), Accompagné (Premium et
  cohorte). Aucun abonnement payant.
- **Données** : compte, progression, journaux, portefeuilles, trades. Jamais de
  phrase de récupération, de clé privée ni de mot de passe d'exchange.

## 2. Questions à trancher

**Statut de l'activité**
1. La formation, les outils, la revue de trades clôturés, la salle des marchés
   et l'accompagnement, tels que décrits, restent-ils hors du conseil en
   investissement (statut de CIF, agrément AMF) ? Où passe la limite pour la
   salle des marchés et les réponses aux questions d'accompagnement ?
2. Les mêmes activités, une fois payantes, changent-elles de qualification ?
3. Faut-il un cadre écrit pour les coachs (charte, relecture) ? Le texte actuel
   est dans `sensitor/platform/support.py` et `sensitor/trading/coaching.py`.

**Crypto-actifs et communication**
4. La présentation de Bitcoin et des crypto-actifs (leçons, articles, site
   public) est-elle concernée par les règles de la loi du 9 juin 2023 sur
   l'influence commerciale et par le règlement européen MiCA (2023/1114) en
   matière de communication sur les crypto-actifs ?
5. Quelles mentions de risque faut-il, et où (site, plateforme, e-mails) ? Les
   mentions actuelles : « Contenu éducatif, ne constitue pas un conseil en
   investissement » et le risque de perte en capital.
6. Des partenariats ou liens affiliés (courtiers, exchanges, prop firms) sont-ils
   envisageables, et à quelles conditions ? Il n'y en a aucun aujourd'hui.

**Vente en ligne**
7. Conditions générales de vente : contenu obligatoire pour un abonnement à un
   contenu numérique et à des ateliers.
8. Droit de rétractation : comment l'appliquer à un contenu numérique fourni
   immédiatement (accord exprès et renoncement, à vérifier au Code de la
   consommation) et à des ateliers en direct ?
9. TVA sur des services électroniques vendus à des particuliers dans l'Union :
   vendre en direct (déclaration via le guichet unique) ou par un « merchant of
   record » qui la gère ?
10. Résiliation d'un abonnement en ligne : quelles obligations de simplicité ?

**Données personnelles**
11. La politique de confidentialité (`content/legal/confidentialite.md`) est-elle
    complète, notamment pour l'accompagnement, la lettre, les statistiques sans
    cookie et les données de trading ?
12. Faut-il une analyse d'impact (AIPD) pour des données financières de membres ?
13. Durées de conservation à fixer : sauvegardes, comptes inactifs, preuves de
    consentement à la lettre.

## 3. Ce que la revue doit produire

- Une réponse écrite à chaque question ci-dessus.
- Les textes à publier : CGV, mentions de risque, mises à jour des conditions
  d'utilisation et de la politique de confidentialité.
- Le feu vert, ou les conditions, pour le paiement (P2.1) : le code suivra la
  solution retenue (page de paiement hébergée par le prestataire, webhook
  signé, droits « payment » dans la même table que les droits manuels).

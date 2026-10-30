# Sensitor · feuille de route produit

Proposition du 30 octobre 2026, fondée sur `docs/SENSITOR_AUDIT.md` (constats
référencés A1 à A12, S1 à S10, D1 à D7). Rien de ce qui suit n'est implémenté :
c'est le plan à valider avant de commencer.

## La vision

Sensitor devient une plateforme indépendante d'éducation aux marchés
financiers. Elle se concentre d'abord sur Bitcoin, les cryptomonnaies,
l'économie monétaire et l'investissement, et réunit un média public, une
newsletter, une Academy gratuite et Premium, une bibliothèque, des outils
pédagogiques et de suivi, une communauté et, à terme, un accompagnement
collectif.

La promesse : comprendre les marchés, les cryptomonnaies et les risques, pour
gagner en autonomie. Éducation, jamais conseil personnalisé.

---

## 1. Situation actuelle

### Ce qui est solide
- **Une Academy complète et vérifiée.**
  - 19 cours publiés, 145 leçons, 563 questions de quiz, 60 exercices, 20 fiches.
  - 35 jeux de données sourcés, 46 graphiques.
  - Un validateur et 3 814 vérifications automatiques, toutes vertes.
- **Un socle de comptes sérieux.**
  - Mots de passe en scrypt, sessions révocables, verrouillage après échecs.
  - Réinitialisation et vérification d'adresse à usage unique.
  - Export et suppression du compte.
- **Des données isolées par membre**, vérifiées par un test qui inspecte toutes
  les méthodes du `Store`.
- **Des outils de suivi riches** :
  - Journal de trading avec plan, revue automatique, import du rapport MT5 et
    analyses ;
  - Portefeuille et risque, avec le portefeuille réel ;
  - Salle des marchés ;
  - revue par un coach.
- **Une API documentée** pour l'application mobile.

### Ce qui bloque un lancement public
- **Base de données** (D1, D5) :
  - injoignable en production au 29 octobre, à cause de l'adresse directe
    Supabase ;
  - aucune reconnexion si la connexion tombe ;
  - aucune sauvegarde.
- **Niveaux d'accès** (A3, A4) : le niveau Premium peut être effacé
  automatiquement, et il existe trois vocabulaires et deux sources de vérité.
- **Navigateur partagé** (S1) : un portefeuille peut passer d'un membre au
  suivant.
- **Textes légaux** : ni mentions légales, ni conditions d'utilisation, ni
  politique de confidentialité.
- **Le lien de paiement Stripe de l'application d'analyse et la page
  `landing_page.html`**, avec ses chiffres inventés : contraires aux règles du
  projet.
- **`main` a 12 commits de retard** sur la branche déployée.

### Ce qui manque pour la nouvelle vision
- **Média public** : un site lisible par les moteurs de recherche, des articles,
  une newsletter. Streamlit n'est pas indexable.
- **Rôles** : un rôle administrateur et une gestion interne (membres, niveaux,
  cohortes, ateliers, demandes d'accompagnement, statistiques).
- **Paiement vérifié.**
- **Contenu Premium** : il n'y en a aucun aujourd'hui.
- **Équilibre éditorial** : 10 cours sur 19 sont du trading, alors que la vision
  met d'abord en avant la monnaie, Bitcoin, la crypto et l'investissement ; le
  parcours Investissement 2 est vide.

---

## 2. Architecture cible

Principe : **ne rien réécrire.** On ajoute un site public statique devant, on
garde la plateforme Streamlit comme espace membre, et l'API FastAPI existante
devient le seul point d'entrée des événements extérieurs (paiement, newsletter).

```
                        ┌──────────────────────────────┐
  Moteurs de recherche  │  A. Site public (statique)    │  sensitor.fr
  Visiteurs  ─────────► │  accueil, à propos, articles, │  généré depuis content/
                        │  ressources gratuites,        │  (même source que l'Academy)
                        │  inscription newsletter       │
                        └──────────────┬───────────────┘
                                       │ « Se connecter », « Commencer »
                        ┌──────────────▼───────────────┐
                        │  B. Espace membre (Streamlit) │  app.sensitor.fr
                        │  sensitor_app.py, inchangé    │
                        │  + profil et préférences      │
                        │  + C. pages d'administration  │
                        └──────────────┬───────────────┘
                                       │ même Store
  Prestataire de paiement ──webhook──► ┌▼─────────────────────────────┐
  Prestataire d'e-mails  ──webhook──►  │  API FastAPI (sensitor/api)   │
  Application mobile ────────────────► │  routes existantes + webhooks │
                                       └──────────────┬───────────────┘
                                                      │
                                       ┌──────────────▼───────────────┐
                                       │  PostgreSQL (une seule base)  │
                                       └──────────────────────────────┘
```

### A. Site public
- **Pages** : accueil, présentation de Sensitor, articles et analyses,
  ressources gratuites, inscription à la newsletter, présentation de l'Academy,
  liens de connexion et d'inscription vers l'espace membre.
- **Les articles sont des fichiers**, comme les leçons, dans un nouveau dossier
  `content/media/` (Markdown avec en-tête TOML) :
  - validés par le même chargeur, aux mêmes règles : pas de tirets longs,
    chiffres sourcés, encadrés opinion et débat ;
  - **une seule source de vérité.**
- **Le site est généré** depuis `content/` par un script Python du dépôt, à
  l'image de `scripts/build_resource_pdfs.py`, sans nouveau service.
- **Les pages de leçons publiques et les ressources gratuites** sont publiées
  à partir des fichiers existants, sans copie.
- **Hébergement statique** avec nom de domaine et HTTPS (Cloudflare Pages,
  Netlify ou équivalent) ; référencement complet : titres, descriptions,
  Open Graph, sitemap, flux RSS.

### B. Espace membre
La plateforme actuelle, sans réécriture : tableau de bord (accueil membre),
Academy, Bibliothèque, Progression, outils (Trading Lab, Journal, Portefeuille,
Salle des marchés). On ajoute :
- **Profil et préférences** : nom affiché, adresse, abonnement newsletter,
  niveau d'accès en lecture, export et suppression (déjà là), langue.
- **Un hébergement avec nom de domaine propre**, à décider en P1 (voir
  Dépendances).

### C. Gestion interne
- **Des pages de la plateforme réservées au rôle administrateur**, contrôlées
  côté serveur :
  - membres : recherche, niveau, rôles, dernière connexion ;
  - accès : attribution manuelle du Premium, avec motif et date de fin ;
  - cohortes et ateliers ;
  - demandes d'accompagnement ;
  - statistiques d'acquisition et de conversion.
- **La ligne de commande `core/admin.py` reste**, pour les urgences.

---

## 3. Gestion des accès centralisée

### Niveaux et rôles

| Niveau | Qui | Accès |
|---|---|---|
| **Visiteur** | sans compte | site public, leçons et fiches publiques, simulateurs sans enregistrement |
| **Free** | compte gratuit | tout le contenu `member`, progression, journal, portefeuille, Salle des marchés `member` |
| **Premium** | droit actif, manuel ou payé | contenu `premium`, outils avancés (optimisation, stress tests, plus de lignes), quotas de revue plus hauts |
| **Accompagné** | Premium + inscription à une cohorte | ateliers de la cohorte, demandes d'accompagnement |
| **Administrateur** | rôle | gestion interne ; n'ouvre pas de contenu payant par lui-même |

Coach reste un **rôle** à part (orthogonal au niveau) : file de revue, rédaction
des séances.

### Mécanisme proposé
1. **Un seul module de permissions**, par exemple `sensitor/core/permissions.py`,
   qui expose une fonction `can(member, capability)` et une table des
   capacités. Exemples :
   - `lesson.read.premium`
   - `portfolio.optimize`
   - `portfolio.max_assets`
   - `review.monthly_quota`
   - `admin.members`
   - `market.publish`

   Les interfaces appellent `can()`. Elles ne comparent plus elles-mêmes des
   chaînes comme `"pro"` ou `"premium"`.
2. **Une table `entitlements`** (droits) :
   - champs : adresse, niveau, source (`manual`, `payment`), référence (admin
     auteur ou identifiant d'abonnement), début, fin, motif ;
   - le niveau effectif est calculé à partir des droits actifs ;
   - `users.tier` reste comme cache, pour la compatibilité de l'API et de
     l'application mobile ;
   - la colonne n'est **écrite que par une seule méthode** (`Store.set_tier`),
     plus jamais par `upsert_user`. C'est la correction de A3.
3. **Une table `user_roles`** (adresse, rôle) pour `coach` et `admin`.
   `users.role` est conservée et lue en repli, le temps de la migration.
4. **Le contrôle se fait côté serveur, dans le `Store`**, pour toute écriture
   protégée :
   - une méthode d'administration vérifie le rôle de l'appelant dans sa propre
     requête, comme le font déjà `coach_queue` et `answer_review` ;
   - l'API et les pages passent par ces méthodes.
5. **Compatibilité** :
   - les valeurs historiques sont lues comme Premium : `pro` et `premium`, tout
     comme `PRO_EMAILS`, transformé en droits manuels lors de la migration ;
   - l'application d'analyse lit le niveau effectif au lieu de `PRO_EMAILS`.
     C'est la correction de A4.
6. **Attribution** :
   - manuelle, par un administrateur, depuis la page Membres (avec trace) ;
   - plus tard, par le webhook de paiement vérifié, sur la même table.

---

## 4. Fonctionnalités à conserver

Tout ce qui existe reste, notamment :
- **Le contenu de l'Academy**, son format (Markdown et TOML), les quiz, les
  exercices, le validateur et les tests de contenu.
- **Les espaces de la plateforme**, leurs URL (`?page=…`) et leurs paramètres.
- **Les calculs** : risque, espérance, prop firm, portefeuille, statistiques de
  trading, conversion de devises. Aucun ne change sans justification et test.
  La seule correction faite récemment, le drawdown mesuré depuis le point de
  départ, est testée.
- **Le schéma de base et son évolution par ajout de colonnes.** Le double
  moteur SQLite et PostgreSQL reste.
- **L'API et ses routes utilisées par l'application mobile**, avec leurs
  paramètres et le comportement ETag.
- **L'application d'analyse séparée**, tant que ses écrans ne sont pas tous
  dans la plateforme.
- **Les règles maison** : pas de tirets longs, chiffres sourcés, opinions
  séparées, jamais de phrase de récupération, de clé privée ni de mot de passe
  d'exchange, pas de conseil personnalisé.

---

## 5. Fonctionnalités à développer

| Domaine | Fonctionnalité | Phase |
|---|---|---|
| Fiabilité | reconnexion PostgreSQL, fin de transaction après les lectures, connexion unique | P0 |
| Fiabilité | sauvegarde quotidienne et restauration testée | P0 |
| Sécurité | correction de A2, A3, S1, S2, S3 ; garde-fou `SENSITOR_AUTH` | P0 |
| Conformité | mentions légales, conditions d'utilisation, politique de confidentialité, polices hébergées sur place | P0 |
| Conformité | retrait du lien Stripe de l'analyseur, archivage de `landing_page.html` | P0 |
| Accès | module de permissions, droits, rôle administrateur | P1 |
| Gestion interne | pages Membres et Accès (administrateur) | P1 |
| Newsletter | consentement, double confirmation, désinscription, prestataire d'envoi | P1 |
| Média public | articles dans `content/media/`, générateur du site statique, référencement | P1 |
| Espace membre | profil et préférences | P1 |
| Contenu | rééquilibrage vers monnaie, Bitcoin et investissement ; parcours Investissement 2 | P1 et P2 (rédaction) |
| Contenu | définir le Premium : quelles leçons, outils et ressources | P1 (décision), P2 (production) |
| Paiement | abonnement vérifié par webhook, CGV, TVA, rétractation | P2, après revue réglementaire |
| Accompagnement | cohortes, ateliers, demandes d'accompagnement | P2 |
| Statistiques | source d'inscription et UTM, entonnoir visiteur, Free puis Premium, mesure d'audience sans cookie | P2 |
| Communauté | discussions modérées | P3 |
| Produit | notifications, vidéos et ebooks, Academy dans l'application mobile, fusion de l'analyseur dans la plateforme | P3 |

---

## 6. Plan par phases

Complexité relative : **S** (moins d'une journée), **M** (quelques jours),
**L** (une à deux semaines), **XL** (plus).

### P0 · avant d'ouvrir à des membres

| # | Tâche | Constat | Complexité |
|---|---|---|---|
| P0.1 | Secrets de production : adresse Supabase « Session pooler », `SENSITOR_PUBLIC_URL`, SMTP ; vérifier la page Compte | D1, Prod ? | S |
| P0.2 | Reconnexion automatique de PostgreSQL et fin de transaction après les lectures ; une seule connexion par processus ; test sur un vrai Postgres | D1, D2, D3 | M |
| P0.3 | Sauvegarde quotidienne (celle du fournisseur, plus un `pg_dump` documenté) et restauration testée une fois | D5 | S |
| P0.4 | Le niveau n'est plus écrit par `upsert_user` ; méthode `set_tier` dédiée ; tests | A3 | S |
| P0.5 | Inscription sur un compte sans mot de passe : la refuser, ou la conditionner à la vérification de l'adresse ; `change_password` exige l'ancien mot de passe s'il existe | A2 | S |
| P0.6 | En production (base PostgreSQL configurée), refuser le mode single, ou afficher une alerte bloquante | A1 | S |
| P0.7 | La déconnexion vide tout l'état de session de l'analyseur ; `restore` repart d'un état vide | S1 | S |
| P0.8 | Masquage du mot de passe dans `describe()` ; `.gitignore` complété | S2, S3 | S |
| P0.9 | Retirer le bouton Stripe et le texte « Set STRIPE_PAYMENT_LINK » de l'analyseur ; archiver `landing_page.html` et `DEPLOYMENT_GUIDE.md` | §3 de l'audit | S |
| P0.10 | Pages légales : mentions, conditions d'utilisation, confidentialité (données collectées, durées, droits, sous-traitants), liens en pied de page ; polices hébergées sur place ; statistiques Streamlit coupées | S9 | M (+ informations de la société) |
| P0.11 | Limiter les demandes de réinitialisation et les renvois de vérification ; remettre `failed_logins` à zéro à l'expiration du verrou | A9 | S |
| P0.12 | Fusionner la branche dans `main`, déployer depuis `main`, fixer la version de Python | Prod ? | S |
| P0.13 | Fiscalité : faire valider le taux par un professionnel et réconcilier les deux leçons | §7 de l'audit | S (+ validation externe) |
| P0.14 | Intégration continue minimale : lancer les 22 fichiers de tests à chaque modification, dont `test_database.py` sur PostgreSQL | §0 de l'audit | M |
| P0.15 | Décision sur les données fictives : journal de démonstration et jeux synthétiques, aujourd'hui étiquetés | §3 de l'audit | S (décision) |

**Critères d'acceptation P0**
- La page Compte de production indique une base PostgreSQL durable.
- Après coupure forcée de la connexion, la page suivante fonctionne sans
  redémarrage, avec un test à l'appui.
- Une restauration depuis la sauvegarde a été faite une fois, et la procédure
  est écrite.
- Un membre passé Premium par `set-tier` le reste après avoir ouvert toutes les
  pages des deux applications (test).
- Une adresse dont le compte n'a pas de mot de passe ne peut pas être réclamée
  sans preuve de possession (test).
- Sur un navigateur partagé, après déconnexion, le membre suivant ne voit rien
  du précédent (test).
- Aucune page ne propose de paiement.
- Les trois pages légales sont accessibles depuis chaque page.
- `main` est la branche déployée, et toute la suite passe en intégration
  continue.

### P1 · fondations de la nouvelle offre

| # | Tâche | Complexité |
|---|---|---|
| P1.1 | Module de permissions `can()`, table `entitlements`, table `user_roles`, migration des valeurs `pro`/`premium`/`PRO_EMAILS` ; tous les contrôles existants passent par `can()` | L |
| P1.2 | Rôle administrateur ; pages Membres et Accès (attribution manuelle du Premium avec motif, date de fin et trace) | M |
| P1.3 | Optimisation, stress tests et nombre de lignes rattachés aux capacités (corrige A5) | S |
| P1.4 | Profil et préférences du membre | M |
| P1.5 | Newsletter, voir le §7 : consentement enregistré, double confirmation, désinscription, synchronisation avec le prestataire, export et suppression | M |
| P1.6 | Média public : type « article » dans `content/media/` avec le même chargeur et les mêmes tests ; générateur du site statique (accueil, à propos, articles, ressources gratuites, présentation de l'Academy, formulaire newsletter) ; référencement | L |
| P1.7 | Hébergement de l'espace membre sur un domaine propre (`app.sensitor.fr`) et déploiement de l'API | M |
| P1.8 | Export complet (sessions, contenu de coach) ; suppression confirmée par le mot de passe ; export et suppression aussi dans l'API | S |
| P1.9 | Journalisation minimale sans données personnelles (erreurs, échecs de connexion à la base), suivi des erreurs | S |
| P1.10 | Décider du contenu Premium (liste écrite, validée par le fondateur) ; corriger l'étiquette et l'invite de la Bibliothèque | S (décision) |
| P1.11 | Mise à jour de la documentation : `V1.md`, `ARCHITECTURE.md`, README, CLAUDE.md | S |

**Critères d'acceptation P1**
- Aucune interface ne compare plus de chaîne de niveau : une recherche de
  `"pro"` ou `"premium"` hors du module de permissions et des migrations ne
  donne rien. Un test le vérifie.
- Un administrateur attribue et retire le Premium depuis la plateforme ; un
  non-administrateur reçoit un refus côté serveur (test sur le `Store` et sur
  l'API).
- Une inscription à la newsletter n'est active qu'après confirmation ; la
  désinscription marche en un clic ; le consentement figure dans l'export.
- Le site public est indexable : chaque article a un titre, une description et
  une URL propres ; sitemap et RSS existent ; le validateur refuse un article
  qui enfreint les règles de contenu.
- L'application mobile fonctionne sans modification (tests d'intégration
  mobile verts).

### P2 · monétisation et accompagnement

| # | Tâche | Complexité |
|---|---|---|
| P2.0 | **Revue réglementaire** (prérequis de CLAUDE.md) : statut éducatif hors conseil en investissement, promotion des crypto-actifs (loi « influenceurs » de 2023, MiCA), CGV, TVA, droit de rétractation pour le contenu numérique | externe |
| P2.1 | Paiement : session de paiement hébergée par le prestataire, webhook signé reçu par l'API, table des abonnements et des événements (sans doublon), droits `payment`, portail client ; aucun numéro de carte ne transite par Sensitor | L |
| P2.2 | Production du contenu Premium décidé en P1.10, et parcours Investissement 2 (méthode du fondateur) | XL (rédaction) |
| P2.3 | Cohortes et ateliers : tables, inscription, calendrier, accès des membres « Accompagné » | L |
| P2.4 | Demandes d'accompagnement : formulaire membre, file et réponse côté administrateur, sur le modèle des revues coach | M |
| P2.5 | Statistiques : source d'inscription et UTM enregistrés à l'inscription, entonnoir visiteur, Free puis Premium, tableau de bord administrateur, mesure d'audience sans cookie sur le site public | M |

**Critères d'acceptation P2**
- Un paiement de test donne le Premium par webhook vérifié ; un webhook non
  signé est refusé ; un événement reçu deux fois n'a qu'un effet ; une
  résiliation retire le droit à la fin de la période (tests).
- Un droit manuel et un droit payé coexistent sans s'écraser.
- Un membre hors cohorte ne voit pas les ateliers de la cohorte (test côté
  serveur).
- Les statistiques n'exposent aucune donnée personnelle hors de la page
  administrateur.

### P3 · communauté et extension

| # | Tâche | Complexité |
|---|---|---|
| P3.1 | Communauté : discussions par thème et par parcours, modération, signalement, obligations d'hébergeur | XL |
| P3.2 | Notifications : séance publiée, nouvel article, atelier | M |
| P3.3 | Vidéos et ebooks | L |
| P3.4 | Academy et progression dans l'application mobile (les routes `/academy` existent déjà) | L |
| P3.5 | Fusion progressive de l'application d'analyse dans la plateforme, puis retrait de ses pages historiques non testées | L |

---

## 7. Dépendances

| Besoin | Option recommandée | Pourquoi | Dépendance de code |
|---|---|---|---|
| Base | PostgreSQL Supabase (Session pooler) ou Neon, offre avec sauvegarde | déjà supporté | aucune |
| E-mails transactionnels | SMTP d'un prestataire européen (Brevo, Postmark, Resend) | `core/mailer.py` existe | aucune |
| Newsletter | le même prestataire (Brevo, par exemple : français, listes, double confirmation, désinscription) via son API HTTP | consentement géré chez un prestataire conforme ; Sensitor garde la preuve et le statut | aucune : bibliothèque standard ou `requests`, déjà installé avec yfinance |
| Site public | générateur statique en Python dans le dépôt, hébergement statique | une seule source de contenu, indexable | aucune : le dépôt a déjà son analyseur de blocs (`sensitor/academy/markup.py`) et un rendu HTML imprimable (`sensitor/academy/printable.py`, utilisé pour les PDF) |
| Paiement | prestataire avec page de paiement hébergée et webhooks signés (Stripe, ou un « merchant of record » qui gère la TVA comme Paddle ou Lemon Squeezy) | aucune donnée de carte chez Sensitor | SDK facultatif : la vérification de signature peut se faire avec la bibliothèque standard |
| API | FastAPI et uvicorn, déjà dans le code, à décommenter dans `requirements.txt` | webhooks et application mobile | déjà prévue |
| Hébergement membre | rester sur Streamlit Community Cloud au départ ; un hébergeur avec domaine propre et pas de mise en veille (Render, Railway, un VPS) dès P1 | domaine, disponibilité | aucune |
| Informations et validations externes | identité de la société pour les pages légales ; revue réglementaire ; validation fiscale | P0.10, P2.0, P0.13 | n/a |

---

## 8. Risques

| Risque | Effet | Parade |
|---|---|---|
| Centraliser les permissions touche l'Academy, la salle des marchés, l'analyseur, les quotas et l'API à la fois | régression d'accès, contenu ouvert ou fermé par erreur | migration par étapes : `can()` d'abord en parallèle des anciens contrôles, un test qui compare les deux sur tous les cas, puis bascule |
| Écrans de l'analyseur partagés par deux applications | une modification casse un espace de la plateforme | toujours lancer `test_portfolio_space.py`, `test_journal_analytics.py`, `test_sensitor_pages.py` |
| Réécriture des chiffres en français (`core/numbers.py`) | un symbole ou un attribut altéré | `test_french_numbers.py` ; ajouter un cas par nouveau format |
| PostgreSQL testé à la main seulement | une requête valide en SQLite échoue en production | intégration continue avec Postgres (P0.14) |
| Streamlit épinglé `<1.65` et thème lié à sa structure HTML | une mise à jour casse l'apparence | mise à jour volontaire, avec captures avant et après |
| Paiement sans revue réglementaire | risque juridique | P2.1 bloqué tant que P2.0 n'est pas fait |
| Accompagnement collectif et revues de trades | requalification en conseil en investissement | cadre écrit et validé, revue d'un trade clôturé seulement, jamais de recommandation ; déjà en place pour les revues |
| Données fictives en production | contraire aux contraintes | décision P0.15 ; à défaut, étiquetage maintenu partout |
| Mise en veille de Streamlit Community Cloud | premier chargement lent, mauvaise impression | site public statique devant (P1.6), puis hébergement sans veille (P1.7) |
| Rééquilibrage éditorial | travail de rédaction long, dépend du fondateur | prioriser les cours Bitcoin, monnaie et investissement dans la page d'accueil dès P1, sans retirer le trading |

---

## 9. Contrôles qualité et sécurité à tenir à chaque phase

- **Isolation** : toute nouvelle méthode du `Store` qui touche des données de
  membre filtre sur l'adresse. `test_every_user_method_is_scoped` doit la
  couvrir, ou la lister explicitement dans ses exemptions.
- **Permissions** : contrôle côté serveur dans le `Store` ou l'API, jamais
  seulement dans l'interface.
- **Sessions** : jetons en empreinte, expiration, révocation ; le cookie reste
  `Secure` en production.
- **Endpoints** : toute nouvelle route de l'API dépend de `current_user`, sauf
  exception documentée et testée. Les webhooks vérifient leur signature.
- **Secrets** : uniquement en variables d'environnement ou secrets du
  déploiement, jamais dans le dépôt (`.gitignore` complété en P0.8), jamais
  dans un message d'erreur ni dans un journal.
- **Journaux** : jamais d'adresse, de jeton, de mot de passe ni d'URL de base
  complète.
- **Données personnelles** : chaque nouvelle table de membre entre dans
  l'export et la suppression. Un test compare la liste des tables du schéma à
  celle de l'export et de la suppression.
- **Jamais** de phrase de récupération, de clé privée ni de mot de passe
  d'exchange : le test existant est étendu à tout nouveau formulaire.
- **Contenu** : le validateur et les tests de contenu passent pour chaque
  article et chaque leçon.
- **Sauvegardes** : une restauration testée au moins une fois par trimestre.

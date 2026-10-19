# Bitcoin : origines et fonctionnement

*Fiche de révision · Sensitor Academy · Monnaie et Bitcoin, parcours 2, « Bitcoin en profondeur »*

## Le problème et la réponse

- **Double dépense** : une monnaie numérique doit empêcher de dépenser deux fois la même unité.
- Solution habituelle : un **tiers de confiance** tient le registre.
- Bitcoin : un **registre public**, ordonné par une **preuve de travail**, la **chaîne la plus travaillée** fait foi.

## Les dates

| Date | Événement |
|---|---|
| 1983 · 1991 · 1997 · 1998 · 2005 | Chaum, Haber et Stornetta, Back (Hashcash), Dai (b-money), Szabo (bit gold) |
| 31 octobre 2008 | publication du livre blanc |
| 3 janvier 2009 | bloc de genèse, titre du *Times* du jour |
| 12 janvier 2009 | bloc 170 : 10 BTC envoyés à Hal Finney |
| 22 mai 2010 | deux pizzas payées 10 000 BTC |

## Les transactions

- **Clé privée** → clé publique → adresse ; jamais l'inverse. La **signature** prouve la détention de la clé.
- Une transaction dépense des **sorties entières** et crée de nouvelles sorties, dont la **monnaie rendue**.
- **Frais** = entrées − sorties = taille (vB) × prix (sat/vB). 1 BTC = 100 000 000 satoshis.
- La **phrase de récupération** ne se communique jamais. Sensitor ne la demandera jamais.

## Le registre

- **SHA-256** : même donnée, même empreinte ; le moindre changement change tout ; pas de retour en arrière.
- Chaque bloc contient l'**empreinte du précédent** : modifier le passé rompt la chaîne.
- **Preuve de travail** : trouver un nonce demande des essais en masse, vérifier en demande un.
- **Difficulté** : ajustée tous les 2 016 blocs, × 14 jours ÷ durée réelle, limitée à un facteur 4.
- Une part **s** de la puissance trouve en moyenne un bloc toutes les 10 ÷ s minutes.

## La sécurité

| Confirmations | Attaquant à 10 % | Attaquant à 30 % |
|---|---|---|
| 1 | 20,5 % | 62,8 % |
| 5 | 0,091 % | 17,7 % |
| 6 | 0,024 % | 13,2 % |

Sous 0,1 % : 5 confirmations face à 10 %, 24 face à 30 %. Un attaquant majoritaire peut annuler ses propres paiements, pas dépenser ceux des autres ni créer des bitcoins hors des règles.

## L'émission

| Halving | Bloc | Date | Récompense |
|---|---|---|---|
| départ | 0 | 3 janvier 2009 | 50 BTC |
| 1 · 2 · 3 · 4 | 210 000 · 420 000 · 630 000 · 840 000 | 2012 · 2016 · 2020 · avril 2024 | 25 · 12,5 · 6,25 · 3,125 BTC |
| 5 | 1 050 000 | vers avril 2028, estimation | 1,5625 BTC |

Total : **20 999 999,9769 BTC**. 95,7 % émis au 17 octobre 2026. Dernière fraction vers 2140. Émission actuelle : 450 BTC par jour, 0,82 % de l'offre par an.

## Ce qui reste débattu

- Bitcoin comme réserve de valeur.
- Le coût environnemental de la preuve de travail.
- La sécurité quand la récompense aura presque disparu.

---

*Document pédagogique. Ne constitue pas un conseil en investissement.*

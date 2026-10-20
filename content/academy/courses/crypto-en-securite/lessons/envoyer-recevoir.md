+++
id = "envoyer-recevoir"
title = "Envoyer et recevoir sans erreur"
summary = "Une transaction confirmée ne s'annule pas. Le bon réseau, la bonne adresse, une transaction d'essai, et ce que coûte un envoi sur Ethereum : la procédure qui évite les pertes irréversibles."
duration_minutes = 14
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Appliquer une procédure d'envoi qui vérifie réseau, adresse et montant.",
  "Reconnaître l'empoisonnement d'adresse.",
  "Calculer le coût d'une transaction sur Ethereum à partir du gaz et de son prix.",
]
quiz = "check-envoyer-recevoir"
resources = ["fiche-crypto-securite"]
sources = [
  "Buterin, V., Conner, E., Dudley, R., Slipper, M., Norden, I. et Bakhta, A. (2019). EIP-1559 : Fee market change for ETH 1.0 chain, en vigueur depuis le 5 août 2021.",
  "Wood, G. Ethereum: A Secure Decentralised Generalised Transaction Ledger (« Yellow Paper ») : 21 000 unités de gaz pour un transfert simple.",
  "Autorité des marchés financiers, mises en garde sur les escroqueries aux cryptoactifs.",
]
+++

## Une transaction ne s'annule pas

Sur un registre public, aucune banque ne peut annuler un virement envoyé par erreur. Une fois confirmée, la transaction est définitive. Les erreurs les plus coûteuses ne sont pas des piratages, mais des envois au mauvais endroit.

::: callout method "La procédure d'envoi"
1. **Le réseau** : vérifier que le réseau choisi à l'envoi est celui qu'accepte le destinataire. Une même adresse peut exister sur plusieurs réseaux ; un actif envoyé sur un réseau que la plateforme ne surveille pas peut être perdu.
2. **L'adresse** : la copier depuis la source, jamais de mémoire ni depuis l'historique, puis comparer plusieurs caractères au début, **au milieu** et à la fin.
3. **Une transaction d'essai** : pour un montant important, envoyer d'abord une petite somme et vérifier qu'elle arrive.
4. **Le montant et les frais** : relire avant de signer ; sur un portefeuille froid, lire l'adresse sur l'écran de l'appareil.
:::

::: callout warning "L'empoisonnement d'adresse"
Un fraudeur envoie un montant nul ou minuscule depuis une adresse qui ressemble à celle d'un de vos contacts : mêmes premiers et derniers caractères. Elle apparaît dans votre historique. Si vous la copiez de là pour votre prochain envoi, les fonds partent au fraudeur. D'où la règle : copier depuis la source, et vérifier aussi le milieu de l'adresse.
:::

## Ce que coûte un envoi sur Ethereum

Sur Ethereum, une transaction consomme du **gaz**, une mesure du travail de calcul : 21 000 unités pour un simple transfert d'ether, davantage pour un jeton ou un contrat. Le prix du gaz s'exprime en **gwei**, un milliardième d'ether, et varie avec la demande.

::: formula
\text{Frais} = \text{gaz consommé} \times \text{prix du gaz}
:::

::: chart frais-gaz
Le coût d'un transfert selon le prix du gaz, ether à 3 000 dollars : 1,26 dollar à 20 gwei pour de l'ether, 3,90 dollars pour un jeton. Hypothèses de la leçon.
:::

## À vous

::: exercise frais-ethereum
:::

::: callout note "Recevoir"
Pour recevoir, on communique une adresse et le réseau. Une adresse ne donne accès à rien : elle peut être partagée sans risque. Ce qui ne se partage jamais, ce sont les clés et la phrase de récupération.
:::

::: callout mistake "Erreur fréquente"
Choisir le réseau « le moins cher » proposé par la plateforme d'envoi sans vérifier que la plateforme de destination le prend en charge. L'économie de quelques centimes peut coûter le montant entier.
:::

::: callout recap
- Une transaction confirmée est définitive : réseau, adresse et montant se vérifient avant.
- Copier l'adresse depuis la source, vérifier début, milieu et fin ; une transaction d'essai pour les montants importants.
- Frais sur Ethereum = gaz × prix du gaz ; 21 000 unités pour un transfert simple.
:::

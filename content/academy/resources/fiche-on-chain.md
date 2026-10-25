# Lire les métriques on-chain de Bitcoin

*Fiche de révision · Sensitor Academy · Crypto, parcours 2, « Altcoins et analyse crypto »*

## Trois familles

| Famille | Exemples |
|---|---|
| Mesurée | transactions, taille, poids, frais, émission |
| Estimée | puissance de calcul, part des pools |
| Dépendante du prix | prix réalisé, MVRV, NUPL, SOPR |

Méthode du cours : un bloc par jour depuis le 9 janvier 2009 (6 474 blocs), moyennes mensuelles.

## Les formules

- **Transactions par jour** ≈ transactions par bloc × blocs par jour.
- **Remplissage** = poids du bloc ÷ 4 000 000.
- **Frais d'un bloc** = coinbase − récompense du protocole.
- **Part des frais** = frais ÷ coinbase.
- **Revenu par EH/s et par jour** = revenu quotidien des mineurs ÷ puissance du réseau.
- **Coefficient de Nakamoto** = nombre de pools pour dépasser 50 % des blocs.
- **Prix réalisé** = Σ unités × prix au dernier mouvement ÷ offre ; **MVRV** = prix ÷ prix réalisé ; **NUPL** = 1 − prix réalisé ÷ prix.

## Les repères (septembre 2026)

- Environ 688 000 transactions par jour ; remplissage de 99,9 %.
- Frais de 0,018 BTC par bloc, 0,6 % du revenu des mineurs.
- Environ 0,50 BTC par EH/s et par jour.
- 3 pools pour dépasser la moitié des blocs en 2026.

## Les dates

- **24 août 2017** : SegWit, la limite devient un poids de 4 millions d'unités.
- **14 novembre 2021** : Taproot.
- **Janvier 2023** : les inscriptions.
- **20 avril 2024**, bloc 840 000 : halving et lancement de Runes, 37,63 BTC de frais dans un seul bloc.

---

*Document pédagogique. Ne constitue pas un conseil en investissement. Aucune métrique n'est un signal infaillible.*

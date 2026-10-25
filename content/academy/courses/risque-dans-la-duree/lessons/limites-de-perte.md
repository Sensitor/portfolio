+++
id = "limites-de-perte"
title = "Limites journalières et règles de prop firm"
summary = "Des limites de perte écrites à l'avance, pour soi ou imposées par une prop firm : comment elles se calculent, combien de pertes elles autorisent, et pourquoi doubler le risque pour se refaire les rapproche."
duration_minutes = 17
access = "member"
status = "published"
version = 1
objectives = [
  "Calculer une limite de perte journalière et une perte maximale.",
  "Traduire une limite en nombre de pertes consécutives.",
  "Lire les règles d'un challenge sans se tromper de référence.",
]
quiz = "check-limites"
resources = ["fiche-risque-duree", "checklist-avant-trade"]
+++

## Pourquoi une limite journalière

Les pires journées ne sont pas toujours dues au marché. Après deux ou trois pertes, la tentation de « se refaire » pousse à prendre des trades moins préparés, plus gros, plus tôt. Une **limite de perte journalière** décidée à froid arrête la séance avant que la décision ne se dégrade.

::: callout definition "Deux limites"
- **Limite journalière** : perte maximale autorisée sur une journée, souvent mesurée depuis le solde de début de journée.
- **Perte maximale** : perte totale au-delà de laquelle on cesse de trader le compte, mesurée depuis le solde initial ou, selon les règles, depuis le plus haut atteint.
:::

## Traduire une limite en nombre de pertes

Avec un risque fixe par trade, une limite se traduit directement en nombre de pertes consécutives :

::: formula
\text{Pertes avant la limite} = \left\lceil \frac{\text{Limite (\%)}}{\text{Risque par trade (\%)}} \right\rceil
:::

Avec une limite de 5 % et 1 % par trade, la limite est atteinte au bout de cinq pertes ; avec 0,5 %, au bout de dix. Avec 2 %, trois pertes suffisent à la dépasser.

## Les règles de prop firm

Les prop firms proposent des comptes financés après un « challenge » qui impose ce type de limites. Les chiffres et les définitions varient d'une société à l'autre ; avant de trader, il faut vérifier par écrit :

- la référence de la limite journalière : solde de début de journée, ou équité, positions ouvertes comprises ;
- la référence de la perte maximale : fixe depuis le solde initial, ou **suiveuse** (*trailing*), qui remonte avec les plus hauts ;
- ce qui compte comme perte : commissions et swaps inclus ou non ;
- les règles annexes : objectifs de gain, nombre minimal de jours, interdictions d'annonces ou de positions le week-end.

::: callout warning "La perte maximale suiveuse"
Avec une perte maximale suiveuse, chaque nouveau plus haut relève le seuil. Compte de 100 000 $, perte maximale suiveuse de 6 000 $ : si le compte monte à 104 000 $, le seuil remonte à 98 000 $. Une baisse jusqu'à 98 000 $ élimine le compte, alors qu'il n'est qu'à 2 % sous son solde initial.
:::

## À vous

::: exercise limites-prop
:::

::: callout mistake "Erreur fréquente"
Doubler le risque après une perte pour revenir à zéro plus vite. La limite journalière se rapproche deux fois plus vite, et la décision est prise au pire moment.
:::

::: callout recap
- Une limite journalière et une perte maximale s'écrivent avant de trader, pas pendant.
- Avec un risque fixe, une limite se traduit en nombre de pertes consécutives : arrondir vers le haut.
- Les règles de prop firm se lisent mot à mot : référence, limite suiveuse, coûts inclus.
- Augmenter le risque pour se refaire rapproche la limite.
:::

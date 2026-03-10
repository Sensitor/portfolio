import model.Personnage;
import model.Race;
import model.Profil;

/**
 * Classe principale de test.
 * Crée plusieurs personnages de différentes races et profils
 * pour démontrer le fonctionnement du système.
 */
public class Main {

    public static void main(String[] args) {
        System.out.println("╔══════════════════════════════════════════╗");
        System.out.println("║   CREATEUR DE PERSONNAGES - RPG JAVA    ║");
        System.out.println("╚══════════════════════════════════════════╝\n");

        // --- Création de personnages variés ---

        // 1. Guerrier Humain
        System.out.println(">> Création d'un Guerrier Humain...\n");
        Personnage guerrier = new Personnage("Aldric", Race.HUMAIN, Profil.GUERRIER);
        guerrier.afficherFiche();

        // 2. Magicien Elfe
        System.out.println(">> Création d'un Magicien Elfe...\n");
        Personnage magicien = new Personnage("Elyndra", Race.ELFE, Profil.MAGICIEN);
        magicien.afficherFiche();

        // 3. Prêtre Nain
        System.out.println(">> Création d'un Prêtre Nain...\n");
        Personnage pretre = new Personnage("Thorin", Race.NAIN, Profil.PRETRE);
        pretre.afficherFiche();

        // 4. Rôdeur Demi-Elfe
        System.out.println(">> Création d'un Rôdeur Demi-Elfe...\n");
        Personnage rodeur = new Personnage("Arannis", Race.DEMI_ELFE, Profil.RODEUR);
        rodeur.afficherFiche();

        // 5. Voleur Demi-Orque
        System.out.println(">> Création d'un Voleur Demi-Orque...\n");
        Personnage voleur = new Personnage("Grokk", Race.DEMI_ORQUE, Profil.VOLEUR);
        voleur.afficherFiche();

        // --- Démonstration du calcul de modificateur ---
        System.out.println("========================================");
        System.out.println("  DEMO : Calcul des modificateurs");
        System.out.println("========================================");
        int[] exemples = {3, 6, 8, 10, 12, 14, 18};
        for (int val : exemples) {
            int mod = Personnage.getModificateur(val);
            String signe = mod >= 0 ? "+" : "";
            System.out.printf("  Caractéristique %2d -> Modificateur %s%d%n", val, signe, mod);
        }
        System.out.println();

        // --- Comparaison de deux personnages ---
        System.out.println("========================================");
        System.out.println("  COMPARAISON : " + guerrier.getNom() + " vs " + magicien.getNom());
        System.out.println("========================================");
        System.out.printf("  %-15s : PV=%d, Def=%d, Mêlée=%d%n",
                guerrier.getNom(), guerrier.getPointsDeVie(),
                guerrier.getDefense(), guerrier.getAttaqueMelee());
        System.out.printf("  %-15s : PV=%d, Def=%d, Magie=%d%n",
                magicien.getNom(), magicien.getPointsDeVie(),
                magicien.getDefense(), magicien.getAttaqueMagique());
        System.out.println("========================================\n");

        System.out.println("Tous les personnages ont été créés avec succès !");
    }
}
